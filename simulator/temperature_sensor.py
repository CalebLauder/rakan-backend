import random
import time
from .base_simulator import BaseDevice
from simulator.config import EVENTS_TOPIC, COMMANDS_TOPIC_FMT

class TemperatureSensor(BaseDevice):
    def __init__(self, device_id, client_id, endpoint, cert, key, ca,
                 baseline=22.0, seed=None):
        super().__init__(device_id, client_id, endpoint, cert, key, ca,
                         EVENTS_TOPIC, COMMANDS_TOPIC_FMT.format(device_id))
        self.baseline = baseline
        self.setpoint = None
        self.random = random.Random(seed)

    def _run_loop(self):
        while not self._stop_event.is_set():
            drift = self.random.uniform(-0.5, 0.5)
            temp = self.setpoint if self.setpoint is not None else self.baseline + drift
            payload = {
                "deviceId": self.device_id,
                "type": "temperature",
                "value": temp,
                "timestamp": time.time()
            }
            self.publish_event(payload)
            time.sleep(3)

    def _on_message(self, client, userdata, msg):
        self.received_commands_count += 1
        try:
            command = json.loads(msg.payload)
            if command.get("action") == "set_setpoint":
                self.setpoint = command.get("value")
            elif command.get("action") == "clear_setpoint":
                self.setpoint = None
        except Exception as e:
            self.last_error = str(e)
