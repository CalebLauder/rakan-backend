# simulators/base_device.py
import threading
import time
import logging
import json
from typing import Optional

from shared.mqtt_client import DeviceClient
from shared.utils import ensure_timestamp, safe_dumps

LOG = logging.getLogger("base_device")
LOG.setLevel(logging.INFO)


class BaseDevice:
    """
    Base device abstraction for simulators.
    Responsibilities:
      - create/connect MQTT client (via DeviceClient)
      - subscribe helper for command topic (if provided)
      - lifecycle: start() / stop()
      - small internal state and metrics
    """

    def __init__(
        self,
        client_id: str,
        endpoint: str,
        cert: Optional[str],
        key: Optional[str],
        ca: Optional[str],
        topic_events: str,
        topic_command: Optional[str] = None,
        qos: int = 1,
    ):
        self.client_id = client_id
        self.endpoint = endpoint
        self.cert = cert
        self.key = key
        self.ca = ca
        self.topic_events = topic_events
        self.topic_command = topic_command
        self.qos = qos

        # mqtt client wrapper (from shared/mqtt_client.py)
        self.client = DeviceClient(
            client_id=self.client_id,
            endpoint=self.endpoint,
            cert=self.cert,
            key=self.key,
            ca=self.ca,
            use_ws=False,
        )

        # lifecycle
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        # metrics & state
        self.sent_count = 0
        self.received_commands_count = 0
        self.last_error: Optional[str] = None
        self.last_seen: Optional[int] = None  # unix timestamp of last publish
        self.state = {}  # small state store (device-specific)

    # -------- lifecycle -------------------------------------------------
    def start(self):
        """Start the device: connect and start background loop thread."""
        LOG.info("[%s] Starting device", self.client_id)
        try:
            self.client.connect()
            if self.topic_command:
                # per-device command handling
                self.client.set_message_callback(self._on_message)
                self.client.subscribe(self.topic_command, qos=self.qos)
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
        except Exception as e:
            self.last_error = str(e)
            LOG.exception("[%s] Error starting device: %s", self.client_id, e)
            raise

    def stop(self, timeout: float = 2.0):
        """Signal loop to stop and disconnect client."""
        LOG.info("[%s] Stopping device", self.client_id)
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=timeout)
        try:
            self.client.disconnect()
        except Exception as e:
            LOG.debug("[%s] Error during disconnect: %s", self.client_id, e)

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive() and not self._stop_event.is_set()

    # -------- abstract loop -------------------------------------------------
    def _run_loop(self):
        """Override in subclass with device-specific behavior. Should check _stop_event regularly."""
        raise NotImplementedError("Subclasses must implement _run_loop")

    # -------- publish helper -------------------------------------------------
    def publish_event(self, payload: dict):
        """Publish an event to the configured events topic. Adds timestamp and updates metrics."""
        try:
            payload = ensure_timestamp(payload)
            self.last_seen = int(payload.get("timestamp", time.time()))
            payload_str = safe_dumps(payload)
            self.client.publish(self.topic_events, payload_str, qos=self.qos)
            self.sent_count += 1
            LOG.debug("[%s] Published to %s: %s", self.client_id, self.topic_events, payload_str)
        except Exception as e:
            self.last_error = str(e)
            LOG.exception("[%s] Failed to publish event: %s", self.client_id, e)

    # -------- command handling -------------------------------------------------
    def _on_message(self, client, userdata, msg):
        """Internal callback from DeviceClient when a command arrives."""
        try:
            self.received_commands_count += 1
            payload = msg.payload.decode() if isinstance(msg.payload, (bytes, bytearray)) else msg.payload
            LOG.debug("[%s] Received command on %s: %s", self.client_id, msg.topic, payload)
            # call subclass hook
            self.handle_command(msg.topic, payload)
        except Exception as e:
            self.last_error = str(e)
            LOG.exception("[%s] Error in _on_message: %s", self.client_id, e)

    def handle_command(self, topic: str, payload):
        """
        Default handler: subclasses override. payload is raw string or bytes.
        """
        LOG.info("[%s] handle_command not implemented in subclass. topic=%s payload=%s", self.client_id, topic, payload)

    # -------- utility/status -------------------------------------------------
    def status(self) -> dict:
        """Return current status & metrics for diagnostics."""
        return {
            "client_id": self.client_id,
            "is_running": self.is_running(),
            "sent_count": self.sent_count,
            "received_commands_count": self.received_commands_count,
            "last_error": self.last_error,
            "last_seen": self.last_seen,
            "state": self.state,
        }
