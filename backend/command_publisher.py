import json
import os
import logging

import boto3

from backend.db import log_event


# --------------------------------------------------
# ENVIRONMENT VARIABLES (Lambda env)
# --------------------------------------------------
# This is your ATS endpoint from IoT Core Settings
MQTT_ENDPOINT = os.getenv(
    "MQTT_ENDPOINT",
    "a2cu3qgpy7qzdx-ats.iot.us-east-1.amazonaws.com",
)

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

COMMAND_TOPIC_PREFIX = "rakan/commands/"  # Final topic: rakan/commands/{deviceId}


# --------------------------------------------------
# LOGGER SETUP
# --------------------------------------------------
logger = logging.getLogger("command_publisher")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] command_publisher: %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


# --------------------------------------------------
# AWS IoT DATA PLANE CLIENT
# --------------------------------------------------
# Lambda uses AWS credentials and IAM role, NOT device certs
iot_data = boto3.client(
    "iot-data",
    region_name=AWS_REGION,
    endpoint_url=f"https://{MQTT_ENDPOINT}",
)


# --------------------------------------------------
# MAIN PUBLISH FUNCTION
# --------------------------------------------------
def publish_command(device_id: str, command_dict: dict) -> dict:
    """
    Publishes a command to AWS IoT MQTT using the IoT Data Plane API.

    Steps:
      1. Build MQTT topic: rakan/commands/{deviceId}
      2. Convert command to JSON
      3. Call iot-data.publish(...)
      4. Log command to DynamoDB
    """

    try:
        if not device_id:
            raise ValueError("device_id is required for publish_command")

        # 1. Build topic
        topic = f"{COMMAND_TOPIC_PREFIX}{device_id}"

        # 2. Convert command to JSON string
        payload = json.dumps(command_dict)

        logger.info(f"Publishing MQTT command to {topic}: {payload}")

        # 3. Publish via AWS IoT Data Plane
        iot_data.publish(
            topic=topic,
            qos=1,
            payload=payload,
        )

        # 4. Log command in EventLogs
        log_event(
            event={"source": "backend", "type": "command_issue"},
            lam_decision={},  # already logged in event_processor; keep minimal here
            command=command_dict,
        )

        return {"published": True, "topic": topic, "payload": command_dict}

    except Exception as e:
        logger.error(f"Failed to publish command: {e}")

        # Log failure as an event as well
        log_event(
            event={"source": "backend", "type": "command_error"},
            lam_decision={"error": True},
            command={"error": str(e), "deviceId": device_id},
        )

        return {"published": False, "error": str(e)}
