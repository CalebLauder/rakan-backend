from command_publisher import CommandPublisher

class EventProcessor:
    def __init__(self):
        self.publisher = CommandPublisher()

    def handle_event(self, event):
        device_id = event.get("deviceId")
        event_type = event.get("type")
        data = event.get("data", {})

        print(f"Received event from {device_id}: {data}")

        if event_type == "motion" and data.get("motion") is True:
            self.publisher.publish(device_id, "switch", True)

        if event_type == "temperature":
            temp = data.get("temperature")
            if temp and temp > 75:
                self.publisher.publish(device_id, "cooling", True)

if __name__ == "__main__":
    processor = EventProcessor()

    # Test event
    test_event = {
        "deviceId": "device1",
        "type": "motion",
        "data": {
            "motion": True
        }
    }

    processor.handle_event(test_event)
