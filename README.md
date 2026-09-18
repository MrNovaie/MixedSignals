# Hand Gesture Number Recognition

Real-time hand gesture recognition using MediaPipe's HandLandmarker (Tasks API) and OpenCV. The script detects a hand via webcam, identifies which fingers are extended, maps that configuration to a number (0–8), and smooths the result across frames to reduce flicker.

## Features

- Real-time hand landmark detection and skeleton overlay, drawn with plain OpenCV (no dependency on `mediapipe.solutions`)
- Per-fingertip position classification (above/below and left/right of a dynamic reference line)
- Finger-extension detection and mapping to a number, 0 through 8
- Frame-to-frame result aggregation (`QuickBatchAggregator`) to stabilize output against single-frame misclassifications
- Runs fully offline once the model file is downloaded — no network calls during detection

## Applications

- Real-time hand gesture recognition
- Finger counting
- Human-computer interaction
- Sign language recognition
- Robotics control

## Requirements

- Python 3.9+
- A webcam
- Packages:
  ```bash
  pip install opencv-python mediapipe
  ```

> **Note on MediaPipe versions:** some recent MediaPipe releases have introduced breaking changes — including the removal of `mediapipe.solutions`, and a Windows-specific `ctypes` binding bug (`AttributeError: function 'free' not found`) in 0.10.30. This script's drawing code intentionally avoids `mediapipe.solutions` to sidestep the first issue. If you hit the `free` symbol error on Windows, pin to a known-stable release, e.g.:
> ```bash
> pip install mediapipe==0.10.31
> ```
> Check what's actually available in your environment with `pip index versions mediapipe`.

## Setup

1. **Install dependencies:**
   ```bash
   pip install opencv-python mediapipe
   ```

2. **Download the hand landmark model** and place it in the same directory as the script:
   ```bash
   curl -o hand_landmarker.task https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task
   ```

3. **Run the script:**
   ```bash
   python main.py
   ```

4. Press **`q`** at any time to quit.

## How It Works

1. Each webcam frame is flipped (mirror view), converted to RGB, and sent to MediaPipe's `HandLandmarker` for asynchronous detection.
2. Once landmarks are available, a **reference line** is drawn through the base of the index and middle fingers, extended in both directions.
3. Each fingertip's position is classified relative to that line using a 2D cross product — giving a simple (top/bottom, left/right) direction pair per finger, without needing joint-angle math.
4. Each finger is judged **extended** or **not extended** based on its position relative to the line (index and thumb use a single axis; other fingers use either axis).
5. The five-finger extended/not-extended pattern is looked up in a fixed table to produce a number from 0–8.
6. That number is fed into `QuickBatchAggregator`, which keeps a rolling window of the last N frames (default 10) and returns the most common value in the window — smoothing out momentary misreads.

### Gesture Mapping

| Thumb | Index | Middle | Ring | Pinky | Number |
|:-----:|:-----:|:------:|:----:|:-----:|:------:|
|   0   |   0   |   0    |  0   |   0   |   0    |
|   0   |   1   |   0    |  0   |   0   |   1    |
|   0   |   1   |   1    |  0   |   0   |   2    |
|   0   |   1   |   1    |  1   |   0   |   3    |
|   0   |   1   |   1    |  1   |   1   |   4    |
|   1   |   1   |   1    |  1   |   1   |   5    |
|   1   |   0   |   0    |  0   |   0   |   6    |
|   1   |   1   |   0    |  0   |   0   |   7    |
|   1   |   1   |   1    |  0   |   0   |   8    |

(1 = extended, 0 = not extended). Any other combination returns `None` — no matching gesture.

## Known Limitations

- Single-hand detection only (`num_hands=1`); the reference-line logic assumes one hand's landmarks and would need revisiting to support two hands simultaneously.
- The extension test uses simple position-relative-to-a-line geometry rather than joint angles, so accuracy can degrade at unusual hand orientations or camera angles.
- The `6` gesture (thumb only) is a non-standard convention — most finger-counting schemes reserve `6` for thumb + pinky. Worth knowing if comparing against other implementations.
- Console output (`print` statements for handedness and fingertip coordinates) runs every frame — useful for debugging, noisy for regular use. Consider gating behind a debug flag.

## Future Improvements

- Implement a more sophisticated method for determining finger extension, possibly using angles between joints
- Add support for recognizing more complex hand gestures beyond simple finger counting
- Optimize performance for lower-end hardware by reducing the number of frames processed or using a more efficient model

## Project Info

- **Time taken to complete:** ~4 hours
- **Difficulty:** Intermediate