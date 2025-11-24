import json
import boto3

class CommandPublisher:
    def __init__(self):
        self.client = boto3.client("iot-data", region_name="us-east-1")

    def publish(self, device_id, command: dict):
        """
        command must contain:
        - deviceId
        - action
        - value
        - reason (optional)
        - timestamp (optional)
        """

        topic = f"rakan/commands/{device_id}"
        payload = json.dumps(command)

        self.client.publish(
            topic=topic,
            qos=1,
            payload=payload
        )
        print(f"[CommandPublisher] Published → {topic}: {payload}")
