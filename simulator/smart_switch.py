import time
import json
from .base_simulator import BaseDevice
from simulator.config import EVENTS_TOPIC, COMMANDS_TOPIC_FMT

class SmartSwitch(BaseDevice):
    def __init__(self, device_id, client_id, endpoint, cert, key, ca):
        super().__init__(device_id, client_id, endpoint, cert, key, ca,
                         EVENTS_TOPIC, COMMANDS_TOPIC_FMT.format(device_id))
        self.state = {"power": "OFF", "brightness": 0}

    def _on_message(self, client, userdata, msg):
        self.received_commands_count += 1
        try:
            command = json.loads(msg.payload)
            action = command.get("action")
            if action == "turn_on":
                self.state["power"] = "ON"
            elif action == "turn_off":
                self.state["power"] = "OFF"
            elif action == "set_brightness":
                value = command.get("value", 0)
                self.state["brightness"] = max(0, min(100, value))
            # publish ack
            ack = {
                "deviceId": self.device_id,
                "type": "switch_state",
                "state": self.state,
                "timestamp": time.time()
            }
            self.publish_event(ack)
        except Exception as e:
            self.last_error = str(e)
