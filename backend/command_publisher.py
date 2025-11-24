import json
import os
import ssl
import logging

import paho.mqtt.client as mqtt

from backend.db import log_event




# --------------------------------------------------
# ENVIRONMENT VARIABLES (from backend/README / .env)
# --------------------------------------------------
MQTT_ENDPOINT = os.getenv(
    "MQTT_ENDPOINT",
    "a2cu3qgpy7qzdx-ats.iot.us-east-1.amazonaws.com",
)
MQTT_CERT_PATH = os.getenv("MQTT_CERT_PATH", "certs/device.pem.crt")
MQTT_PRIVATE_KEY_PATH = os.getenv("MQTT_PRIVATE_KEY_PATH", "certs/private.pem.key")
MQTT_CA_PATH = os.getenv("MQTT_CA_PATH", "certs/AmazonRootCA1.pem")

COMMAND_TOPIC_PREFIX = "rakan/commands/"  # Final topic: rakan/commands/{deviceId}


# --------------------------------------------------
# LOGGER SETUP
# --------------------------------------------------
logger = logging.getLogger("command_publisher")
if not logger.handlers:
    # Avoid adding multiple handlers if module re-imports
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] command_publisher: %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


# --------------------------------------------------
# MQTT CLIENT SETUP
# --------------------------------------------------
def create_mqtt_client() -> mqtt.Client:
    """
    Creates a secure MQTT client using AWS IoT certificates.
    """
    client = mqtt.Client()

    # TLS / certificate configuration
    client.tls_set(
        ca_certs=MQTT_CA_PATH,
        certfile=MQTT_CERT_PATH,
        keyfile=MQTT_PRIVATE_KEY_PATH,
        tls_version=ssl.PROTOCOL_TLSv1_2,
    )

    return client


mqtt_client = create_mqtt_client()


def ensure_connected():
    """
    Ensures MQTT client is connected before publishing.
    Reconnects automatically if connection is lost.
    """
    try:
        if not mqtt_client.is_connected():
            logger.info(f"Connecting to AWS IoT at {MQTT_ENDPOINT} ...")
            mqtt_client.connect(MQTT_ENDPOINT, port=8883, keepalive=60)
            mqtt_client.loop_start()
    except Exception as e:
        logger.error(f"MQTT connection error: {e}")
        raise


# --------------------------------------------------
# MAIN PUBLISH FUNCTION
# --------------------------------------------------
def publish_command(device_id: str, command_dict: dict) -> dict:
    """
    Publishes a command to AWS IoT MQTT and logs the action.

    Steps:
      1. Build MQTT topic: rakan/commands/{deviceId}
      2. Convert command to JSON
      3. Ensure MQTT connection
      4. Publish to AWS IoT
      5. Log command to DynamoDB
    """

    try:
        if not device_id:
            raise ValueError("device_id is required for publish_command")

        # 1. Build topic
        topic = f"{COMMAND_TOPIC_PREFIX}{device_id}"

        # 2. Convert command to JSON string
        payload = json.dumps(command_dict)

        logger.info(f"Publishing MQTT command to {topic}: {payload}")

        # 3. Ensure MQTT connection is alive
        ensure_connected()

        # 4. Publish (QoS 1 = at least once)
        mqtt_client.publish(topic, payload, qos=1)

        # 5. Log command in EventLogs
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
