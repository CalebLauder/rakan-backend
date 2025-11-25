import random
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


class TemperatureSensor(BaseDevice):
    def __init__(self, device_id="temp01", client_id="temp01",
                 baseline=22.0, seed=None):

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

        self.baseline = baseline
        self.setpoint = None
        self.random = random.Random(seed)

     def _run_loop(self):
        while not self._stop_event.is_set():
            drift = self.random.uniform(-0.5, 0.5)
            temp = (
                self.setpoint
                if self.setpoint is not None
                else self.baseline + drift
            )

            payload = {
                "deviceId": self.device_id,
                "type": "temperature",
                "data": {
                    "temperature": temp
                },
                "timestamp": time.time(),
            }

            self.publish_event(payload)
            time.sleep(3)


    def _on_message(self, client, userdata, msg):
        self.received_commands_count += 1
        try:
            command = json.loads(msg.payload.decode())
            action = command.get("action")
            if action == "set_setpoint":
                self.setpoint = command.get("value")
            elif action == "clear_setpoint":
                self.setpoint = None
            print(f"[TemperatureSensor] Command received: {command}")
        except Exception as e:
            self.last_error = str(e)


if __name__ == "__main__":
    device = TemperatureSensor()
    device.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[TemperatureSensor] Stopping...")
        device.stop()
