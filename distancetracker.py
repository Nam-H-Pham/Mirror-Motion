from posedetector import PoseDetector
from dataclasses import dataclass

@dataclass
class size_pair:
    # Size pair for the user, representing their size relative to the frame at both the start and end of the hallway/room
    start_size: float | None
    end_size: float | None

class DistanceTracker:
    def __init__(self):
        self.start_size_pair = size_pair(start_size=None, end_size=None) # Start of the hallway/room
        self.end_size_pair = size_pair(start_size=None, end_size=None) # End of the hallway/room

        self.current_size_pair = size_pair(start_size=None, end_size=None) # Current size pair for the user, updated in real-time as they move through the hallway/room


    def set_start_size_pair(self, start_pose: PoseDetector, end_pose: PoseDetector) -> bool:
        start_size = self.calculate_user_size_relative_to_frame(start_pose)
        end_size = self.calculate_user_size_relative_to_frame(end_pose)

        # Fail if we cannot calculate the size for either the start or end pose (e.g., if key landmarks are not visible)
        if start_size is None or end_size is None:
            return False
        
        self.start_size_pair = size_pair(
            start_size=start_size,
            end_size=end_size
        )

        return True
    
    def set_end_size_pair(self, start_pose: PoseDetector, end_pose: PoseDetector) -> bool:
        start_size = self.calculate_user_size_relative_to_frame(start_pose)
        end_size = self.calculate_user_size_relative_to_frame(end_pose)

        # Fail if we cannot calculate the size for either the start or end pose (e.g., if key landmarks are not visible)
        if start_size is None or end_size is None:
            return False
        
        self.end_size_pair = size_pair(
            start_size=start_size,
            end_size=end_size
        )

        return True
    
    def update_current_size_pair(self, start_pose: PoseDetector, end_pose: PoseDetector) -> bool:
        start_size = self.calculate_user_size_relative_to_frame(start_pose)
        end_size = self.calculate_user_size_relative_to_frame(end_pose)

        # Fail if we cannot calculate the size for either the start or end pose (e.g., if key landmarks are not visible)
        if start_size is None or end_size is None:
            return False
        
        self.current_size_pair = size_pair(
            start_size=start_size,
            end_size=end_size
        )

        return True

    def calculate_user_size_relative_to_frame(self, pose: PoseDetector) -> dict:
        results = pose.get_last_results()
        if not results or not results.pose_landmarks:
            return None

        landmarks = results.pose_landmarks.landmark

        # Calculate size by the percentage of the frame occupied by the person's height (using landmarks like nose and feet)
        nose = landmarks[0]  # Nose landmark
        left_foot = landmarks[27]  # Left foot landmark
        right_foot = landmarks[28]  # Right foot landmark

        # If any of the key landmarks are not visible, we cannot calculate size accurately
        if nose.visibility < 0.5 or (left_foot.visibility < 0.5 and right_foot.visibility < 0.5):
            return None
        
        # Calculate the height of the person in the frame
        person_height = min(left_foot.y, right_foot.y) - nose.y # in pixels
        frame_ratio = person_height / 1.0  # Assuming frame height is normalized to 1.0

        return frame_ratio  # normalized ratio of person height to frame height

    
    def estimate_progress(self) -> float | None:
        # Estimate the user's progress through the hallway/room based on their current size relative to the start and end size pairs
        if self.start_size_pair.start_size is None or self.start_size_pair.end_size is None:
            return None  # Cannot estimate progress without valid start size pair
        
        if self.end_size_pair.start_size is None or self.end_size_pair.end_size is None:
            return None  # Cannot estimate progress without valid end size pair
        
        if self.current_size_pair.start_size is None or self.current_size_pair.end_size is None:
            return None  # Cannot estimate progress without valid current size pair

        # Calculate progress as a percentage based on the current size relative to the start and end sizes
        start_progress = (self.current_size_pair.start_size - self.start_size_pair.start_size) / (self.end_size_pair.start_size - self.start_size_pair.start_size)
        end_progress = (self.current_size_pair.end_size - self.start_size_pair.end_size) / (self.end_size_pair.end_size - self.start_size_pair.end_size)

        # Average the progress from both cameras for a more robust estimate
        overall_progress = (start_progress + end_progress) / 2

        return overall_progress