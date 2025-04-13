from munch import Munch, munchify, unmunchify
import json


def encode_message(content : Munch) -> str:
    return json.dumps(unmunchify(content))
    
def decode_message(content : str) -> Munch:
    return munchify(json.loads(content))