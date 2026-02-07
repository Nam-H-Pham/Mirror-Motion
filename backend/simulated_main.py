import threading
import time
from enum import Enum

from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware




# --- Simulated LapTracker replacement ----------------------------------------

class LapState(Enum):
    NOT_STARTED = 0
    STARTED = 1       # moving away from start toward the far end
    RETURNING = 2     # coming back toward the start


class SimLapTracker:
    """
    Simulates a person moving back and forth along a hallway.

    hallway_progress: 0.0 .. 1.0
      - 0.0 = start
      - 1.0 = far end

    Lap rules (typical):
      - NOT_STARTED until first movement begins
      - STARTED while moving 0 -> 1
      - RETURNING while moving 1 -> 0
      - lap_count increments when we return to 0 after reaching 1
      - current_lap_progress is a 0..1 progress of the *round trip*:
          0.0 at start (0)
          0.5 at far end (1)
          1.0 back at start (0) then wraps to 0.0 for the next lap
    """

    def __init__(
        self,
        speed: float = 0.25,     # hallway units per second
        tick_hz: float = 30.0,   # simulation updates per second
        start_pos: float = 0.0,
    ):
        self._lock = threading.Lock()
        self._stop = threading.Event()

        self._pos = float(start_pos)     # 0..1
        self._dir = 1                    # +1 forward, -1 backward
        self._speed = float(speed)
        self._dt = 1.0 / float(tick_hz)

        self._lap_count = 0
        self._state = LapState.NOT_STARTED
        self._phase = 0.0                # 0..2 (0->1 forward, 1->2 backward)

        self._thread = None

    # Keep the same lifecycle-ish API as your real tracker
    def run(self) -> None:
        """Blocking loop (like your tracker.run())"""
        self._stop.clear()
        self._state = LapState.STARTED  # begin movement immediately
        last = time.perf_counter()

        while not self._stop.is_set():
            now = time.perf_counter()
            dt = now - last
            last = now

            # avoid huge jump if the process stalls
            if dt > 0.2:
                dt = 0.2

            self._tick(dt)
            time.sleep(self._dt)

    def cleanup(self) -> None:
        self._stop.set()

    # API-compatible getters
    def get_lap_count(self) -> int:
        with self._lock:
            return int(self._lap_count)

    def get_current_lap_progress(self) -> float:
        with self._lock:
            # phase in [0,2] -> progress in [0,1]
            # 0.0 start, 0.5 far end, 1.0 back at start
            p = min(max(self._phase / 2.0, 0.0), 1.0)
            return float(p)

    def get_hallway_progress(self) -> float:
        with self._lock:
            return float(self._pos)

    def get_lap_state(self) -> LapState:
        with self._lock:
            return self._state

    # internal simulation tick
    def _tick(self, dt: float) -> None:
        with self._lock:
            step = self._speed * dt * self._dir
            new_pos = self._pos + step

            # bounce off far end
            if new_pos >= 1.0:
                overflow = new_pos - 1.0
                new_pos = 1.0 - overflow
                self._dir = -1
                self._state = LapState.RETURNING

            # bounce off start
            if new_pos <= 0.0:
                overflow = -new_pos
                new_pos = 0.0 + overflow

                # if we were returning and reached start, that's a completed lap
                if self._state == LapState.RETURNING:
                    self._lap_count += 1
                    self._phase = 0.0  # reset for next lap

                self._dir = 1
                self._state = LapState.STARTED

            self._pos = max(0.0, min(1.0, new_pos))

            # update phase smoothly:
            # forward: phase = pos (0..1)
            # returning: phase = 1 + (1 - pos) (1..2)
            if self._state == LapState.STARTED:
                self._phase = self._pos
            elif self._state == LapState.RETURNING:
                self._phase = 1.0 + (1.0 - self._pos)
            else:
                self._phase = 0.0


# --- FastAPI server ----------------------------------------------------------

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Single shared tracker instance (lives for the whole process)
tracker = SimLapTracker(speed=0.22, tick_hz=30.0)


@app.get("/lap_count")
def get_lap_count() -> dict:
    return {"lap_count": tracker.get_lap_count()}


@app.get("/current_lap_progress")
def get_current_lap_progress() -> dict:
    return {"current_lap_progress": tracker.get_current_lap_progress()}


@app.get("/hallway_progress")
def get_hallway_progress() -> dict:
    return {"hallway_progress": tracker.get_hallway_progress()}


@app.get("/lap_state")
def get_lap_state() -> dict:
    # from LapState enum values: NOT_STARTED, STARTED, RETURNING
    return {"lap_state": tracker.get_lap_state().name}

@app.get("/start_is_calibrated")
def get_start_is_calibrated() -> dict:
    # Simulated tracker is always "calibrated" for both start and end
    return {"start_is_calibrated": True}

@app.get("/end_is_calibrated")
def get_end_is_calibrated() -> dict:
    # Simulated tracker is always "calibrated" for both start and end
    return {"end_is_calibrated": True}


def run_api() -> None:
    # Important: run Uvicorn in a background thread
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False,
        workers=1,
    )
    server = uvicorn.Server(config)
    server.run()


if __name__ == "__main__":
    # Start the API server in the background
    api_thread = threading.Thread(target=run_api, name="Uvicorn", daemon=True)
    api_thread.start()

    # Give the server a moment to start (optional)
    time.sleep(0.2)

    # Run the simulated tracker on the MAIN thread (same structure as your original)
    try:
        tracker.run()
    finally:
        tracker.cleanup()
