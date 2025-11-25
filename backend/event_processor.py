import json
import os
import uuid
from datetime import datetime

import boto3

# -----------------------------
# AWS CLIENTS & ENV VARS
# -----------------------------

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
EVENT_TABLE = os.getenv("EVENT_TABLE", "Rakan_EventLogs")
STATE_TABLE = os.getenv("STATE_TABLE", "Rakan_DeviceState")
LAM_FUNCTION_NAME = os.getenv("LAM_FUNCTION_NAME", "LAMDecisionEngine")
COMMAND_TOPIC_FMT = os.getenv("COMMAND_TOPIC_FMT", "rakan/commands/{deviceId}")

dynamodb = boto3.client("dynamodb", region_name=AWS_REGION)
iot = boto3.client("iot-data", region_name=AWS_REGION)
lam = boto3.client("lambda", region_name=AWS_REGION)


# -----------------------------
# HELPERS
# -----------------------------

def _log_event(event: dict) -> None:
    try:
        dynamodb.put_item(
            TableName=EVENT_TABLE,
            Item={
                "logId": {"S": str(uuid.uuid4())},          # MUST match table PK
                "timestamp": {"S": datetime.utcnow().isoformat() + "Z"},
                "event": {"S": json.dumps(event)},
            },
        )
    except Exception as e:
        print(f"[EventProcessor] Failed to log event: {e}")



def _update_device_state(device_id: str, decision: dict, event: dict) -> None:
    """
    Update the DeviceState table with the latest decision + event.
    """
    try:
        timestamp = event.get("timestamp") or datetime.utcnow().isoformat() + "Z"
        dynamodb.update_item(
            TableName=STATE_TABLE,
            Key={"deviceId": {"S": device_id}},
            UpdateExpression="SET #s = :state, updatedAt = :ts",
            ExpressionAttributeNames={"#s": "state"},
            ExpressionAttributeValues={
                ":state": {"S": json.dumps(decision)},
                ":ts": {"S": timestamp},
            },
        )
    except Exception as e:
        print(f"[EventProcessor] Failed to update device state: {e}")


def _call_lam(event: dict) -> dict:
    """
    Call Tristan's AI_DecisionEngine Lambda with the event and
    return its JSON decision.
    """
    try:
        response = lam.invoke(
            FunctionName=LAM_FUNCTION_NAME,
            Payload=json.dumps(event).encode("utf-8"),
        )
        payload_bytes = response.get("Payload").read()
        decision = json.loads(payload_bytes or "{}")
        return decision
    except Exception as e:
        print(f"[EventProcessor] LAM invoke error: {e}")
        return {"error": str(e)}


def _valid_decision(decision: dict) -> bool:
    """
    Check that the LAM decision has the required keys.
    """
    return (
        isinstance(decision, dict)
        and "deviceId" in decision
        and "action" in decision
        and "value" in decision
    )


def _fallback_decision(event: dict) -> dict:
    """
    Safe fallback when LAM fails or returns invalid output.
    """
    return {
        "deviceId": event.get("deviceId", "unknown"),
        "action": "ignore",
        "value": None,
        "reason": "LAM error or invalid response; fallback used.",
    }


def _publish_command(decision: dict) -> None:
    """
    Publish the decision as a command to AWS IoT Core.
    Topic: rakan/commands/{deviceId}
    """
    try:
        device_id = decision["deviceId"]
        topic = COMMAND_TOPIC_FMT.format(deviceId=device_id)
        iot.publish(
            topic=topic,
            qos=1,
            payload=json.dumps(decision),
        )
    except Exception as e:
        print(f"[EventProcessor] Failed to publish command: {e}")


# -----------------------------
# MAIN EVENT PROCESSOR CLASS
# -----------------------------

class EventProcessor:
    """
    EventProcessor:
      1. Receives event from AWS IoT Rule (Lambda trigger)
      2. Logs the raw event to EventLogs
      3. Calls LAM (AI_DecisionEngine) with the event
      4. Validates LAM decision or uses fallback
      5. Publishes command to IoT Core
      6. Updates device state in DeviceState
      7. Returns decision for debugging / API
    """

    def handle_event(self, event: dict) -> dict:
        # Allow string payloads (just in case)
        if isinstance(event, str):
            try:
                event = json.loads(event)
            except Exception:
                return {"error": "Event must be valid JSON string or dict"}

        if not isinstance(event, dict):
            return {"error": "Event must be a JSON object"}

        device_id = event.get("deviceId")
        if not device_id:
            return {"error": "Missing deviceId in event"}

        # 1. Log the incoming event
        _log_event(event)

        # 2. Call LAM to compute a decision
        lam_decision = _call_lam(event)

        # 3. Validate or fallback
        if not _valid_decision(lam_decision):
            lam_decision = _fallback_decision(event)

        # Make sure we always include a timestamp + reason
        if "reason" not in lam_decision:
            lam_decision["reason"] = "No reason provided by LAM."

        lam_decision.setdefault(
            "timestamp", datetime.utcnow().isoformat() + "Z"
        )

        # 4. Publish resulting command to IoT Core
        _publish_command(lam_decision)

        # 5. Update device state
        _update_device_state(device_id, lam_decision, event)

        # 6. Return decision + event for debugging / API layers
        return {
            "status": "processed",
            "event": event,
            "decision": lam_decision,
        }


# -----------------------------
# LAMBDA ENTRYPOINT
# -----------------------------

def lambda_handler(event, context):
    """
    AWS Lambda entrypoint.
    This is what the AWS IoT Rule (rakan/events) should invoke.
    """
    processor = EventProcessor()
    return processor.handle_event(event)
