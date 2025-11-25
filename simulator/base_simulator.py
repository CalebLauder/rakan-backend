import threading
import time
import json

from simulator.shared.mqtt_client import DeviceClient
from simulator.shared.utils import ensure_timestamp, safe_dumps


class BaseDevice:
    def __init__(self, device_id, client_id, endpoint, cert, key, ca,
                 topic_events, topic_command=None):

        self.device_id = device_id
        self.topic_events = topic_events
        self.topic_command = topic_command

        self.client = DeviceClient(client_id, endpoint, cert, key, ca)
        self.client.set_message_callback(self._on_message)

        self._stop_event = threading.Event()
        self._thread = None

        self.state = {}
        self.last_seen = None
        self.sent_count = 0
        self.received_commands_count = 0
        self.last_error = None

    def start(self):
        print(f"[{self.__class__.__name__}] Starting device {self.device_id}...")

        self.client.connect()

        if self.topic_command:
            print(f"[MQTT] Subscribing to {self.topic_command}")
            self.client.subscribe(self.topic_command)

        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self.client.disconnect()

    def _run_loop(self):
        while not self._stop_event.is_set():
            try:
                self.publish_event()
                time.sleep(5)
            except Exception as e:
                self.last_error = str(e)

    def publish_event(self, payload=None):
        if payload is None:
            payload = {
                "deviceId": self.device_id,
                "timestamp": ensure_timestamp(),
                "state": self.state
            }

        print(f"[EVENT] Publishing → {self.topic_events}: {payload}")
        self.client.publish(self.topic_events, safe_dumps(payload))
        self.sent_count += 1
        self.last_seen = time.time()

    def _on_message(self, client, userdata, msg):
        # to be overridden
        self.received_commands_count += 1

    def status(self):
        return {
            "device_id": self.device_id,
            "state": self.state,
            "sent_count": self.sent_count,
            "received_commands_count": self.received_commands_count,
            "last_seen": self.last_seen,
            "last_error": self.last_error
        }
