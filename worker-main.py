from paho.mqtt import client as MQTT
import secrets
import time

from common.Topics import *
from worker.ReliableBroadcast import RBInstance, RBMessage, rbmessage_decode
from common.Heartbeat import Heartbeat, heartbeat_decode

# MQTT network info. Broker always takes 192.168.0.2
MQTT_HOST = "192.168.1.130" # broker ip
MQTT_PORT = 1883 # broker port

# mqtt name of this client, random base64 string
client_name = secrets.token_urlsafe(8)

# mqtt client
client = MQTT.Client(MQTT.CallbackAPIVersion.VERSION2, client_id=client_name)

nodes : list[str] = []
node_ping : list[str] = []
broadcast_queue : list[RBInstance] = []

def heartbeat_timeout_loop():
    global nodes, node_ping
    while True:
        nodes = node_ping
        node_ping = []
        time.sleep(1)
        

def heartbeat_cb(message : bytes):
    node = message.decode()
    if node not in node_ping:
        node_ping.append(node)

def on_connect(client : MQTT.Client, userdata, flags, reason_code, properties):
    client.subscribe(f"{HEARTBEAT_TOPIC}")
    client.subscribe(f"/{client_name}/{REQUEST_INBOX}")
    client.subscribe(f"{BROADCAST_TOPIC}")
    
def on_message(client : MQTT.Client, userdata, message : MQTT.MQTTMessage):
    if(message.topic.endswith(REQUEST_INBOX)):
        # data = message_decode(message.payload)
        initial_message = RBMessage("initial", "client", message.payload.decode())
        client.publish(f"{BROADCAST_TOPIC}", initial_message.encode_message())
    if(message.topic.endswith(BROADCAST_TOPIC)):
        rb_message = rbmessage_decode(message.payload.decode())
        if rb_message.state == 'initial':
            broadcast_queue.append(RBInstance(client, nodes, rb_message))
        else:
            index = -1
            for i in range(len(broadcast_queue)):
                if rb_message.subject == broadcast_queue[i].subject:
                    index = i
                    break
            out = broadcast_queue[index].handle_message(rb_message)
            if out is not None:
                print(out.encode_message())
                broadcast_queue.pop(index)

        
    
    
    
    
    
client.on_connect = on_connect
client.on_message = on_message


if __name__ == "__main__":
    while not client.is_connected():
        try:
            client.connect(MQTT_HOST, MQTT_PORT)
        except OSError as e:
            print(e)
            time.sleep(5)

    client.loop_start()
    while client.is_connected():
        client.publish(f"{HEARTBEAT_TOPIC}", client_name)
        time.sleep(0.2)
                
        