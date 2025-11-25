import random
import time
from .base_simulator import BaseDevice
from simulator.config import MQTT_ENDPOINT, CERT_PATH, KEY_PATH, CA_PATH, EVENTS_TOPIC, COMMANDS_TOPIC_FMT

class MotionSensor(BaseDevice):
    def __init__(self, device_id, client_id, endpoint, cert, key, ca,
                 motion_prob_day=0.02, motion_prob_night=0.1, seed=None):
        super().__init__(device_id, client_id, endpoint, cert, key, ca,
                         EVENTS_TOPIC, COMMANDS_TOPIC_FMT.format(device_id))
        self.motion_prob_day = motion_prob_day
        self.motion_prob_night = motion_prob_night
        self.random = random.Random(seed)
        self.current_motion = False

    def _run_loop(self):
        while not self._stop_event.is_set():
            self.current_motion = self.random.random() < self.motion_prob_day
            payload = {
                "deviceId": self.device_id,
                "type": "motion",
                "motion": self.current_motion,
                "timestamp": time.time()
            }
            self.publish_event(payload)
            time.sleep(5)

    def _on_message(self, client, userdata, msg):
        self.received_commands_count += 1
        # Example: allow setting motion probability for testing
        try:
            command = json.loads(msg.payload)
            if command.get("action") == "set_motion_prob":
                self.motion_prob_day = command.get("day", self.motion_prob_day)
                self.motion_prob_night = command.get("night", self.motion_prob_night)
        except Exception as e:
            self.last_error = str(e)


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

    # Keep the script alive forever
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[MotionSensor] Stopping...")
        device.stop()

