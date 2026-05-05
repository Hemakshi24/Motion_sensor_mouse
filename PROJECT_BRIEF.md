# VisionMouse Project Brief

## Problem

Computer control usually assumes a person can use a physical mouse, touchpad, or touchscreen. That is not always true for people with temporary injuries, mobility constraints, sterile work environments, public kiosks, or classroom robotics demos.

## Solution

VisionMouse uses a normal webcam as a motion sensor. A user moves a hand or object in front of the camera, and the Python app converts the strongest detected motion into mouse movement.

## Core Features

- Webcam motion detection with OpenCV.
- Mouse control with PyAutoGUI.
- Relative and absolute movement modes.
- Optional click detection for large motion.
- Presenter hotkeys for pause, recalibration, and click toggle.
- Camera scanner for easier setup on hackathon laptops.

## Tech Stack

- Python
- OpenCV
- NumPy
- PyAutoGUI

## Why It Is Useful

- No special hardware required.
- Works as a quick accessibility prototype.
- Demonstrates computer vision and human-computer interaction clearly.
- Easy to extend with gestures, dwell clicking, hand tracking, or custom UI modes.

## Future Improvements

- Add hand landmark tracking with MediaPipe.
- Add dwell-to-click for accessibility use cases.
- Add gesture commands for scroll, drag, and right click.
- Add calibration zones for different users and camera positions.
- Package as a desktop app with a setup screen.
