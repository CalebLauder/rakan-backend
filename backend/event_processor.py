import json
import os
import requests

# Database helpers (Martin's DB Layer)
from backend.db import (
    get_device_state,
    put_device_state,
    log_event
)

# Command publisher (Robby’s AWS IoT publishing)
from backend.command_publisher import publish_command


# -----------------------------
# ENVIRONMENT VARIABLES
# -----------------------------
LAM_API_KEY = os.getenv("LAM_API_KEY", "")
LAM_URL = os.getenv("LAM_URL", "")


# -----------------------------
# LAM CALL FUNCTION
# -----------------------------
def call_lam(lam_input):
    """
    Sends event + state to the LAM reasoning engine
    and returns structured JSON with an AI decision.
    """

    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LAM_API_KEY}"
        }

        resp = requests.post(
            LAM_URL,
            headers=headers,
            json=lam_input,
            timeout=5
        )

        return resp.json()

    except Exception as e:
        return {"error": str(e)}


# -----------------------------
# VALIDATE LAM OUTPUT
# -----------------------------
def validate_lam_output(obj):
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


# -----------------------------
# FALLBACK RULE
# -----------------------------
def fallback_rule(event):
    """
    Fallback logic for when LAM fails.
    Always choose "ignore" for safety.
    """
    return {
        "action": "ignore",
        "deviceId": event["deviceId"],
        "value": None,
        "reason": "LAM unavailable, fallback executed."
    }


# -----------------------------
# MAIN EVENT PROCESSOR
# -----------------------------
def handler(event, context=None):
    """
    === EVENT PROCESSING PIPELINE ===

    1. Receive & parse event from AWS IoT
    2. Query DynamoDB for previous state
    3. Send event + state to LAM for reasoning
    4. Validate LAM output (fallback if needed)
    5. Build command payload
    6. Publish command to AWS IoT
    7. Update device state in DynamoDB
    8. Log full event (event + LAM + command)
    """

    # ----------------------------------------------------
    # 1. Parse event
    # ----------------------------------------------------
    if isinstance(event, str):
        try:
            event = json.loads(event)
        except Exception:
            return {"error": "Invalid JSON string received"}

    device_id = event.get("deviceId")
    if not device_id:
        return {"error": "Missing deviceId in event"}

    # ----------------------------------------------------
    # 2. Get previous device state
    # ----------------------------------------------------
    previous_state = get_device_state(device_id)

    # ----------------------------------------------------
    # 3. Build LAM input object
    # ----------------------------------------------------
    lam_input = {
        "event": event,
        "previousState": previous_state,
    }

    lam_decision = call_lam(lam_input)

    # ----------------------------------------------------
    # 4. Validate LAM response
    # ----------------------------------------------------
    if not validate_lam_output(lam_decision):
        lam_decision = fallback_rule(event)

    # ----------------------------------------------------
    # 5. Build command payload
    # ----------------------------------------------------
    cmd = {
        "deviceId": lam_decision["deviceId"],
        "action": lam_decision["action"],
        "value": lam_decision["value"],
        "reason": lam_decision.get("reason", "")
    }

    # ----------------------------------------------------
    # 6. Publish command to AWS IoT
    # ----------------------------------------------------
    publish_command(device_id, cmd)

    # ----------------------------------------------------
    # 7. Update device state
    # ----------------------------------------------------
    put_device_state(device_id, {
        "lastEvent": event,
        "lastCommand": cmd,
        "updatedAt": event.get("timestamp", "")
    })

    # ----------------------------------------------------
    # 8. Log everything (event, LAM decision, command)
    # ----------------------------------------------------
    log_event(event, lam_decision, cmd)

    # ----------------------------------------------------
    # Return final output for debugging
    # ----------------------------------------------------
    return {
        "status": "processed",
        "event": event,
        "lam": lam_decision,
        "command": cmd,
    }
