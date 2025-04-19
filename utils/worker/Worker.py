from paho.mqtt import client as MQTT
import secrets
import time
import threading
from copy import deepcopy
from base64 import b64decode

from ..common.Topics import *
from .ReliableBroadcast import RBInstance, RBMessage, rbmessage_decode
from ..common.Heartbeat import Heartbeat, heartbeat_decode

# MQTT network info.
MQTT_HOST = "192.168.1.130" # broker ip
MQTT_PORT = 1883 # broker port

class Worker:

    client : MQTT.Client # mqtt client
    client_name : str # client's unique name
    leader = False # whether this node is the leader
    busy = False # whether this node is processing a task

    nodes : dict = {} # nodes and their statuses
    node_ping : dict = {} # intermediate dict before the main one
    broadcast_queue : list[RBInstance] = [] # queue of pending reliable broadcasts

    def __init__(self):
        self.client_name = secrets.token_urlsafe(8) # set client name as random string
        self.client = MQTT.Client(MQTT.CallbackAPIVersion.VERSION2, client_id=self.client_name)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

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
         
        threading.Thread(target=self.heartbeat_timeout_loop, daemon=True).start() # start heartbeat

        while self.client.is_connected():
            hb_message = Heartbeat(node=self.client_name, status="free" if not self.busy else "busy")
            self.client.publish(f"{HEARTBEAT_TOPIC}", hb_message.encode_message())
            time.sleep(0.1)


    # tracks nodes' heartbeats.
    def heartbeat_timeout_loop(self):
        while True:
            self.nodes = deepcopy(self.node_ping)
            self.node_ping = {}
            time.sleep(0.5)

    # adds a node to the list of known nodes.        
    def heartbeat_cb(self, message : Heartbeat):
        node = message.node
        if node not in self.node_ping:
            self.node_ping[node] = message.status

    # gets the request from the user and broadcasts it.
    def request_cb(self, data : str):
        video = b64decode(data)
        with open("test123.mp4", "wb") as f:
            f.write(video)
        self.leader = True
        initial_message = RBMessage("initial", "client", data)
        self.client.publish(f"{BROADCAST_TOPIC}", initial_message.encode_message())

    # follows the reliable broadcast protocol.
    def broadcast_cb(self, rb_message : RBMessage):
        if rb_message.state == 'initial':
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
                print(out.encode_message())
                self.broadcast_queue.pop(index)

    # subscribe to topics
    def on_connect(self, client : MQTT.Client, userdata, flags, reason_code, properties):
        client.subscribe(f"{HEARTBEAT_TOPIC}")
        client.subscribe(f"/{self.client_name}/{REQUEST_INBOX}")
        client.subscribe(f"{BROADCAST_TOPIC}")
    
    # specify callbacks
    def on_message(self, client : MQTT.Client, userdata, message : MQTT.MQTTMessage):
        if(message.topic.endswith(HEARTBEAT_TOPIC)):
            hb = heartbeat_decode(message.payload.decode())
            self.heartbeat_cb(hb)
        elif(message.topic.endswith(REQUEST_INBOX)):
            self.request_cb(message.payload.decode())
        elif(message.topic.endswith(BROADCAST_TOPIC)):
            rb_message = rbmessage_decode(message.payload.decode())
            self.broadcast_cb(rb_message)
            

    
