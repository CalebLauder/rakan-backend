import json
import os
import requests

# Database helpers (Martin's DB Layer)
from backend.db import (
    get_device_state,
    put_device_state,
    log_event,
)

# Command publisher (publishes MQTT commands to AWS IoT)
from backend.command_publisher import publish_command



# --------------------------------------------------
# ENVIRONMENT VARIABLES (from backend/README / .env)
# --------------------------------------------------
LAM_API_KEY = os.getenv("LAM_API_KEY", "")
LAM_URL = os.getenv("LAM_URL", "")


# --------------------------------------------------
# LAM CALL FUNCTION
# --------------------------------------------------
def call_lam(lam_input: dict) -> dict:
    """
    Sends event + state to the LAM reasoning engine
    and returns structured JSON with an AI decision.
    """

    if not LAM_URL:
        # If not configured, immediately fallback
        return {"error": "LAM_URL not configured"}

    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LAM_API_KEY}",
        }

        resp = requests.post(
            LAM_URL,
            headers=headers,
            json=lam_input,
            timeout=5,
        )
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


# --------------------------------------------------
# VALIDATE LAM OUTPUT
# --------------------------------------------------
def validate_lam_output(obj: dict) -> bool:
    """
    Ensures LAM returns a JSON object with:
    - action
    - deviceId
    - value
    """
    return (
        isinstance(obj, dict)
        and "action" in obj
        and "deviceId" in obj
        and "value" in obj
    )


# --------------------------------------------------
# FALLBACK RULE
# --------------------------------------------------
def fallback_rule(event: dict) -> dict:
    """
    Fallback logic for when LAM fails.
    Always choose "ignore" for safety.
    """
    return {
        "action": "ignore",
        "deviceId": event.get("deviceId", "unknown"),
        "value": None,
        "reason": "LAM unavailable or invalid output, fallback executed.",
    }


# --------------------------------------------------
# MAIN EVENT PROCESSOR (LAMBDA HANDLER)
# --------------------------------------------------
def handler(event, context=None):
    """
    === EVENT PROCESSING PIPELINE ===

    1. Receive & parse event from AWS IoT
    2. Query DynamoDB for previous state
    3. Send event + state to LAM for reasoning
    4. Validate LAM output (fallback if needed)
    5. Build command payload
    6. Publish command to AWS IoT MQTT
    7. Update device state in DynamoDB
    8. Log full event (event + LAM + command)
    """

    # ------------------------------------------------
    # 1. Parse event
    # ------------------------------------------------
    if isinstance(event, str):
        try:
            event = json.loads(event)
        except Exception:
            return {"error": "Invalid JSON string received as event"}

    if not isinstance(event, dict):
        return {"error": "Event must be a JSON object"}

    device_id = event.get("deviceId")
    if not device_id:
        return {"error": "Missing deviceId in event"}

    # ------------------------------------------------
    # 2. Get previous device state
    # ------------------------------------------------
    previous_state = get_device_state(device_id)

    # ------------------------------------------------
    # 3. Build LAM input object
    # ------------------------------------------------
    lam_input = {
        "event": event,
        "previousState": previous_state,
    }

    lam_decision = call_lam(lam_input)

    # ------------------------------------------------
    # 4. Validate LAM response
    # ------------------------------------------------
    if not validate_lam_output(lam_decision):
        lam_decision = fallback_rule(event)

    # ------------------------------------------------
    # 5. Build command payload
    # ------------------------------------------------
    cmd = {
        "deviceId": lam_decision["deviceId"],
        "action": lam_decision["action"],
        "value": lam_decision["value"],
        "reason": lam_decision.get("reason", ""),
    }

    # ------------------------------------------------
    # 6. Publish command to AWS IoT MQTT
    # ------------------------------------------------
    publish_command(device_id, cmd)

    # ------------------------------------------------
    # 7. Update device state (DynamoDB)
    # ------------------------------------------------
    put_device_state(
        device_id,
        {
            "lastEvent": event,
            "lastCommand": cmd,
            "updatedAt": event.get("timestamp", ""),
        },
    )

    # ------------------------------------------------
    # 8. Log everything (event, LAM decision, command)
    # ------------------------------------------------
    log_event(event, lam_decision, cmd)

    # Return final output for debugging / API responses
    return {
        "status": "processed",
        "event": event,
        "lam": lam_decision,
        "command": cmd,
    }
