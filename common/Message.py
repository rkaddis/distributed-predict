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


