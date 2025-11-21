import json

class CommandPublisher:
    """
    Responsible for outputting device commands in the standard contract format.
    Later, this will publish to AWS (SQS, Lambda, etc).
    For now, it just prints.
    """

    def publish(self, device_id, action, value):
        command = {
            "deviceId": device_id,
            "action": action,
            "value": value
        }

        print("Publishing command:", json.dumps(command))
        return command
