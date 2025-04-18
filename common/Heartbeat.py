from .Message import Message
from munch import munchify
import json

class Heartbeat(Message):

    node : str
    status : str

    def __init__(self, node = "", status = ""):
        super().__init__()
        self.node = node
        self.status = status

        self.content.node = node
        self.content.status = status

def heartbeat_decode(content : str) -> Heartbeat:
    data = munchify(json.loads(content))
    return Heartbeat(data.node, data.status)