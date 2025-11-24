import json
import boto3
import os
from datetime import datetime

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ.get("DDB_TABLE"))

def make_decision(event):
    """
    Expected input format:
    {
      "deviceId": "sensor-001",
      "type": "motion" | "temperature" | "door" | "humidity",
      "data": {
         "motion": true,
         "temperature": 81,
         "humidity": 40
      }
    }
    """

    device_id = event.get("deviceId", "unknown")
    event_type = event.get("type", "unknown")
    data = event.get("data", {})

    # ----- MOTION SENSOR -----
    if event_type == "motion":
        motion_state = data.get("motion", False)

        if motion_state:
            return {
                "deviceId": device_id,
                "action": "switch",
                "value": True,
                "reason": "Motion detected — switching device ON."
            }
        else:
            return {
                "deviceId": device_id,
                "action": "switch",
                "value": False,
                "reason": "No motion — switching device OFF."
            }

    # ----- TEMPERATURE SENSOR -----
    if event_type == "temperature":
        temp = data.get("temperature")

        if temp is None:
            return {
                "deviceId": device_id,
                "action": "ignore",
                "value": None,
                "reason": "Temperature data missing."
            }

        if temp > 75:
            return {
                "deviceId": device_id,
                "action": "cooling",
                "value": temp,
                "reason": f"High temperature ({temp}°F). Cooling activated."
            }
        else:
            return {
                "deviceId": device_id,
                "action": "ignore",
                "value": None,
                "reason": f"Temperature normal ({temp}°F). No action taken."
            }

    # ----- DOOR SENSOR -----
    if event_type == "door":
        is_open = data.get("door_open", False)

        if is_open:
            return {
                "deviceId": device_id,
                "action": "switch",
                "value": True,
                "reason": "Door opened — switching ON related device."
            }
        else:
            return {
                "deviceId": device_id,
                "action": "switch",
                "value": False,
                "reason": "Door closed — switching OFF related device."
            }

    # ----- HUMIDITY SENSOR -----
    if event_type == "humidity":
        humidity = data.get("humidity")

        if humidity is None:
            return {
                "deviceId": device_id,
                "action": "ignore",
                "value": None,
                "reason": "Humidity data missing."
            }

        if humidity > 60:
            return {
                "deviceId": device_id,
                "action": "adjust",
                "value": humidity,
                "reason": f"High humidity ({humidity}%). Adjusting ventilation."
            }
        else:
            return {
                "deviceId": device_id,
                "action": "ignore",
                "value": None,
                "reason": f"Humidity normal ({humidity}%). No action taken."
            }

    # ----- UNKNOWN EVENT TYPE -----
    return {
        "deviceId": device_id,
        "action": "ignore",
        "value": None,
        "reason": f"Unknown event type '{event_type}'. No action taken."
    }


def lambda_handler(event, context):
    decision_output = make_decision(event)

    # Add timestamp for logging in DynamoDB
    decision_output["timestamp"] = datetime.utcnow().isoformat()

    # Save to DynamoDB
    table.put_item(Item=decision_output)

    return {
        "statusCode": 200,
        "body": json.dumps(decision_output)
    }
