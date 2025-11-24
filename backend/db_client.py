import os
import uuid
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Key

# -----------------------------
# Configuration
# -----------------------------

# AWS region (same as your DynamoDB tables, e.g., us-east-1)
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Table names (default to your Rakan_* tables, but allow env override)
DEVICE_STATE_TABLE = os.getenv("DEVICE_TABLE", "Rakan_DeviceState")
EVENT_LOGS_TABLE = os.getenv("LOG_TABLE", "Rakan_EventLogs")

# Index name for querying logs by deviceId
EVENT_LOGS_DEVICE_INDEX = os.getenv("EVENT_LOGS_DEVICE_INDEX", "DeviceIdIndex")

# DynamoDB resource + table objects
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
device_state_table = dynamodb.Table(DEVICE_STATE_TABLE)
event_logs_table = dynamodb.Table(EVENT_LOGS_TABLE)


# -----------------------------
# Helper Functions
# -----------------------------

def _now_iso() -> str:
    """Return current UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


# -----------------------------
# Device State Functions
# -----------------------------

def save_device_state(device_id: str, device_type: str, state: dict, extra: dict | None = None) -> None:
    """
    Create or update the current state of a device in Rakan_DeviceState.

    Args:
        device_id: str - unique device ID
        device_type: str - e.g., "smart_switch", "motion_sensor"
        state: dict - e.g., {"value": True}
        extra: dict - additional fields, ex: {"location": "Bedroom"}
    """
    item: dict = {
        "deviceId": device_id,
        "type": device_type,
        "state": state,
        "lastSeenAt": _now_iso(),
    }

    if extra:
        item.update(extra)

    device_state_table.put_item(Item=item)


def get_device_state(device_id: str) -> dict | None:
    """
    Get the current state of a device from Rakan_DeviceState.
    Returns a dict or None if not found.
    """
    resp = device_state_table.get_item(Key={"deviceId": device_id})
    return resp.get("Item")


# -----------------------------
# Event Log Functions
# -----------------------------

def log_event(
    device_id: str,
    event_type: str,
    value,
    source: str = "device",
    details: dict | None = None,
    created_at: str | None = None,
) -> str:
    """
    Insert a log entry into Rakan_EventLogs and return the logId.

    Args:
        device_id (str): device that produced the event
        event_type (str): ex. "motion", "switch", "temperature"
        value: event value (bool, number, string, etc.)
        source (str): "device", "user", "AI", "system"
        details (dict): optional metadata
        created_at (str): ISO string timestamp (optional)
    """
    if created_at is None:
        created_at = _now_iso()

    log_id = str(uuid.uuid4())

    item: dict = {
        "logId": log_id,
        "deviceId": device_id,
        "eventType": event_type,
        "value": value,
        "source": source,
        "createdAt": created_at,
    }

    if details:
        item["details"] = details

    event_logs_table.put_item(Item=item)
    return log_id


def get_recent_events_for_device(device_id: str, limit: int = 20) -> list[dict]:
    """
    Query Rakan_EventLogs using DeviceIdIndex to fetch the most recent events
    for a single device.
    """
    resp = event_logs_table.query(
        IndexName=EVENT_LOGS_DEVICE_INDEX,
        KeyConditionExpression=Key("deviceId").eq(device_id),
        ScanIndexForward=False,  # Newest events first
        Limit=limit,
    )
    return resp.get("Items", [])


def get_recent_events_global(limit: int = 50) -> list[dict]:
    """
    Scan Rakan_EventLogs for recent events across all devices.
    (Used for frontend dashboard.)
    """
    resp = event_logs_table.scan(Limit=limit)
    return resp.get("Items", [])
