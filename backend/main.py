import threading
import time

import uvicorn
from fastapi import FastAPI

from lap_tracker import LapTracker

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Single shared tracker instance (lives for the whole process)
tracker = LapTracker(rotate_frames=True, threshold=0.14, display_windows=False)


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
    return {"start_is_calibrated": tracker.get_start_is_calibrated()}

@app.get("/end_is_calibrated")
def get_end_is_calibrated() -> dict:
    return {"end_is_calibrated": tracker.get_end_is_calibrated()}

def run_api() -> None:
    # Important: run Uvicorn in a background thread
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        # If you hot-reload, do it externally (reload=True uses subprocesses and won't work nicely here)
        reload=False,
        # One worker only; multiple workers = multiple processes = tracker wont be shared
        workers=1,
    )
    server = uvicorn.Server(config)
    server.run()


if __name__ == "__main__":
    # Start the API server in the background
    api_thread = threading.Thread(target=run_api, name="Uvicorn", daemon=True)
    api_thread.start()

    # Give the server a moment to start (optional but avoids race during startup logs)
    time.sleep(0.2)

    # Run tracker (with imshow/waitKey) on the MAIN thread (macOS requirement)
    try:
        tracker.run()
    finally:
        tracker.cleanup()
