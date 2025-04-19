from munch import Munch, munchify, unmunchify
import json

class Message:

    content : Munch = None

    def __init__(self, content : Munch = Munch()):
        self.content = content


    def encode_message(self) -> str:
        """
        Encodes a Munch object into a JSON string.
        """
        return json.dumps(unmunchify(self.content))
        
    def decode_message(self, content : str):
        """
        Decodes a JSON string into a Munch.
        """
        self.content = munchify(json.loads(content))

def message_decode(content : str) -> Message:
    return Message(munchify(json.loads(content)))

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

