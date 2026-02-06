import cv2
from dotenv import load_dotenv, dotenv_values
from posedetector import PoseDetector
from distancetracker import DistanceTracker
from enum import Enum

load_dotenv()

# Load video streams from IP cameras
url_start = dotenv_values().get("URL_START")
url_end =  dotenv_values().get("URL_END")
print(f"URL_START: {url_start}, URL_END: {url_end}")

# Initialize 2 video captures for the two cameras (start and end of a hallway/room)
cap_start = cv2.VideoCapture(url_start)
cap_end = cv2.VideoCapture(url_end)

# Initialize PoseDetector for both cameras (Libraries like MediaPipe used for pose estimation)
pd_start = PoseDetector(min_detection_confidence=0.5, min_tracking_confidence=0.5)
pd_end = PoseDetector(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Initialize DistanceTracker once before the loop
distance_tracker = DistanceTracker()

class LapState(Enum):
    NOT_STARTED = 0
    STARTED = 1
    RETURNING = 2

laps = 0
lap_state = LapState.NOT_STARTED

# Main loop to read frames from both cameras, process them, and display the results
while True:

    # boolean indicating if the frame was read successfully, and the frame itself
    ret_start, frame_start = cap_start.read() 
    ret_end, frame_end = cap_end.read()

    # Rotate frames
    if ret_start:
        frame_start = cv2.rotate(frame_start, cv2.ROTATE_90_CLOCKWISE)
    if ret_end:
        frame_end = cv2.rotate(frame_end, cv2.ROTATE_90_CLOCKWISE)

    # Process frames with PoseDetector and display them
    if ret_start:
        pd_start.process(frame_start) # Pose estimation results for the start camera
        frame_start = pd_start.overlay_pose(frame_start) # Overlay pose landmarks on the frame
        cv2.imshow("Camera Start", frame_start)
        
    if ret_end:
        pd_end.process(frame_end)
        frame_end = pd_end.overlay_pose(frame_end)
        cv2.imshow("Camera End", frame_end)

    # Get keyboard input once per iteration
    key = cv2.waitKey(1) & 0xFF

    # Exit loop if ESC key is pressed
    if key == 27:  # ESC
        break

    # Helper function to update distance tracker pairs
    def update_tracker_pair(update_method, pair_name):
        if update_method(pd_start, pd_end):
            print(f"{pair_name} updated successfully.")
        else:
            print(f"Failed to update {pair_name}. Please ensure key landmarks are visible in both cameras.")

    # If S key is pressed, update the start size pair for distance tracking
    if key == ord('s'):
        update_tracker_pair(distance_tracker.set_start_size_pair, "Start size pair")

    # If E key is pressed, update the end size pair for distance tracking
    if key == ord('e'):
        update_tracker_pair(distance_tracker.set_end_size_pair, "End size pair")

    # Update the current size pair for distance tracking in real-time as the user moves through the hallway/room
    distance_tracker.update_current_size_pair(pd_start, pd_end)

    progress = distance_tracker.estimate_progress()
    if progress is not None:
        threshold = 0.14
        
        if lap_state == LapState.NOT_STARTED and progress < threshold:
            lap_state = LapState.STARTED
            print("Lap started!")

        elif lap_state == LapState.STARTED and progress > (1 - threshold):
            lap_state = LapState.RETURNING
            print("Return back to start...")

        elif lap_state == LapState.RETURNING and progress < threshold:
            lap_state = LapState.STARTED
            laps += 1
            print(f"Lap completed! Total laps: {laps}")



cap_start.release()
cap_end.release()
cv2.destroyAllWindows()
