import json
import os
import ssl
import logging
import paho.mqtt.client as mqtt

from backend.db import log_event


# --------------------------------------------------
# ENVIRONMENT VARIABLES
# --------------------------------------------------
AWS_IOT_ENDPOINT = os.getenv("MQTT_ENDPOINT", "")
CERT_PATH = os.getenv("CERT_PATH", "")
KEY_PATH = os.getenv("KEY_PATH", "")
CA_PATH = os.getenv("CA_PATH", "")
COMMAND_TOPIC_PREFIX = "rakan/commands/"


# --------------------------------------------------
# LOGGER SETUP
# --------------------------------------------------
logger = logging.getLogger("command_publisher")
logger.setLevel(logging.INFO)


# --------------------------------------------------
# MQTT CLIENT SETUP
# --------------------------------------------------
def create_mqtt_client():
    """
    Creates a secure MQTT client using AWS IoT certificates.
    """

    client = mqtt.Client()

    # TLS / cert config
    client.tls_set(
        ca_certs=CA_PATH,
        certfile=CERT_PATH,
        keyfile=KEY_PATH,
        tls_version=ssl.PROTOCOL_TLSv1_2,
    )

    return client


mqtt_client = create_mqtt_client()


# --------------------------------------------------
# CONNECT WITH RETRY LOGIC
# --------------------------------------------------
def ensure_connected():
    """
    Ensures MQTT client is connected before publishing.
    Reconnects automatically if connection is lost.
    """
    try:
        if not mqtt_client.is_connected():
            mqtt_client.connect(AWS_IOT_ENDPOINT, 8883, keepalive=60)
            mqtt_client.loop_start()
    except Exception as e:
        logger.error(f"MQTT connection error: {e}")


# --------------------------------------------------
# MAIN PUBLISH FUNCTION
# --------------------------------------------------
def publish_command(device_id, command_dict):
    """
    Publishes a command to AWS IoT MQTT and logs the action.

    Steps:
      1. Build MQTT topic
      2. Convert command to JSON
      3. Ensure connection
      4. Publish to AWS IoT
      5. Log command to DynamoDB
    """

    try:
        # 1. Build topic
        topic = f"{COMMAND_TOPIC_PREFIX}{device_id}"

        # 2. Convert command to JSON string
        payload = json.dumps(command_dict)

        logger.info(f"Publishing to {topic}: {payload}")

        # 3. Ensure MQTT connection is alive
        ensure_connected()

        # 4. Publish
        mqtt_client.publish(topic, payload, qos=1)

        # 5. Log command
        log_event(
            event={"system": "backend"},
            lam_decision={"auto": True},
            command=command_dict
        )

        return {"published": True, "topic": topic, "payload": command_dict}

    except Exception as e:
        logger.error(f"Failed to publish command: {e}")

        # Log failure
        log_event(
            event={"system": "backend"},
            lam_decision={"error": True},
            command={"error": str(e)}
        )

        return {"published": False, "error": str(e)}
