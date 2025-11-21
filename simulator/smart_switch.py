# simulators/smart_switch.py
import time
import json
import logging

from simulators.base_device import BaseDevice

LOG = logging.getLogger("smart_switch")
LOG.setLevel(logging.INFO)


class SmartSwitch(BaseDevice):
    """
    SmartSwitch simulator:
      - publishes state on change (and periodic heartbeat)
      - subscribes to rakan/commands/{deviceId}
      - supports commands: turn_on, turn_off, set_brightness
      - sends an ack event to the events topic after state change
    """

    def __init__(self, *args, heartbeat: float = 30.0, **kwargs):
        super().__init__(*args, **kwargs)
        # initial state
        self.state = {"power": "OFF", "brightness": 0}
        self.heartbeat = float(heartbeat)

    def _run_loop(self):
        """Publish heartbeat state periodically; actual state changes happen in handle_command."""
        LOG.info("[%s] SmartSwitch loop started (heartbeat=%ss)", self.client_id, self.heartbeat)
        while not self._stop_event.is_set():
            try:
                # periodic heartbeat publish of state
                payload = {"deviceId": self.client_id, "type": "switch_state", "state": self.state}
                self.publish_event(payload)
            except Exception as e:
                self.last_error = str(e)
                LOG.exception("[%s] Error publishing heartbeat: %s", self.client_id, e)

            # sleep with stop responsiveness
            for _ in range(int(max(1, self.heartbeat * 10))):
                if self._stop_event.is_set():
                    break
                time.sleep(self.heartbeat / 10.0)
        LOG.info("[%s] SmartSwitch loop exiting", self.client_id)

    def handle_command(self, topic: str, payload):
        """
        Expect JSON command payloads, e.g.:
          {"deviceId":"switch-001","command":"turn_on"}
          {"deviceId":"switch-001","command":"set_brightness","value":50}
        """
        try:
            if isinstance(payload, (bytes, bytearray)):
                payload = payload.decode()
            data = json.loads(payload) if isinstance(payload, str) else payload
        except Exception:
            LOG.exception("[%s] Invalid command payload: %s", self.client_id, payload)
            self.last_error = "invalid_command_payload"
            return

        cmd = data.get("command")
        try:
            if cmd == "turn_on":
                self.state["power"] = "ON"
                if self.state.get("brightness", 0) == 0:
                    self.state["brightness"] = 100
            elif cmd == "turn_off":
                self.state["power"] = "OFF"
            elif cmd == "set_brightness":
                val = int(data.get("value", 0))
                val = max(0, min(100, val))
                self.state["brightness"] = val
                # if brightness > 0 ensure power is ON
                if val > 0:
                    self.state["power"] = "ON"
                else:
                    # if brightness 0, treat as OFF
                    self.state["power"] = "OFF"
            else:
                LOG.info("[%s] Unknown command received: %s", self.client_id, cmd)
                return
            # ack the state change
            ack = {"deviceId": self.client_id, "type": "switch_state", "state": self.state}
            self.publish_event(ack)
            LOG.info("[%s] Applied command %s, new state=%s", self.client_id, cmd, self.state)
        except Exception as e:
            self.last_error = str(e)
            LOG.exception("[%s] Error applying command %s: %s", self.client_id, cmd, e)
