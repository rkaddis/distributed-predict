import json  # noqa

from munch import Munch, munchify  # noqa
from paho.mqtt import client as MQTTClient
from hashlib import sha256

from ..common.Messages import RBMessage, rbmessage_decode  # noqa
from ..common.Topics import BROADCAST_TOPIC


class RBInstance:
    def __init__(self, client: MQTTClient.Client, nodes: list[str], initial_message: RBMessage, use_hash : bool = False):
        self.client = client  # mqtt client
        self.nodes = nodes  # list of nodes in network
        self.initial_message = initial_message  # the initial message/state of the RB protocol
        self.subject = initial_message.subject  # the subject of the message
        self.echo_messages: list[RBMessage] = []
        self.ready_messages: list[RBMessage] = []
        self.use_hash = use_hash
        self.hash_value = None
        
        if self.use_hash:
            self.hash_value = sha256(initial_message.data.encode())

        # send out your initial contents as an echo
        if self.use_hash:
            echo_message = RBMessage("echo", self.subject, str(self.hash_value))
        else:
            echo_message = RBMessage("echo", self.subject, initial_message.data)
        self.send_all(echo_message)

    def send_all(self, message: RBMessage):
        """
        Sends a RBMessage to all nodes.
        """
        self.client.publish(f"{BROADCAST_TOPIC}", message.encode_message())

    def count_alike_messages(self, messages: list[RBMessage]) -> tuple[int, RBMessage]:
        """
        Tallies up a list of RBMessages and returns the most common value, and its count.
        """
        contents: dict = {}

        for message in messages:
            if message.data not in contents:
                contents[message.data] = 0
            contents[message.data] += 1

        max_data = None
        max_count = 0
        for key in contents:
            if contents[key] > max_count:
                max_data = key
                max_count = contents[key]

        return max_count, max_data

    def handle_message(self, message: RBMessage) -> RBMessage | None:
        n = len(self.nodes)
        f = (n - 1) // 3
        if message.state == "echo":
            self.echo_messages.append(message)
            max_count, max_data = self.count_alike_messages(self.echo_messages)

            if max_count >= (n + f) // 2:
                if self.use_hash:
                    ready_message = RBMessage("ready", self.initial_message.subject, sha256(max_data.data.encode()))
                else:
                    ready_message = RBMessage("ready", self.initial_message.subject, max_data)
                self.send_all(ready_message)

        elif message.state == "ready":
            self.ready_messages.append(message)
            max_count, max_data = self.count_alike_messages(self.ready_messages)

            if max_count >= (2 * f + 1):
                if self.use_hash:
                    if sha256(max_data.data.encode()) == self.hash_value:
                        accept_message = RBMessage("accepted", self.initial_message.subject, self.initial_message.data)
                        return accept_message
                    else:
                        raise Exception("Hash was bad!")
                else:
                    accept_message = RBMessage("accepted", self.initial_message.subject, max_data.data)
                    return accept_message

    def __eq__(self, other):
        return self.subject == other.subject
