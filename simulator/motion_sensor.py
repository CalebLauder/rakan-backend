# simulators/motion_sensor.py
import time
import datetime
import random
import logging
from typing import Optional

from base_simulator import BaseSimulator

LOG = logging.getLogger("motion_sensor")
LOG.setLevel(logging.INFO)


class MotionSensor(BaseSimulator):
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
        self.day_start = int(day_start)
        self.night_start = int(night_start)
        self.random = random.Random(seed) if seed is not None else random.Random()
        self.state = {"motion": False}

    def _is_night(self, when_ts: float) -> bool:
        dt = datetime.datetime.fromtimestamp(when_ts)
        hour = dt.hour
        return (self.night_start <= hour) or (hour < self.day_start)

    def _choose_motion(self) -> bool:
        now = time.time()
        prob = self.night_prob if self._is_night(now) else self.day_prob
        return self.random.random() < prob

    def _run_loop(self):
        LOG.info("[%s] MotionSensor loop started (interval=%ss)", self.client_id, self.interval)
        while not self._stop_event.is_set():
            try:
                motion = self._choose_motion()
                self.state["motion"] = bool(motion)
                payload = {
                    "deviceId": self.client_id,
                    "type": "motion",
                    "motion": bool(motion)
                }
                self.publish_event(payload)

            except Exception as e:
                self.last_error = str(e)
                LOG.exception("[%s] Error in motion loop: %s", self.client_id, e)

            # Sleep in small steps so we can stop early cleanly
            for _ in range(int(max(1, self.interval * 10))):
                if self._stop_event.is_set():
                    break
                time.sleep(self.interval / 10.0)

        LOG.info("[%s] MotionSensor loop exiting", self.client_id)
