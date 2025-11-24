import boto3
import os
from datetime import datetime
import uuid

# Environment variables
DEVICE_TABLE = os.getenv("DEVICE_TABLE", "Rakan_DeviceState")
LOG_TABLE = os.getenv("LOG_TABLE", "Rakan_EventLogs")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)


def put_device_state(deviceId, state_dict):
    """Update or create the stored state for a device."""
    table = dynamodb.Table(DEVICE_TABLE)
    item = {
        "deviceId": deviceId,
        "lastSeen": datetime.utcnow().isoformat() + "Z",
        "state": state_dict,
    }
    table.put_item(Item=item)
    return item


def get_device_state(deviceId):
    """Return the saved state of a device."""
    table = dynamodb.Table(DEVICE_TABLE)
    resp = table.get_item(Key={"deviceId": deviceId})
    return resp.get("Item")


def log_event(event, lam_decision=None, command=None):
    """Insert an event into the logs table."""
    table = dynamodb.Table(LOG_TABLE)
    log_id = str(uuid.uuid4())

    item = {
        "logId": log_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event": event,
        "lamDecision": lam_decision or {},
        "commandSent": command or {},
    }

    table.put_item(Item=item)
    return item
