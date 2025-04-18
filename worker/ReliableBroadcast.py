from munch import Munch
from paho.mqtt import client as MQTTClient
from munch import munchify
import json

from ..common.Message import Message
from ..common.Topics import *


class RBMessage(Message):

    state : str = None
    subject : str = None
    data : str = None

    def __init__(self, state : str, subject : str, data : str):
        super().__init__()
        self.state = state
        self.subject = subject
        self.data = data

        self.content.state = state
        self.content.subject = subject
        self.content.data = data

    def __eq__(self, other):
        return self.state == other.state and self.subject == other.subject and self.data == other.data
    
def rbmessage_decode(content : str) -> RBMessage:
    m = munchify(json.loads(content))
    return RBMessage(m.state, m.subject, m.data)

class RBInstance:

    client : MQTTClient.Client
    nodes : list[str]
    subject : str
    initial_message = RBMessage
    echo_messages : list[RBMessage] = []
    ready_messages : list[RBMessage] = []

    def __init__(self, client : MQTTClient.Client, nodes : list[str], initial_message: RBMessage):
        self.client = client # mqtt client
        self.nodes = nodes # list of nodes in network
        self.initial_message = initial_message # the initial message/state of the RB protocol
        self.subject = initial_message.subject # the subject of the message

        # send out your initial contents as an echo
        echo_message = RBMessage("echo", self.subject, initial_message.data)
        print(echo_message.state)
        self.send_all(echo_message)


    def send_all(self, message : RBMessage):
        """
        Sends a RBMessage to all nodes.
        """
        self.client.publish(f"{BROADCAST_TOPIC}", message.encode_message())

    def count_alike_messages(self, messages : list[RBMessage]) -> tuple[int, RBMessage]:
        """
        Tallies up a list of RBMessages and returns the most common value, and its count.
        """
        contents : dict = {}

        for message in messages:
            if message.data not in contents:
                contents[message.data] = 0
            contents[message.data] += 1

        max_data = None
        max_count = 0
        for key in contents:
            if(contents[key] > max_count):
                max_data = key
                max_count = contents[key]

        return max_count, max_data


    def handle_message(self, message : RBMessage) -> RBMessage | None:
        n = len(self.nodes)
        f = (n+1) // 3
        if message.state == "echo":
            self.echo_messages.append(message)
            max_count, max_data = self.count_alike_messages(self.echo_messages)
            
            if max_count >= (n+f) // 2:
                ready_message = RBMessage("ready", self.initial_message.subject, max_data)
                self.send_all(ready_message)
            
        elif message.state == "ready":
            self.ready_messages.append(message)
            max_count, max_data = self.count_alike_messages(self.ready_messages)

            if max_count >= (2*f+1):
                accept_message = RBMessage("accepted", self.initial_message.subject, max_data)
                return accept_message
            
    def __eq__(self, other):
        return self.subject == other.subject
            


    