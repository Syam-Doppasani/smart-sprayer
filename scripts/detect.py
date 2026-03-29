import cv2
import time
import os
import winsound
import torch
from ultralytics import YOLO

# ===== CONFIG =====
USE_WEBCAM = False  # True = local webcam, False = IP camera
CAMERA_URL = ""  # Change IP to match your phone
CAMERA_INDEX = 0  # webcam index

SERIAL_PORT = "COM3"
BAUD_RATE = 115200
USE_SERIAL = False  # Set True when Arduino is connected

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "..", "runs", "detect", "plant_detector_v2", "weights", "best.pt")

CONF_THRESHOLD = 0.45  # higher threshold — fewer false positives after better training
MIN_BOX_SIZE = 15  # minimum box width/height in pixels to filter noise
COOLDOWN = 3  # seconds between spray triggers
GPU_DEVICE = 0  # use first CUDA GPU when available

# ===== INIT =====
print(f"Loading model from: {MODEL_PATH}")
print(f"Confidence threshold: {CONF_THRESHOLD}")
model = YOLO(MODEL_PATH)
print(f"Model classes: {model.names}")
if torch.cuda.is_available():
    gpu_name = torch.cuda.get_device_name(GPU_DEVICE)
    print(f"CUDA available. Using GPU {GPU_DEVICE}: {gpu_name}")
    INFER_DEVICE = GPU_DEVICE
else:
    print("CUDA not available. Falling back to CPU.")
    INFER_DEVICE = "cpu"

ser = None
if USE_SERIAL:
    try:
        import serial
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE)
        print(f"Serial connected on {SERIAL_PORT}")
    except Exception as e:
        print(f"Serial not available: {e}")

def open_camera():
    if USE_WEBCAM:
        print("ERROR: This script is configured for IP camera only. Set USE_WEBCAM=False.")
        return None

    print(f"Opening IP camera: {CAMERA_URL}")
    cap_ip = cv2.VideoCapture(CAMERA_URL)
    if cap_ip.isOpened():
        return cap_ip
    print("IP camera failed to open.")
    return None


cap = open_camera()
if cap is None:
    print("ERROR: Could not open any camera source.")
    raise SystemExit(1)

print("Camera opened. Press ESC to quit.")

last_spray = 0
frame_count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    frame = cv2.resize(frame, (640, 480))

    results = model(frame, verbose=False, device=INFER_DEVICE)
    frame_count += 1

    detected = False
    det_count = 0

    for r in results:
        for box in r.boxes:
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            label = model.names[cls_id]

            if conf > CONF_THRESHOLD:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                box_w = x2 - x1
                box_h = y2 - y1

                # Skip tiny false-positive boxes
                if box_w < MIN_BOX_SIZE or box_h < MIN_BOX_SIZE:
                    continue

                detected = True
                det_count += 1

                # Dark bounding box (BGR)
                color = (20, 20, 20)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)

                # Draw label background for readability
                text = f"{label} {conf:.0%}"
                (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)
                cv2.rectangle(frame, (x1, y1 - th - 10), (x1 + tw + 4, y1), color, -1)
                cv2.putText(frame, text, (x1 + 2, y1 - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

                print(f"  [{label}] conf={conf:.3f} size={box_w}x{box_h} box=({x1},{y1})-({x2},{y2})")

    # ===== SPRAY LOGIC =====
    # Spray when ANY plant is detected (single class model)
    if detected and (time.time() - last_spray > COOLDOWN):
        print("PLANT DETECTED - SPRAY TRIGGERED!")
        winsound.Beep(1000, 200)  # buzzer: 1000Hz for 200ms
        if ser:
            ser.write(b'S')
        last_spray = time.time()

    # Show status bar on frame
    status = "PLANT DETECTED - SPRAYING" if det_count > 0 else "Scanning..."
    status_color = (0, 255, 0) if det_count > 0 else (100, 100, 100)
    cv2.rectangle(frame, (0, 0), (640, 35), (0, 0, 0), -1)
    cv2.putText(frame, f"Frame: {frame_count} | Plants: {det_count} | Conf: {CONF_THRESHOLD} | {status}",
                (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, status_color, 2)
    cv2.imshow("Smart Sprayer - Plant Detection", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()
if ser:
    ser.close()
print("Done.")
