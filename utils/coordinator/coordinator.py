from paho.mqtt import client as MQTT
import threading
import time

# MQTT network info. Broker always takes 192.168.0.2
MQTT_HOST = "127.0.0.1" # broker ip
MQTT_PORT = 1883 # broker port

HEARTBEAT_TOPIC = "heartbeat"

client_name = "coordinator" # mqtt client name
worker_nodes = [] # names of worker nodes on the network
worker_queue = []

# mqtt client
client = MQTT.Client(MQTT.CallbackAPIVersion.VERSION2, client_id=client_name)

def get_input_split():
    while True:
        if(not client.is_connected()):
            print("Awaiting MQTT connection...")
            time.sleep(5)
            continue
        
        input_string = input("Enter data: ")
        
        while len(worker_nodes) == 0:
            print("Awaiting a worker connection...")
            time.sleep(5)
        
        split_len = max(len(input_string) // len(worker_nodes), 1)
        for worker in worker_nodes:
            client.publish(f"/{worker}/inbox", input_string[0:split_len])
            input_string = input_string[split_len:]
            
def heartbeat_timeout_loop():
    global worker_nodes, worker_queue
    while True:
        worker_nodes = worker_queue
        worker_queue = []
        time.sleep(1)
        

def heartbeat_cb(message : bytes):
    worker = message.decode()
    if worker not in worker_queue:
        worker_queue.append(worker)
        
        
def on_connect(client : MQTT.Client, userdata, flags, reason_code, properties):
    client.subscribe("/heartbeat")
    
def on_message(client : MQTT.Client, userdata, message : MQTT.MQTTMessage):
    if(message.topic.endswith(HEARTBEAT_TOPIC)):
        heartbeat_cb(message.payload)
        
if __name__ == '__main__':
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT)
    client.loop_start()
    threading.Thread(target=heartbeat_timeout_loop, daemon=True).start()
    get_input_split()