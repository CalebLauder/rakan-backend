import json
import os
from backend.db import get_device_state, put_device_state, log_event
from backend.command_publisher import publish_command
import requests

# LAM endpoint or API key
LAM_API_KEY = os.getenv("LAM_API_KEY", "")
LAM_URL = os.getenv("LAM_URL", "")


def call_lam(lam_input):
    """Call the LAM reasoning service and return structured JSON."""
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LAM_API_KEY}",
        }
        resp = requests.post(LAM_URL, headers=headers, json=lam_input)
        return resp.json()
    except Exception as e:
        return {"error": str(e)}


def validate_lam_output(obj):
    """Check if LAM output has required keys."""
    return (
        isinstance(obj, dict)
        and "action" in obj
        and "deviceId" in obj
        and "value" in obj
    )


def fallback_rule(event):
    """Default action if LAM fails — do nothing."""
    return {
        "action": "ignore",
        "deviceId": event["deviceId"],
        "value": None,
        "reason": "LAM unavailable, fallback executed."
    }


def handler(event, context=None):
    """
    Main event-processing logic:
    1. Parse event
    2. Get previous state
    3. Send to LAM
    4. Validate response
    5. Publish command
    6. Update DB
    7. Log everything
    """

    # 1. Parse incoming event
    if isinstance(event, str):
        event = json.loads(event)

    device_id = event.get("deviceId")

    # 2. Fetch device state
    previous_state = get_device_state(device_id)

    # 3. Build LAM input
    lam_input = {
        "event": event,
        "previousState": previous_state,
    }

    lam_decision = call_lam(lam_input)

    # 4. Validate / fallback
    if not validate_lam_output(lam_decision):
        lam_decision = fallback_rule(event)

    # 5. Publish command
    cmd = {
        "deviceId": lam_decision["deviceId"],
        "action": lam_decision["action"],
        "value": lam_decision["value"],
        "reason": lam_decision.get("reason", ""),
    }
    publish_command(device_id, cmd)

    # 6. Update device state
    put_device_state(device_id, {
        "lastAction": cmd,
        "lastEvent": event
    })

    # 7. Log event
    log_event(event, lam_decision, cmd)

    return {
        "status": "processed",
        "event": event,
        "lam": lam_decision,
        "command": cmd,
    }
