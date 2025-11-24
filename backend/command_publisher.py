import boto3
import json
import os

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# IoT Data Plane client (used for publishing to MQTT via AWS)
iot_data = boto3.client("iot-data", region_name=AWS_REGION)


def publish_command(deviceId, command_obj):
    """
    Publishes a command to the AWS IoT MQTT topic:
    rakan/commands/{deviceId}
    """
    topic = f"rakan/commands/{deviceId}"

    payload = json.dumps(command_obj)

    try:
        resp = iot_data.publish(
            topic=topic,
            qos=1,
            payload=payload
        )
        return {"status": "ok", "topic": topic, "payload": payload}
    except Exception as e:
        return {"status": "error", "error": str(e), "topic": topic}
