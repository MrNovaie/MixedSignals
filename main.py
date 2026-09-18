'''Overview

This script uses MediaPipe to detect hand landmarks in real-time from a webcam feed. It draws the detected landmarks and connections on the video frames, determines the position of each fingertip relative to a reference line, and identifies which fingers are extended. The script also aggregates results over multiple frames to provide a more stable output of detected finger configurations.

Use the 'q' key to exit the application.

Applications:
- Real-time hand gesture recognition
- Finger counting
- Human-computer interaction
- Sign language recognition
- Robotics control

Time taken to complete: 2 hours
Project difficulty: Intermediate
Future improvements:
- Implement a more sophisticated method for determining finger extension, possibly using angles between joints.
- Add support for recognizing more complex hand gestures beyond simple finger counting.
- Optimize performance for lower-end hardware by reducing the number of frames processed or using a more efficient model
'''

#Imports
import cv2
import mediapipe as mp
import time
import math
from collections import Counter
from typing import Optional

# Standard MediaPipe hand connections (pairs of landmark indices), hardcoded
# so drawing doesn't depend on mp.solutions existing in your installed version.
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),          # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),          # Index finger
    (5, 9), (9, 10), (10, 11), (11, 12),     # Middle finger
    (9, 13), (13, 14), (14, 15), (15, 16),   # Ring finger
    (13, 17), (17, 18), (18, 19), (19, 20),  # Pinky
    (0, 17),                                  # Palm base
]

# Initialise hand detection and drawing modules
BaseOptions = mp.tasks.BaseOptions(model_asset_path="hand_landmarker.task")
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

# Shared state: holds the most recent detection result, updated by the async callback
latest_result = None

def result_callback(result, output_image, timestamp_ms):
    """Called automatically by MediaPipe whenever a detection finishes."""
    global latest_result
    latest_result = result

    if result.handedness:
        for hand_categories in result.handedness:
            for category in hand_categories:
                print(f"Handedness: {category.category_name}, Score: {category.score:.2f}")


def draw_landmarks(img, result):
    """Draw hand landmarks + connections onto img, using the latest available result.

    Pure OpenCV implementation — does not touch mp.solutions, so it works
    regardless of whether your installed mediapipe version still ships it.
    """
    if result is None or not result.hand_landmarks:
        return

    h, w = img.shape[:2]

    for hand_landmarks in result.hand_landmarks:
        # Convert normalized (0-1) coordinates to pixel coordinates
        points = [(int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks]

        # Draw connections (skeleton lines) first, so dots sit on top
        for start_idx, end_idx in HAND_CONNECTIONS:
            if start_idx < len(points) and end_idx < len(points):
                cv2.line(img, points[start_idx], points[end_idx], (0, 255, 0), 2)
            
        # Draw landmark points
        for point in points:
            cv2.circle(img, point, 4, (0, 0, 255), -1)

    # Draw a horizontal reference line between the base of the index and middle fingers
    if len(points) > 19:
        x1, y1 = points[5]  # Base of index finger
        x2, y2 = points[9] # Base of middle finger
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx*dx + dy*dy)
        if length == 0:
            return None
        ux = dx / length
        uy = dy / length
        extension_length = 200  # Length of the extension line
        start_point = (int(x1 - extension_length * ux), int(y1 - extension_length * uy))
        end_point = (int(x2 + extension_length * ux), int(y2 + extension_length * uy))
        cv2.line(img, start_point, end_point, (255, 0, 0), 2) #Horizontal reference line between index and middle finger bases
        x3, y3 = points[0]  # Base of thumb
        dx2 = x3 - x1
        dy2 = y3 - y1

    return points, x1, y1, dx, dy, dx2, dy2

def get_finger_coordinates(img, points, x1, y1, dx, dy, dx2, dy2):
        # Draw finger labels
        fingers = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky'] #Labels for each finger

        fingertip_coords = {
            fingers[i]: None for i in range(5)
        }

        for i in range(5): 
            finger_points = points[i*4+1:(i+1)*4+1] #Get the 4 landmarks for each finger (excluding the base)

            # Calculate the position of the fingertip relative to the reference line

            for j, point in enumerate(finger_points):
                if j == 3:  # Only label the fingertip
                    tb_side = dx * (point[1] - y1) - dy * (point[0] - x1)
                    lr_side = dx2 * (point[1] - y1) - dy2 * (point[0] - x1)
                    #We define vertical direction as 0 for top, 1 for bottom. Horizontal, 0 for left, 1 for right.
                    if tb_side > 0:
                        vertical_direction = 1 #Bottom
                    else:
                        vertical_direction = 0 #Top
                    if lr_side > 0:
                        horizontal_direction = 0 #Left
                    else:
                        horizontal_direction = 1 #Right
                
                    fingertip_coords[fingers[i]] = (vertical_direction, horizontal_direction)
                    cv2.putText(img, f"{fingers[i]}", point, cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        print("Fingertip coordinates and directions:", fingertip_coords)
        return fingers, fingertip_coords

def is_finger_extended(fingers, fingertip_coords):
    """Determine if each finger is extended based on its position relative to the reference line."""
    extended_status = {}
    for finger in fingers:
        vertical_direction, horizontal_direction = fingertip_coords[finger]
        if finger == 'Thumb':
            # For the thumb, we consider it extended if it's to the left of the reference line (horizontal_direction == 0)
            extended_status[finger] = 1 if horizontal_direction == 0 else 0
        elif finger == 'Index':
            # For the index finger, we consider it extended if it's above the reference line (vertical_direction == 0)
            extended_status[finger] = 1 if vertical_direction == 0 else 0
        else:
            # A non-thumb and non-index finger is considered extended if it is above the reference line (vertical_direction == 0) or if to the left of the reference line (horizontal_direction == 0)
            extended_status[finger] = 1 if vertical_direction == 0 or horizontal_direction == 0 else 0
    return extended_status

def finger_to_number(fingers, extended_status):
    """Convert the extended status of fingers to a number based on a predefined mapping."""
    # Define a mapping from finger extended status to numbers
    finger_number_mapping = {
        (0, 0, 0, 0, 0): 0,
        (0, 1, 0, 0, 0): 1,
        (0, 1, 1, 0, 0): 2,
        (0, 1, 1, 1, 0): 3,
        (0, 1, 1, 1, 1): 4,
        (1, 1, 1, 1, 1): 5,
        (1, 0, 0, 0, 1): 6,
        (1, 1, 0, 0, 0): 7,
        (1, 1, 1, 0, 0): 8,
    }

    # Create a tuple of the extended status in the order of fingers
    status_tuple = (
        extended_status[fingers[0]],
        extended_status[fingers[1]],
        extended_status[fingers[2]],
        extended_status[fingers[3]],
        extended_status[fingers[4]])

    # Return the corresponding number or None if not found
    return finger_number_mapping.get(status_tuple)

class QuickBatchAggregator:
    """Aggregates results from multiple frames to provide a more stable output."""

    def __init__(self, batch_size: int = 10):
        self.batch_size = batch_size
        self.results: list[Optional[int]] = []

    def get_aggregated_result(self) -> Optional[int]:
        """Return the most common result in the current batch."""
        if not self.results:
            return None
        counts = Counter(self.results)
        most_common, _ = counts.most_common(1)[0]
        return most_common

    def add_result(self, result: Optional[int]) -> Optional[int]:
        """Add a new result (1-8 or None) to the batch.
        Returns the most common result in the current window."""
        self.results.append(result)
        if len(self.results) > self.batch_size:
            self.results.pop(0)  # Trim to window size first
        return self.get_aggregated_result()  # Then aggregate over the trimmed window



options = HandLandmarkerOptions(
    base_options=BaseOptions,
    running_mode=VisionRunningMode.LIVE_STREAM,
    num_hands=1, # Maximum number of hands to detect, set to 1 for single hand detection
    min_hand_detection_confidence=0.75,
    min_tracking_confidence=0.75,
    result_callback=result_callback
)

def main():
    aggregator = QuickBatchAggregator(batch_size=10)  # Create an instance of the aggregator
    with HandLandmarker.create_from_options(options) as landmarker:
        capture = cv2.VideoCapture(0)  # Camera at 0 index, multiple cameras have multiple indexes
        capture.set(3, 1280)  # 3 is the width property, 1280 pixels wide
        capture.set(4, 720)   # 4 is the height property, 720 pixels tall

        while capture.isOpened():  # Check if camera is open
            attempt = 0  # Initialise attempt counter
            success, img = capture.read()  # Read image from camera
            while not success and attempt < 5:
                time.sleep(0.02)  # Wait for 20 milliseconds before retrying
                success, img = capture.read()  # Try to read image again
                attempt += 1
            if not success:
                print("Failed to read from camera after 5 attempts.")
                break

            img = cv2.flip(img, 1)  # Flip image horizontally for easy reading from screen

            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert image to RGB format
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            timestamp_ms = int(time.time() * 1000)
            landmarker.detect_async(mp_image, timestamp_ms)  # Kick off async detection

            result_data = draw_landmarks(img, latest_result)  # Draw whatever the most recent result is
            if latest_result and latest_result.hand_landmarks:
                points, x1, y1, dx, dy, dx2, dy2 = result_data  # Unpack the returned values from draw_landmarks
                fingers, fingertip_coords = get_finger_coordinates(img, points, x1, y1, dx, dy, dx2, dy2)  # Get fingertip coordinates and directions
                extended_status = is_finger_extended(fingers, fingertip_coords)
                number = finger_to_number(fingers, extended_status)
                result = aggregator.add_result(number)  # Add the current number to the aggregator and get the most common result
                if result is not None:
                    print(f"Aggregated number: {result}")  # Print aggregated number to console

            cv2.imshow("Image", img)  # Display image (with landmarks) in window

            if cv2.waitKey(1) & 0xFF == ord('q'):  # 'q' key to exit
                break

        capture.release()  # Release camera resource
        cv2.destroyAllWindows()  # Close all OpenCV windows

if __name__ == "__main__":
    main()