import json


class Message:
    """
    Base Message class, used for encoding/decoding over MQTT topics.
    """
    def __init__(self, content: dict = {}):
        self.content = content

    def encode_message(self) -> str:
        """
        Encodes a Munch object into a JSON string.
        """
        return json.dumps(self.content)

    def __del__(self):
        del self.content


def message_decode(content: str) -> Message:
    """Decodes an MQTT string into a Message."""
    return Message(json.loads(content))


class RBMessage(Message):
    """
    Message that contains fields relevant to Reliable Broadcast.
    """
    state: str = None
    subject: str = None
    data: str = None

    def __init__(self, state: str, subject: str, data: str):
        super().__init__({})
        self.state = state
        self.subject = subject
        self.data = data

        self.content["state"] = state
        self.content["subject"] = subject
        self.content["data"] = data

    def __eq__(self, other):
        return self.state == other.state and self.subject == other.subject and self.data == other.data

    def __del__(self):
        del self.content


def rbmessage_decode(content: str) -> RBMessage:
    """Decodes an MQTT string into an RBMessage."""
    d = json.loads(content)
    return RBMessage(d["state"], d["subject"], d["data"])


class Heartbeat(Message):
    """
    Message that contains fields for node heartbeats.
    """
    node: str
    status: str

    def __init__(self, node="", status=""):
        super().__init__({})
        self.node = node
        self.status = status

        self.content["node"] = node
        self.content["status"] = status

    def __del__(self):
        del self.content


def heartbeat_decode(content: str) -> Heartbeat:
    """Decodes an MQTT string into a Heartbeat."""
    data = json.loads(content)
    return Heartbeat(data["node"], data["status"])


class VideoRequest(Message):
    """
    Message that contains fields for client video requests.
    """
    video: str
    target: int

    def __init__(self, video="", target=0):
        super().__init__({})
        self.video = video
        self.target = target

        self.content["video"] = video
        self.content["target"] = target

    def __del__(self):
        del self.content


def videorequest_decode(content: str) -> VideoRequest:
    """Decodes an MQTT string into a VideoRequest."""
    data = json.loads(content)
    return VideoRequest(data["video"], data["target"])
