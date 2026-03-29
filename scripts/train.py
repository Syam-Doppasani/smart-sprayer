from ultralytics import YOLO
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "dataset", "data.yaml")

def main():
    model = YOLO("yolov8s.pt")  # small model — better accuracy than nano

    model.train(
        data=DATA_PATH,
        epochs=80,
        imgsz=640,
        batch=16,
        device=0,             # RTX 4060 GPU
        workers=4,
        name="plant_detector_v2",
        patience=15,

        # ===== DATA AUGMENTATION =====
        augment=True,
        hsv_h=0.02,           # hue shift — simulates lighting changes
        hsv_s=0.7,            # saturation variation
        hsv_v=0.4,            # brightness variation
        degrees=15.0,         # random rotation ±15°
        translate=0.1,        # random shift
        scale=0.5,            # random zoom
        fliplr=0.5,           # horizontal flip
        flipud=0.3,           # vertical flip
        mosaic=1.0,           # mosaic augmentation (combines 4 images)
        mixup=0.1,            # mixup augmentation
        copy_paste=0.1,       # copy-paste augmentation
    )

if __name__ == "__main__":
    main()