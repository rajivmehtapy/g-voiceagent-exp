import jwt
import time
from datetime import datetime, timedelta

def generate_token(room_name="test-room", participant_name="user"):
    api_key = "API7Q6NLPMBAucwL"
    api_secret = "7CieAF7wshkHS0fsfGlQq6nnmrC1FtCN0mNboQfQWLXC"
    payload = {
        "iss": api_key,
        "exp": int((datetime.now() + timedelta(hours=1)).timestamp()),
        "nbf": int(datetime.now().timestamp()),
        "sub": participant_name,
        "name": participant_name,
        "room": room_name,
        "video": True,
        "audio": True,
        "canPublish": True,
        "canSubscribe": True,
    }
    
    token = jwt.encode(payload, api_secret, algorithm="HS256")
    return token

print(generate_token())