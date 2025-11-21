# simulators/motion_sensor.py
import time
import datetime
import random
import logging
from typing import Optional

from simulator.base_device import BaseDevice

LOG = logging.getLogger("motion_sensor")
LOG.setLevel(logging.INFO)


class MotionSensor(BaseDevice):
    """
    Motion sensor simulator.

    - interval: default publish interval in seconds (5s)
    - day_prob: motion probability during day hours (0-1)
    - night_prob: motion probability during night hours (0-1)
    - deterministic seed: optional to make outputs reproducible for tests
    """

    def __init__(
        self,
        *args,
        interval: float = 5.0,
        day_prob: float = 0.02,
        night_prob: float = 0.10,
        seed: Optional[int] = None,
        day_start: int = 7,
        night_start: int = 22,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.interval = float(interval)
        self.day_prob = float(day_prob)
        self.night_prob = float(night_prob)
        self.day_start = int(day_start)  # hour when day begins
        self.night_start = int(night_start)  # hour when night begins
        self.random = random.Random(seed) if seed is not None else random.Random()
        # initial state
        self.state = {"motion": False}

    def _is_night(self, when_ts: float) -> bool:
        """Return True if local hour is in night window."""
        dt = datetime.datetime.fromtimestamp(when_ts)
        hour = dt.hour
        # night is night_start .. 23 + 0 .. (day_start-1)
        if self.night_start <= hour or hour < self.day_start:
            return True
        return False

    def _choose_motion(self) -> bool:
        now = time.time()
        if self._is_night(now):
            prob = self.night_prob
        else:
            prob = self.day_prob
        return self.random.random() < prob

    def _run_loop(self):
        """Main loop: pick motion with configured probabilities and publish event every interval."""
        LOG.info("[%s] MotionSensor loop started (interval=%ss)", self.client_id, self.interval)
        while not self._stop_event.is_set():
            try:
                motion = self._choose_motion()
                self.state["motion"] = bool(motion)
                payload = {"deviceId": self.client_id, "type": "motion", "motion": bool(motion)}
                self.publish_event(payload)
            except Exception as e:
                self.last_error = str(e)
                LOG.exception("[%s] Error in motion loop: %s", self.client_id, e)
            # wait interval but wake early if stop requested
            for _ in range(int(max(1, self.interval * 10))):
                if self._stop_event.is_set():
                    break
                time.sleep(self.interval / 10.0)
        LOG.info("[%s] MotionSensor loop exiting", self.client_id)
