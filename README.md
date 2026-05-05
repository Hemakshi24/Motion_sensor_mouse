# VisionMouse

A webcam-based motion sensor mouse built in Python for hackathon demos.

VisionMouse turns ordinary camera motion into mouse movement. It is designed for accessibility prototypes, touchless kiosks, classroom demos, and low-cost human-computer interaction experiments.

## What It Does

- Detects the strongest moving object in the camera feed.
- Moves the system mouse from that motion.
- Supports relative movement and absolute screen mapping.
- Includes a live preview with motion marker and status overlay.
- Lets the presenter pause, recalibrate, and toggle clicking during a demo.
- Scans camera indexes and tries Windows-friendly OpenCV backends.

## Install

```powershell
python -m pip install -r requirements.txt
```

## Run

Start safely with clicking disabled:

```powershell
python motion_sensor_mouse.py --no-click
```

Then try absolute mode for a more direct “camera position to screen position” demo:

```powershell
python motion_sensor_mouse.py --mode absolute --no-click
```

Enable click detection only after movement feels stable:

```powershell
python motion_sensor_mouse.py --mode absolute --click
```

Move your hand or another object in front of the camera. The script finds the strongest moving area and moves the mouse based on it.

Move the real mouse pointer to any screen corner to trigger PyAutoGUI's emergency stop.

## Demo Controls

Use these keys while the camera preview is active:

- `q` quits.
- `p` pauses or resumes control.
- `b` recalibrates the current frame.
- `c` toggles automatic clicking.

## Useful Options

```powershell
python motion_sensor_mouse.py --list-cameras
python motion_sensor_mouse.py --camera 1 --backend dshow --no-click
python motion_sensor_mouse.py --camera 0 --backend msmf --no-click
python motion_sensor_mouse.py --mode absolute --no-click
python motion_sensor_mouse.py --mode relative --click
python motion_sensor_mouse.py --speed 0.8 --smoothing 0.2
python motion_sensor_mouse.py --threshold 35 --min-area 1200
python motion_sensor_mouse.py --camera 1
```

- `--list-cameras` scans camera indexes `0` through `5`.
- `--backend dshow` uses DirectShow, which often works better on Windows.
- `--backend msmf` uses Microsoft Media Foundation.
- `--mode relative` nudges the mouse based on movement away from the camera center.
- `--mode absolute` maps camera position to screen position.
- `--click` enables automatic clicking.
- `--no-click` keeps automatic clicking disabled.
- `--speed` changes pointer movement strength.
- `--smoothing` changes how jumpy or responsive the pointer feels.
- `--threshold` makes motion detection more or less sensitive.
- `--min-area` ignores tiny moving objects and camera noise.
- `--camera` selects another webcam if your default camera is not the right one.

## Hackathon Demo Flow

1. Run `python motion_sensor_mouse.py --list-cameras`.
2. Start `python motion_sensor_mouse.py --mode absolute --no-click`.
3. Show the preview detecting a moving hand.
4. Move the pointer around a browser, slide, or drawing app.
5. Press `c` to enable clicking for one simple click demo.
6. Press `p` to pause and explain how the system works.

## If The Camera Does Not Open

Run:

```powershell
python motion_sensor_mouse.py --list-cameras
```

Then use the camera number that works, for example:

```powershell
python motion_sensor_mouse.py --camera 1 --backend dshow --no-click
```

If no cameras are found:

- Close apps that may be using the camera, such as Camera, Zoom, Teams, or OBS.
- Open Windows Settings and allow camera access for desktop apps.
- Try another backend: `--backend dshow` or `--backend msmf`.
- Try another index: `--camera 1`, `--camera 2`, etc.
