import json
import random
import time

from simulator.config import (
    MQTT_ENDPOINT,
    CA_PATH,
    CERT_PATH,
    KEY_PATH,
    EVENTS_TOPIC,
    COMMANDS_TOPIC_FMT
)

from simulator.base_simulator import BaseDevice


class MotionSensor(BaseDevice):
    def __init__(self, device_id="motion01", client_id="motion01"):

        command_topic = COMMANDS_TOPIC_FMT.format(deviceId=device_id)

        super().__init__(
            device_id=device_id,
            client_id=client_id,
            endpoint=MQTT_ENDPOINT,
            cert=CERT_PATH,
            key=KEY_PATH,
            ca=CA_PATH,
            topic_events=EVENTS_TOPIC,
            topic_command=command_topic
        )

        self.random = random.Random()
        self.motion_prob = 0.10  # 10% chance per cycle


    def _run_loop(self):
        while not self._stop_event.is_set():
            motion_detected = self.random.random() < self.motion_prob

            # NEW backend-compliant payload
            payload = {
                "deviceId": self.device_id,
                "type": "motion",
                "data": {
                    "motion": motion_detected
                },
                "timestamp": time.time()
            }

            self.publish_event(payload)
            time.sleep(5)


    def _on_message(self, client, userdata, msg):
        try:
            command = json.loads(msg.payload.decode())
            print(f"[COMMAND RECEIVED] {command}")

        except Exception as e:
            self.last_error = str(e)


if __name__ == "__main__":
    device = MotionSensor()
    device.start()
    while True:
        time.sleep(1)
