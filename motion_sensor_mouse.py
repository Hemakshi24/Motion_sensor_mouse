"""VisionMouse: webcam motion sensor mouse controller for demos and prototypes."""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import cv2
    import numpy as np
else:
    cv2: Any = None
    np: Any = None

pyautogui: Any = None


CAMERA_BACKENDS = {
    "auto": 0,
    "dshow": 700,
    "msmf": 1400,
}


@dataclass
class MotionPoint:
    x: int
    y: int
    area: float


@dataclass
class AppState:
    paused: bool
    click_enabled: bool
    last_click_time: float = 0.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Control the mouse with webcam motion detection."
    )
    parser.add_argument("--camera", type=int, default=0, help="Camera index to use.")
    parser.add_argument(
        "--backend",
        choices=CAMERA_BACKENDS,
        default="auto",
        help="Camera backend. On Windows, try dshow or msmf if auto fails.",
    )
    parser.add_argument(
        "--list-cameras",
        action="store_true",
        help="Scan camera indexes 0-5 and print which ones can open.",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=28,
        help="Pixel difference threshold for motion detection.",
    )
    parser.add_argument(
        "--min-area",
        type=int,
        default=900,
        help="Minimum moving contour area before the mouse responds.",
    )
    parser.add_argument(
        "--mode",
        choices=["relative", "absolute"],
        default="relative",
        help="relative nudges the pointer; absolute maps motion position to the screen.",
    )
    parser.add_argument(
        "--smoothing",
        type=float,
        default=0.28,
        help="Pointer smoothing from 0.05 to 1.0. Higher is snappier.",
    )
    parser.add_argument(
        "--deadzone",
        type=int,
        default=25,
        help="Ignore small movements near the center of the frame.",
    )
    parser.add_argument(
        "--speed",
        type=float,
        default=1.2,
        help="Mouse movement multiplier.",
    )
    parser.add_argument(
        "--click-area",
        type=int,
        default=6000,
        help="Trigger a click when the motion area is at least this large.",
    )
    parser.add_argument(
        "--click-cooldown",
        type=float,
        default=1.0,
        help="Seconds to wait between automatic clicks.",
    )
    parser.add_argument(
        "--click",
        action="store_true",
        help="Enable automatic clicks when large motion is detected.",
    )
    parser.add_argument(
        "--no-click",
        action="store_true",
        help="Keep automatic clicks disabled. This is the default.",
    )
    parser.add_argument(
        "--no-preview",
        action="store_true",
        help="Run without showing the camera preview window.",
    )
    return parser.parse_args()


def ensure_dependencies() -> bool:
    global cv2, np, pyautogui

    try:
        import cv2 as cv2_module
        import numpy as np_module
        import pyautogui as pyautogui_module
    except ModuleNotFoundError as exc:
        missing_name = exc.name or "a required package"
        print(f"Missing dependency: {missing_name}")
        print("Install everything with:")
        print("  python -m pip install -r requirements.txt")
        return False

    cv2 = cv2_module
    np = np_module
    pyautogui = pyautogui_module
    CAMERA_BACKENDS.update(
        {
            "auto": cv2.CAP_ANY,
            "dshow": cv2.CAP_DSHOW,
            "msmf": cv2.CAP_MSMF,
        }
    )
    return True


def open_camera(camera_index: int, backend_name: str) -> cv2.VideoCapture | None:
    backend = CAMERA_BACKENDS[backend_name]
    camera = cv2.VideoCapture(camera_index, backend)

    if camera.isOpened():
        return camera

    camera.release()
    return None


def open_camera_with_fallbacks(camera_index: int, backend_name: str) -> cv2.VideoCapture | None:
    backend_names = [backend_name]
    if backend_name == "auto":
        backend_names.extend(["dshow", "msmf"])
    else:
        backend_names.append("auto")

    tried: set[str] = set()
    for name in backend_names:
        if name in tried:
            continue
        tried.add(name)
        camera = open_camera(camera_index, name)
        if camera is not None:
            print(f"Opened camera {camera_index} using backend: {name}")
            return camera

    return None


def list_cameras(max_index: int = 5) -> int:
    found = 0
    for camera_index in range(max_index + 1):
        working_backends: list[str] = []
        for backend_name in CAMERA_BACKENDS:
            camera = open_camera(camera_index, backend_name)
            if camera is None:
                continue

            ok, _ = camera.read()
            camera.release()
            if ok:
                working_backends.append(backend_name)

        if working_backends:
            found += 1
            print(f"Camera {camera_index}: works with {', '.join(working_backends)}")
        else:
            print(f"Camera {camera_index}: not available")

    if found == 0:
        print("No working cameras found. Close apps using the webcam and check camera privacy permissions.")

    return 0 if found else 1


def find_motion(
    previous_gray: np.ndarray,
    current_gray: np.ndarray,
    threshold: int,
    min_area: int,
) -> MotionPoint | None:
    diff = cv2.absdiff(previous_gray, current_gray)
    blurred = cv2.GaussianBlur(diff, (7, 7), 0)
    _, mask = cv2.threshold(blurred, threshold, 255, cv2.THRESH_BINARY)
    mask = cv2.dilate(mask, None, iterations=2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    largest = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(largest)
    if area < min_area:
        return None

    moments = cv2.moments(largest)
    if moments["m00"] == 0:
        return None

    x = int(moments["m10"] / moments["m00"])
    y = int(moments["m01"] / moments["m00"])
    return MotionPoint(x=x, y=y, area=area)


def move_mouse_relative(
    point: MotionPoint,
    frame_width: int,
    frame_height: int,
    deadzone: int,
    speed: float,
    smoothing: float,
) -> None:
    center_x = frame_width // 2
    center_y = frame_height // 2
    offset_x = point.x - center_x
    offset_y = point.y - center_y

    if abs(offset_x) < deadzone:
        offset_x = 0
    if abs(offset_y) < deadzone:
        offset_y = 0

    move_x = int(offset_x * speed * smoothing)
    move_y = int(offset_y * speed * smoothing)

    if move_x or move_y:
        pyautogui.moveRel(move_x, move_y, duration=0)


def move_mouse_absolute(
    point: MotionPoint,
    frame_width: int,
    frame_height: int,
    smoothing: float,
) -> None:
    screen_width, screen_height = pyautogui.size()
    target_x = int((point.x / max(frame_width, 1)) * screen_width)
    target_y = int((point.y / max(frame_height, 1)) * screen_height)
    current_x, current_y = pyautogui.position()

    next_x = int(current_x + (target_x - current_x) * smoothing)
    next_y = int(current_y + (target_y - current_y) * smoothing)
    pyautogui.moveTo(next_x, next_y, duration=0)


def make_background_frame(frame: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.GaussianBlur(gray, (21, 21), 0)


def draw_preview(
    frame: np.ndarray,
    point: MotionPoint | None,
    state: AppState,
    mode: str,
) -> None:
    height, width = frame.shape[:2]
    cv2.line(frame, (width // 2 - 20, height // 2), (width // 2 + 20, height // 2), (0, 255, 255), 1)
    cv2.line(frame, (width // 2, height // 2 - 20), (width // 2, height // 2 + 20), (0, 255, 255), 1)

    panel_color = (20, 20, 20)
    cv2.rectangle(frame, (0, 0), (width, 76), panel_color, -1)
    cv2.putText(
        frame,
        "VisionMouse",
        (12, 26),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (0, 220, 255),
        2,
    )
    status = "PAUSED" if state.paused else "LIVE"
    click_status = "click ON" if state.click_enabled else "click OFF"
    cv2.putText(
        frame,
        f"{status} | {mode} | {click_status}",
        (12, 56),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        1,
    )

    if point is not None:
        cv2.circle(frame, (point.x, point.y), 16, (0, 255, 0), 2)
        cv2.putText(
            frame,
            f"motion area: {int(point.area)}",
            (10, 104),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )

    cv2.putText(
        frame,
        "q quit | p pause | b recalibrate | c click toggle",
        (10, height - 15),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        1,
    )
    cv2.imshow("Motion Sensor Mouse - press q to quit", frame)


def handle_preview_key(key: int, state: AppState, frame: np.ndarray) -> tuple[bool, np.ndarray | None]:
    if key == ord("q"):
        return True, None
    if key == ord("p"):
        state.paused = not state.paused
    if key == ord("c"):
        state.click_enabled = not state.click_enabled
    if key == ord("b"):
        return False, make_background_frame(frame)
    return False, None


def main() -> int:
    args = parse_args()

    if not ensure_dependencies():
        return 1

    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0

    if args.list_cameras:
        return list_cameras()

    smoothing = min(max(args.smoothing, 0.05), 1.0)
    camera = open_camera_with_fallbacks(args.camera, args.backend)
    if camera is None:
        print(f"Could not open camera index {args.camera}.")
        print("Try:")
        print("  python motion_sensor_mouse.py --list-cameras")
        print("  python motion_sensor_mouse.py --camera 1 --backend dshow")
        print("Also close Zoom/Teams/Camera apps and check Windows camera privacy permissions.")
        return 1

    ok, previous_frame = camera.read()
    if not ok:
        print("Could not read from the camera.")
        camera.release()
        return 1

    previous_frame = cv2.flip(previous_frame, 1)
    previous_gray = make_background_frame(previous_frame)
    state = AppState(paused=False, click_enabled=args.click and not args.no_click)

    print("VisionMouse is running. Move your hand/object in view.")
    print("Preview controls: q quit, p pause, b recalibrate background, c toggle click.")
    print("Move the pointer to a screen corner for PyAutoGUI failsafe.")

    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                print("Camera frame read failed.")
                break

            frame = cv2.flip(frame, 1)
            gray = make_background_frame(frame)

            point = None
            if not state.paused:
                point = find_motion(previous_gray, gray, args.threshold, args.min_area)
                if point is not None:
                    if args.mode == "absolute":
                        move_mouse_absolute(
                            point,
                            frame_width=frame.shape[1],
                            frame_height=frame.shape[0],
                            smoothing=smoothing,
                        )
                    else:
                        move_mouse_relative(
                            point,
                            frame_width=frame.shape[1],
                            frame_height=frame.shape[0],
                            deadzone=args.deadzone,
                            speed=args.speed,
                            smoothing=smoothing,
                        )

                    now = time.monotonic()
                    should_click = (
                        state.click_enabled
                        and point.area >= args.click_area
                        and now - state.last_click_time >= args.click_cooldown
                    )
                    if should_click:
                        pyautogui.click()
                        state.last_click_time = now

            previous_gray = gray

            if not args.no_preview:
                draw_preview(frame, point, state, args.mode)
                should_quit, new_background = handle_preview_key(cv2.waitKey(1) & 0xFF, state, frame)
                if new_background is not None:
                    previous_gray = new_background
                if should_quit:
                    break

    except pyautogui.FailSafeException:
        print("PyAutoGUI failsafe triggered. Stopping.")
    finally:
        camera.release()
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
