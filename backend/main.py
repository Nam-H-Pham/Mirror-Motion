from fastapi import FastAPI
from contextlib import asynccontextmanager
from lap_tracker import LapTracker
import threading


@asynccontextmanager
async def lifespan(app: FastAPI):
    tracker = LapTracker(rotate_frames=True, threshold=0.14)

    # If run() blocks, start it in a thread
    thread = threading.Thread(target=tracker.run, daemon=True)
    thread.start()

    app.state.tracker = tracker

    yield  # --- app runs here --- 

    tracker.cleanup()


app = FastAPI(lifespan=lifespan)


def get_tracker() -> LapTracker:
    return app.state.tracker


@app.get("/lap_count")
def get_lap_count() -> dict:
    tracker = get_tracker()
    return {"lap_count": tracker.get_lap_count()}


@app.get("/current_lap_progress")
def get_current_lap_progress() -> dict:
    tracker = get_tracker()
    return {"current_lap_progress": tracker.get_current_lap_progress()}


@app.get("/hallway_progress")
def get_hallway_progress() -> dict:
    tracker = get_tracker()
    return {"hallway_progress": tracker.get_hallway_progress()}


@app.get("/lap_state")
def get_lap_state() -> dict:
    tracker = get_tracker()
    # enum values: NOT_STARTED, STARTED, RETURNING
    return {"lap_state": tracker.get_lap_state().name}
