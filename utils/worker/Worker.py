import secrets
import tempfile
import threading
import time
from base64 import b64decode, b64encode
from copy import deepcopy

import cv2 as cv
import numpy as np  # noqa
from paho.mqtt import client as MQTT

from ..common.Messages import (
    Heartbeat,
    RBMessage,
    VideoRequest,
    heartbeat_decode,
    rbmessage_decode,
    videorequest_decode,
)
from ..common.MQTT_Broker import MQTT_HOST, MQTT_PORT
from ..common.Topics import HEARTBEAT_TOPIC, BROADCAST_TOPIC, CMD_INBOX, REQUEST_INBOX, CLIENT_TOPIC
from .ImagePredict import ImagePredictor
from .MaxSubarray import max_subarray
from .ReliableBroadcast import RBInstance


class Worker:
    client: MQTT.Client  # mqtt client
    client_name: str  # client's unique name
    leader = False  # whether this node is the leader
    busy = False  # whether this node is processing a task

    nodes: dict = {}  # nodes and their statuses
    node_ping: dict = {}  # intermediate dict before the main one
    broadcast_queue: list[RBInstance] = []  # queue of pending reliable broadcasts
    image_dict: dict = {} # dictionary of video frames
    results_dict: dict = {} # dictionary of frame results
    processing_queue: list[int] = [] # list of frames currently being processed
    predictor: ImagePredictor # the YOLO image processor
    free_nodes: list[str] = [] # list of nodes that are not busy
    target: int = 0 # the target object
    processing_time : float = 0 # total time spent processing frames

    def __init__(self):
        self.client_name = secrets.token_urlsafe(8)  # set client name as random string
        self.client = MQTT.Client(MQTT.CallbackAPIVersion.VERSION2, client_id=self.client_name)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.predictor = ImagePredictor(f"{__file__.replace('Worker.py', 'yolo12n.pt')}")

        # wait for MQTT connection
        while not self.client.is_connected():
            try:
                self.client.connect(MQTT_HOST, MQTT_PORT)
                self.client.loop_start()
                time.sleep(0.5)
            except OSError as e:
                print(e)
                time.sleep(5)
        print(f"Connected as {self.client_name}")

        threading.Thread(target=self.heartbeat_timeout_loop, daemon=True).start()  # start heartbeat

        while self.client.is_connected():
            hb_message = Heartbeat(node=self.client_name, status="free" if not self.busy else "busy")
            self.client.publish(f"{HEARTBEAT_TOPIC}", hb_message.encode_message())
            del hb_message
            time.sleep(0.1)

    # tracks nodes' heartbeats.
    def heartbeat_timeout_loop(self):
        while True:
            self.nodes = deepcopy(self.node_ping)
            self.node_ping = {}
            time.sleep(0.5)

    def leader_loop(self):
        # distribute tasks to open nodes
        while len(self.results_dict) != len(self.image_dict):
            for node in self.free_nodes:
                task_id = -1
                for i in self.image_dict:
                    if i not in self.processing_queue and i not in self.results_dict:
                        task_id = i
                        break

                if task_id != -1:
                    self.client.publish(f"/{node}/{CMD_INBOX}", task_id)
                    self.processing_queue.append(task_id)
                    print(f" {node} is processing frame {task_id}")
                    self.free_nodes.remove(node)
                else:
                    self.processing_queue = []

            time.sleep(0.01)

        # return the results to the client
        start_frame, end_frame = max_subarray(dict(sorted(self.results_dict.items())))
        fourcc = cv.VideoWriter_fourcc(*"mp4v")  # Be sure to use lower case
        tf = tempfile.NamedTemporaryFile(suffix=".mp4")
        rows, cols, _ = self.image_dict[0].shape
        out = cv.VideoWriter(tf.name, fourcc, 30.0, (cols, rows))
        for frame in range(start_frame, end_frame):
            out.write(self.image_dict[frame])
        out.release()

        clip = ""
        with open(tf.name, "rb") as f:
            clip = f.read()

        self.client.publish(CLIENT_TOPIC, b64encode(clip).decode())
        print("Sent results back to client.")
        print(f"Total time spent processing: {round(self.processing_time, 2)} seconds")

    # adds a node to the list of known nodes.
    def heartbeat_cb(self, message: Heartbeat):
        node = message.node
        if node not in self.node_ping:
            self.node_ping[node] = message.status
        if self.leader and message.status == "free" and node not in self.free_nodes:
            self.free_nodes.append(node)

    # gets the request from the user and broadcasts it.
    def request_cb(self, message: VideoRequest):
        self.leader = True
        initial_message = RBMessage("initial", "client", message.encode_message())
        self.client.publish(f"{BROADCAST_TOPIC}", initial_message.encode_message())

    # follows the reliable broadcast protocol.
    def broadcast_cb(self, rb_message: RBMessage):
        if rb_message.state == "initial":
            self.broadcast_queue.append(RBInstance(self.client, self.nodes, rb_message))
        else:
            index = -1
            for i in range(len(self.broadcast_queue)):
                if rb_message.subject == self.broadcast_queue[i].subject:
                    index = i
                    break
            if index == -1:
                return
            out = self.broadcast_queue[index].handle_message(rb_message)
            if out is not None:
                self.broadcast_queue.pop(index)

                if out.subject == "client":  # client's video request
                    vr = videorequest_decode(out.data)
                    video_bytes = b64decode(vr.video)
                    tf = tempfile.NamedTemporaryFile(suffix=".mp4")
                    tf.write(video_bytes)
                    cap = cv.VideoCapture(tf.name)

                    check, im = cap.read()
                    frame = 0
                    while check:
                        self.image_dict[frame] = im
                        check, im = cap.read()
                        frame += 1

                    self.target = vr.target
                    print(f"Got {len(self.image_dict.keys())} frames")
                    if self.leader:
                        threading.Thread(target=self.leader_loop, daemon=True).start()

                elif out.subject.isdigit():  # frame data
                    frame_id = int(out.subject)
                    self.results_dict[frame_id] = int(out.data) if int(out.data) > 0 else -1
                    try:
                        self.processing_queue.remove(frame_id)
                    except Exception:
                        pass

    # handle a command from the leader
    def command_cb(self, task_id: int):
        print(f"Processing task {task_id}")
        self.busy = True
        image = self.image_dict[task_id]
        # start_ts = time.time()
        hits = self.predictor.image_predict(image, target=self.target)
        # self.processing_time += time.time() - start_ts
        initial_message = RBMessage("initial", str(task_id), str(hits))
        self.client.publish(f"{BROADCAST_TOPIC}", initial_message.encode_message())
        self.busy = False
        print(f"Done with task {task_id}")

    # subscribe to topics
    def on_connect(self, client: MQTT.Client, userdata, flags, reason_code, properties):
        client.subscribe(f"{HEARTBEAT_TOPIC}")
        client.subscribe(f"/{self.client_name}/{REQUEST_INBOX}")
        client.subscribe(f"{BROADCAST_TOPIC}")
        client.subscribe(f"/{self.client_name}/{CMD_INBOX}")

    # specify callbacks
    def on_message(self, client: MQTT.Client, userdata, message: MQTT.MQTTMessage):
        if message.topic.endswith(HEARTBEAT_TOPIC):
            hb = heartbeat_decode(message.payload.decode())
            self.heartbeat_cb(hb)
            del hb
        elif message.topic.endswith(REQUEST_INBOX):
            vr = videorequest_decode(message.payload.decode())
            self.request_cb(vr)
        elif message.topic.endswith(BROADCAST_TOPIC):
            rb_message = rbmessage_decode(message.payload.decode())
            self.broadcast_cb(rb_message)
            del rb_message
        elif message.topic.endswith(CMD_INBOX):
            threading.Thread(target=self.command_cb, args=[int(message.payload.decode())], daemon=True).start()
