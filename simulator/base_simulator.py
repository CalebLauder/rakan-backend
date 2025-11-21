import threading
import time
import json
from simulator.shared.mqtt_client import DeviceClient
from simulator.shared.utils import ensure_timestamp, safe_dumps

class BaseDevice:
    def __init__(self, device_id, client_id, endpoint, cert, key, ca,
                 topic_events, topic_command):
        self.device_id = device_id
        self.topic_events = topic_events
        self.topic_command = topic_command
        self.client = DeviceClient(client_id, endpoint, cert, key, ca,
                                   on_message=self._on_message)
        self._stop_event = threading.Event()
        self._thread = None

        # Device state
        self.state = {}
        self.last_seen = None
        self.sent_count = 0
        self.received_commands_count = 0
        self.last_error = None

    def start(self):
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self.client.disconnect()
        if self._thread:
            self._thread.join()

    def _run_loop(self):
        # Override in child class for specific device logic
        while not self._stop_event.is_set():
            try:
                self.publish_event()
                time.sleep(5)  # default, override in child
            except Exception as e:
                self.last_error = str(e)

    def publish_event(self, payload=None):
        if payload is None:
            payload = {
                "deviceId": self.device_id,
                "timestamp": ensure_timestamp(),
                "state": self.state
            }
        self.client.publish(self.topic_events, safe_dumps(payload))
        self.sent_count += 1
        self.last_seen = time.time()

    def _on_message(self, client, userdata, msg):
        # Override in child
        self.received_commands_count += 1

    def status(self):
        return {
            "device_id": self.device_id,
            "state": self.state,
            "last_seen": self.last_seen,
            "sent_count": self.sent_count,
            "received_commands_count": self.received_commands_count,
            "last_error": self.last_error
        }
