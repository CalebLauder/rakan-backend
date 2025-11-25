import random
import time
import json

from .base_simulator import BaseDevice
from simulator.config import (
    MQTT_ENDPOINT,
    CERT_PATH,
    KEY_PATH,
    CA_PATH,
    EVENTS_TOPIC,
    COMMANDS_TOPIC_FMT
)


class MotionSensor(BaseDevice):
    def __init__(self, device_id, client_id, endpoint, cert, key, ca,
                 motion_prob_day=0.02, motion_prob_night=0.1, seed=None):

        # Correct command topic formatting
        command_topic = COMMANDS_TOPIC_FMT.format(deviceId=device_id)

        super().__init__(
            device_id=device_id,
            client_id=client_id,
            endpoint=endpoint,
            cert=cert,
            key=key,
            ca=ca,
            topic_events=EVENTS_TOPIC,
            topic_command=command_topic
        )

        self.motion_prob_day = motion_prob_day
        self.motion_prob_night = motion_prob_night
        self.random = random.Random(seed)
        self.current_motion = False

    # ------------------------------
    # MAIN SIM LOOP
    # ------------------------------
    def _run_loop(self):
        while not self._stop_event.is_set():
            # random chance of motion
            self.current_motion = self.random.random() < self.motion_prob_day

            payload = {
                "deviceId": self.device_id,
                "sensor": "motion",
                "value": self.current_motion,
                "timestamp": time.time()
            }

            self.publish_event(payload)
            time.sleep(5)

    # ------------------------------
    # COMMAND HANDLING
    # ------------------------------
    def _on_message(self, client, userdata, msg):
        self.received_commands_count += 1

        try:
            command = json.loads(msg.payload)
            print(f"[MotionSensor] Received command: {command}")
        except Exception as e:
            self.last_error = str(e)


# ------------------------------
# MAIN RUNNER
# ------------------------------
if __name__ == "__main__":
    device = MotionSensor(
        device_id="motion01",
        client_id="motion01",
        endpoint=MQTT_ENDPOINT,
        cert=CERT_PATH,
        key=KEY_PATH,
        ca=CA_PATH
    )

    print(f"[MotionSensor] Starting device {device.device_id}...")
    device.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[MotionSensor] Stopping...")
        device.stop()
