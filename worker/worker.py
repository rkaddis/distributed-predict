from paho.mqtt import client as MQTT
import base64
import secrets
import time

# MQTT network info. Broker always takes 192.168.0.2
MQTT_HOST = "192.168.0.2" # broker ip
MQTT_PORT = 1883 # broker port

# MQTT topic info
DATA_IN_TOPIC = "inbox"
DATA_OUT_TOPIC = "outbox"
HEARTBEAT_TOPIC = "heartbeat"

# mqtt name of this client, random base64 string
client_name = secrets.token_urlsafe(8)

# mqtt client
client = MQTT.Client(MQTT.CallbackAPIVersion.VERSION2, client_id=client_name)

def on_connect(client : MQTT.Client, userdata, flags, reason_code, properties):
    client.subscribe(f"/{client_name}/{DATA_IN_TOPIC}")
    
def on_message(client : MQTT.Client, userdata, message : MQTT.MQTTMessage):
    if(message.topic.endswith(DATA_IN_TOPIC)):
        data_in_cb(message.payload)
        
        
# MQTT message callbacks       
def data_in_cb(data : bytes):
    client.publish(f"/{client_name}/{DATA_OUT_TOPIC}", data)
    
    
    
    
    
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
        client.publish(f"/{HEARTBEAT_TOPIC}", client_name)
        time.sleep(0.2)
                
        