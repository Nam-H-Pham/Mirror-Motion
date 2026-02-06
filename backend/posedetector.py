import mediapipe as mp
import cv2

class PoseDetector:
    def __init__(self, min_detection_confidence=0.5, min_tracking_confidence=0.5):
        self.pose = mp.solutions.pose.Pose(
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )

        self.last_results = None

    def process(self, frame: cv2.Mat) -> None:
        frame.flags.writeable = False # Apparently helps performance (https://github.com/google-ai-edge/mediapipe/blob/master/docs/solutions/pose.md)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(frame)
        frame.flags.writeable = True
        self.last_results = results

    def get_last_results(self) -> mp.solutions.pose.PoseLandmark:
        return self.last_results

    def overlay_pose(self, frame: cv2.Mat) -> cv2.Mat:
        mp.solutions.drawing_utils.draw_landmarks(frame, self.last_results.pose_landmarks, mp.solutions.pose.POSE_CONNECTIONS)
        return frame
    
    def right_hand_raised(self) -> bool:
        if not self.last_results or not self.last_results.pose_landmarks:
            return False
        
        landmarks = self.last_results.pose_landmarks.landmark
        # Check if right wrist is above right shoulder
        return landmarks[16].y < landmarks[12].y
    
    def left_hand_raised(self) -> bool:
        if not self.last_results or not self.last_results.pose_landmarks:
            return False
        
        landmarks = self.last_results.pose_landmarks.landmark
        # Check if left wrist is above left shoulder
        return landmarks[15].y < landmarks[11].y
