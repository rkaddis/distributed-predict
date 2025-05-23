import threading
import time
from base64 import b64encode

from paho.mqtt import client as MQTT
from utils.common.Messages import Heartbeat, VideoRequest, heartbeat_decode
from utils.common.Topics import HEARTBEAT_TOPIC, REQUEST_INBOX

# MQTT network info. Broker always takes 192.168.0.2
MQTT_HOST = "192.168.1.130"  # broker ip
MQTT_PORT = 1883  # broker port

# mqtt name of this client, random base64 string
client_name = "tester"

# mqtt client
client = MQTT.Client(MQTT.CallbackAPIVersion.VERSION2, client_id=client_name)

nodes: list[str] = []
node_ping: list[str] = []


def heartbeat_timeout_loop():
    global nodes, node_ping
    while True:
        nodes = node_ping
        node_ping = []
        time.sleep(1)


def heartbeat_cb(message: Heartbeat):
    node = message.node
    if node not in node_ping:
        node_ping.append(node)


def on_connect(client: MQTT.Client, userdata, flags, reason_code, properties):
    client.subscribe(f"{HEARTBEAT_TOPIC}")


def on_message(client: MQTT.Client, userdata, message: MQTT.MQTTMessage):
    if message.topic.endswith(HEARTBEAT_TOPIC):
        hb = heartbeat_decode(message.payload.decode())
        heartbeat_cb(hb)


client.on_connect = on_connect
client.on_message = on_message


client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_HOST, MQTT_PORT)
client.loop_start()
threading.Thread(target=heartbeat_timeout_loop, daemon=True).start()
time.sleep(2)
video = ""
with open("test_video.mp4", "rb") as f:
    video = f.read()
vr = VideoRequest(b64encode(video).decode(), 76)
print(f"Sending message to {nodes[0]}")
client.publish(f"/{nodes[0]}/{REQUEST_INBOX}", vr.encode_message())
time.sleep(1)
