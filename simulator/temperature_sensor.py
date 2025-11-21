# simulators/temperature_sensor.py
import time
import random
import logging
import json
from typing import Optional

from simulators.base_device import BaseDevice

LOG = logging.getLogger("temperature_sensor")
LOG.setLevel(logging.INFO)


class TemperatureSensor(BaseDevice):
    """
    Temperature sensor simulator with baseline, drift and noise.
    - interval: seconds between samples (default 3s)
    - baseline: starting temperature (C)
    - drift: max per-step drift
    - noise: gaussian noise sigma
    - supports setpoint changes via commands (apply_command)
    """

    def __init__(
        self,
        *args,
        interval: float = 3.0,
        baseline: float = 22.0,
        drift: float = 0.1,
        noise: float = 0.2,
        seed: Optional[int] = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.interval = float(interval)
        self.value = float(baseline)
        self.drift = float(drift)
        self.noise = float(noise)
        self.random = random.Random(seed) if seed is not None else random.Random()
        self.state = {"value": self.value, "setpoint": None}

    def _run_loop(self):
        LOG.info("[%s] TemperatureSensor loop started (interval=%ss)", self.client_id, self.interval)
        while not self._stop_event.is_set():
            try:
                # apply small drift and noise
                delta = self.random.uniform(-self.drift, self.drift)
                noise = self.random.gauss(0, self.noise)
                self.value = self.value + delta + noise
                # if setpoint present, slowly move towards it
                sp = self.state.get("setpoint")
                if sp is not None:
                    # simple move towards setpoint
                    self.value += (sp - self.value) * 0.02  # small adjustment factor

                payload = {"deviceId": self.client_id, "type": "temperature", "value": round(self.value, 2)}
                self.state["value"] = round(self.value, 2)
                self.publish_event(payload)
            except Exception as e:
                self.last_error = str(e)
                LOG.exception("[%s] Error in temperature loop: %s", self.client_id, e)
            # sleep but be responsive to stop
            for _ in range(int(max(1, self.interval * 10))):
                if self._stop_event.is_set():
                    break
                time.sleep(self.interval / 10.0)
        LOG.info("[%s] TemperatureSensor loop exiting", self.client_id)

    def handle_command(self, topic: str, payload):
        """Simple command handler - supports setting a setpoint via JSON: {'command':'set_setpoint','value':25}"""
        try:
            # payload may be bytes or string
            if isinstance(payload, (bytes, bytearray)):
                payload = payload.decode()
            data = json.loads(payload) if isinstance(payload, str) else payload
        except Exception:
            # if parse error, log and ignore
            LOG.exception("[%s] temperature sensor received invalid command payload: %s", self.client_id, payload)
            self.last_error = "invalid_command_payload"
            return

        cmd = data.get("command")
        if cmd == "set_setpoint":
            try:
                val = float(data.get("value"))
                self.state["setpoint"] = val
                LOG.info("[%s] Setpoint updated to %s", self.client_id, val)
                # optionally publish acknowledgement
                ack = {"deviceId": self.client_id, "type": "temperature_setpoint", "value": val}
                self.publish_event(ack)
            except Exception:
                self.last_error = "invalid_setpoint_value"
                LOG.exception("[%s] Invalid setpoint value: %s", self.client_id, data.get("value"))
        elif cmd == "clear_setpoint":
            self.state["setpoint"] = None
            LOG.info("[%s] Cleared setpoint", self.client_id)
            ack = {"deviceId": self.client_id, "type": "temperature_setpoint", "value": None}
            self.publish_event(ack)
        else:
            LOG.info("[%s] Unknown temperature command: %s", self.client_id, cmd)
