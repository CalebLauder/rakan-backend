# simulator/shared/utils.py
import json, time
def ensure_timestamp(payload):
    if "timestamp" not in payload:
        payload["timestamp"] = int(time.time())
    return payload

def safe_dumps(payload):
    return json.dumps(payload, default=str)
