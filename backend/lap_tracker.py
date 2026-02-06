import cv2
from dotenv import load_dotenv, dotenv_values
from posedetector import PoseDetector
from distancetracker import DistanceTracker
from lap_state import LapState
import numpy as np
import threading
from frame_grabber import FrameGrabber

class LapTracker:
    def __init__(self, rotate_frames=True, threshold=0.14):
        load_dotenv()

        url_start = dotenv_values().get("URL_START")
        url_end = dotenv_values().get("URL_END")
        print(f"URL_START: {url_start}, URL_END: {url_end}")

        # threaded grabbers (instead of direct cap.read in the loop)
        self.start_cam = FrameGrabber(url_start, "start").start()
        self.end_cam = FrameGrabber(url_end, "end").start()

        self.pd_start = PoseDetector(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        self.pd_end = PoseDetector(min_detection_confidence=0.5, min_tracking_confidence=0.5)

        self.distance_tracker = DistanceTracker()

        self._state_lock = threading.Lock()
        self.laps = 0
        self.lap_state = LapState.NOT_STARTED
        self.rotate_frames = rotate_frames
        self.threshold = threshold
        self.current_lap_progress = 0.0
        self.hallway_progress = 0.0

    def update_tracker_pair(self, update_method, pair_name):
        if update_method(self.pd_start, self.pd_end):
            print(f"{pair_name} updated successfully.")
        else:
            print(f"Failed to update {pair_name}. Please ensure key landmarks are visible in both cameras.")

    def run(self):
        while True:
            ret_start, frame_start = self.start_cam.read_latest()
            ret_end, frame_end = self.end_cam.read_latest()

            if ret_start and frame_start is not None:
                if self.rotate_frames:
                    frame_start = cv2.rotate(frame_start, cv2.ROTATE_90_CLOCKWISE)
                self.pd_start.process(frame_start)
                out_start = self.pd_start.overlay_pose(np.zeros_like(frame_start))
                cv2.imshow("Camera Start", out_start)

            if ret_end and frame_end is not None:
                if self.rotate_frames:
                    frame_end = cv2.rotate(frame_end, cv2.ROTATE_90_CLOCKWISE)
                self.pd_end.process(frame_end)
                out_end = self.pd_end.overlay_pose(np.zeros_like(frame_end))
                cv2.imshow("Camera End", out_end)

            key = cv2.waitKey(1) & 0xFF
            if key == 27:
                break
            if key == ord('s'):
                self.update_tracker_pair(self.distance_tracker.set_start_size_pair, "Start size pair")
            if key == ord('e'):
                self.update_tracker_pair(self.distance_tracker.set_end_size_pair, "End size pair")

            self.distance_tracker.update_current_size_pair(self.pd_start, self.pd_end)

            progress = self.distance_tracker.estimate_progress()
            if progress is not None:
                with self._state_lock:
                    self.hallway_progress = progress
                    if self.lap_state == LapState.STARTED:
                        self.current_lap_progress = progress / 2
                    elif self.lap_state == LapState.RETURNING:
                        self.current_lap_progress = 0.5 + (1 - progress) / 2

                    if self.lap_state == LapState.NOT_STARTED and progress < self.threshold:
                        self.lap_state = LapState.STARTED
                    elif self.lap_state == LapState.STARTED and progress > (1 - self.threshold):
                        self.lap_state = LapState.RETURNING
                    elif self.lap_state == LapState.RETURNING and progress < self.threshold:
                        self.lap_state = LapState.STARTED
                        self.laps += 1

        self.cleanup()

    def get_snapshot(self):
        with self._state_lock:
            return self.laps, self.hallway_progress, self.current_lap_progress, self.lap_state

    def cleanup(self):
        self.start_cam.release()
        self.end_cam.release()
        cv2.destroyAllWindows()

    # thread-safe getters
    def get_lap_count(self) -> int:
        with self._state_lock:
            return self.laps

    def get_current_lap_progress(self) -> float:
        with self._state_lock:
            return self.current_lap_progress

    def get_hallway_progress(self) -> float:
        with self._state_lock:
            return self.hallway_progress

    def get_lap_state(self) -> LapState:
        with self._state_lock:
            return self.lap_state


if __name__ == "__main__":
    tracker = LapTracker(rotate_frames=True, threshold=0.14)
    tracker.run()

    while True:
        # print(f"Hallway Progress: {hp:.2f}, Current Lap Progress: {clp:.2f}, Laps: {laps}, State: {st}")
        laps, hp, clp, st = tracker.get_snapshot()
        print(f"Hallway Progress: {hp:.2f}, Current Lap Progress: {clp:.2f}, Laps: {laps}, State: {st}")