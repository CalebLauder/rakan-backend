import json
import boto3

class CommandPublisher:
    def __init__(self):
        # THIS MUST RUN OR NOTHING WORKS
        self.client = boto3.client("iot-data", region_name="us-east-1")

    def publish(self, device_id: str, command: dict):
        """
        command must contain:
            deviceId
            action
            value
            reason (optional)
            timestamp (optional)
        """

        topic = f"rakan/commands/{device_id}"
        payload = json.dumps(command)

        self.client.publish(
            topic=topic,
            qos=1,
            payload=payload
        )

        print(f"[CommandPublisher] Published → {topic}: {payload}")


# --------------------------------------------------
# WRAPPER USED BY EventProcessor + API
# --------------------------------------------------
_publisher = CommandPublisher()

def publish_command(device_id: str, command: dict):
    return _publisher.publish(device_id, command)
