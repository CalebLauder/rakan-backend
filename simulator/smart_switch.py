import time
import json

from simulator.config import (
    MQTT_ENDPOINT,
    CA_PATH,
    CERT_PATH,
    KEY_PATH,
    EVENTS_TOPIC,
    COMMANDS_TOPIC_FMT,
)

from simulator.base_simulator import BaseDevice


class SmartSwitch(BaseDevice):
    def __init__(self, device_id="switch01", client_id="switch01"):
        command_topic = COMMANDS_TOPIC_FMT.format(deviceId=device_id)

        super().__init__(
            device_id=device_id,
            client_id=client_id,
            endpoint=MQTT_ENDPOINT,
            cert=CERT_PATH,
            key=KEY_PATH,
            ca=CA_PATH,
            topic_events=EVENTS_TOPIC,
            topic_command=command_topic,
        )

        self.state = {"power": "OFF", "brightness": 0}

    def _on_message(self, client, userdata, msg):
        self.received_commands_count += 1
        try:
            command = json.loads(msg.payload.decode())
            action = command.get("action")

            if action == "turn_on":
                self.state["power"] = "ON"
            elif action == "turn_off":
                self.state["power"] = "OFF"
            elif action == "set_brightness":
                value = command.get("value", 0)
                self.state["brightness"] = max(0, min(100, value))

            print(f"[SmartSwitch] Command received: {command}")
            # publish ack
            ack = {
                "deviceId": self.device_id,
                "sensor": "switch_state",
                "state": self.state,
                "timestamp": time.time(),
            }
            self.publish_event(ack)

        except Exception as e:
            self.last_error = str(e)


if __name__ == "__main__":
    device = SmartSwitch()
    device.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[SmartSwitch] Stopping...")
        device.stop()
