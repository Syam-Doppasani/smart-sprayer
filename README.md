
# 🌱 Smart Sprayer – AI-Powered Precision Agriculture System

An intelligent plant detection and automated spraying system that combines computer vision, deep learning, and ESP32-based hardware control to make agricultural spraying more precise and efficient.

Smart Sprayer uses a custom-trained YOLOv8 model to identify plants through a live camera feed. When a plant is detected, the system generates a spraying trigger that can communicate with the hardware controller, enabling automated, detection-based spraying instead of continuous manual operation.

## 🚀 Project Overview

Traditional agricultural spraying often involves applying chemicals uniformly across an entire field, regardless of where plants are located.

Smart Sprayer explores a more targeted approach by integrating AI-based visual detection with an embedded control system.

The system consists of two major components:

- **AI Detection System:** Processes live camera frames using a trained YOLOv8 model to identify plants.
- **Embedded Control System:** Uses an ESP32 microcontroller to manage the sprayer hardware, Wi-Fi communication, and real-time telemetry.

The goal is to build a precision agriculture solution that can reduce unnecessary spraying, improve resource utilization, and support smarter farming practices.

## ✨ Key Features

- **Real-Time Plant Detection:** Detects plants from an IP camera feed using a custom-trained YOLOv8 model.
- **Custom AI Model:** Supports a single-class plant detection model trained using agricultural image data.
- **GPU Acceleration:** Supports NVIDIA CUDA-enabled GPUs for faster inference, with CPU fallback.
- **Automated Spray Triggering:** Generates a spray trigger when a plant is detected.
- **ESP32 Integration:** Supports communication between the AI processing system and the hardware controller.
- **Wi-Fi Connectivity:** Enables wireless communication and hardware status monitoring.
- **Spray Duration Control:** ESP32 provides timed spraying with automatic shutdown.
- **Live Monitoring:** Displays detection results, confidence scores, and system status.
- **Dataset Preparation:** Includes scripts for preprocessing, organizing, and splitting training data.

## 🧠 Technology Stack

| Component | Technology |
|---|---|
| Object Detection | YOLOv8 |
| AI Framework | Ultralytics |
| Programming Language | Python |
| Computer Vision | OpenCV |
| Deep Learning | PyTorch |
| GPU Acceleration | NVIDIA CUDA |
| Microcontroller | ESP32 |
| Embedded Programming | Arduino (C++) |
| Communication | Wi-Fi, HTTP, UDP |
| Dataset Format | YOLO |

## 🏗️ System Architecture

```text
                CAMERA / IP CAMERA
                       |
                       v
              LIVE VIDEO STREAM
                       |
                       v
             PYTHON AI PROCESSING
                       |
                       v
                YOLOv8 MODEL
                       |
                       v
                PLANT DETECTION
                       |
                       v
               SPRAY TRIGGER
                       |
                       v
              HARDWARE CONTROLLER
                       |
                       v
                    ESP32
                       |
                       v
                RELAY / MOSFET
                       |
                       v
                 SPRAYER MOTOR
                       |
                       v
               TARGETED SPRAYING
```

The ESP32 also exposes HTTP endpoints for spray control and status monitoring, while sending periodic telemetry to a configured PC over UDP.

## 📂 Repository Structure

```text
smart-sprayer/
│
├── esp32/
│   └── esp32_sprayer.ino
│
├── scripts/
│   ├── detect.py
│   ├── preprocess.py
│   ├── split_data.py
│   ├── train.py
│   └── utils.py
│
├── README.md
│
├── data/                 # Dataset files (local)
│
└── runs/                 # Model training outputs (local)
```

### Script Description

**`scripts/detect.py`**
- Loads the trained YOLOv8 model.
- Captures frames from an IP camera.
- Detects plants and filters predictions using confidence and bounding-box thresholds.
- Generates spray triggers with a cooldown mechanism.
- Displays real-time detection results.

**`scripts/train.py`**
- Initializes a YOLOv8 small model.
- Trains the model using the prepared agricultural dataset.
- Applies data augmentation to improve model generalization.
- Saves the trained model weights.

**`scripts/preprocess.py`**
- Converts dataset labels into a single plant class.
- Prepares annotations for the detection model.

**`scripts/split_data.py`**
- Organizes image-label pairs into training and validation sets.
- Generates the YOLO dataset configuration file.

**`esp32/esp32_sprayer.ino`**
- Connects the ESP32 to Wi-Fi.
- Controls the sprayer output.
- Provides HTTP endpoints for spray activation, stopping, and status monitoring.
- Sends periodic UDP telemetry containing spraying status and Wi-Fi signal information.
- Automatically stops spraying after the requested duration.

## ⚙️ Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Syam-Doppasani/smart-sprayer.git

cd smart-sprayer
```

### 2. Create a Python Environment

```bash
python -m venv venv
```

Activate the environment:

**Windows**
```bash
venv\Scripts\activate
```

**Linux / macOS**
```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install ultralytics opencv-python torch torchvision pyserial
```

Note: PyTorch should be installed with a compatible CUDA build to enable NVIDIA GPU acceleration.

### 4. Prepare the Dataset

Organize the dataset in the expected directory structure and run:

```bash
python scripts/split_data.py
```

For datasets requiring single-class label conversion:

```bash
python scripts/preprocess.py
```

### 5. Train the Detection Model

```bash
python scripts/train.py
```

The training configuration currently uses YOLOv8s with 80 epochs, 640-pixel image size, and GPU device 0.

### 6. Configure the Detection System

Before starting detection, update the following settings in `scripts/detect.py`:

- `CAMERA_URL`: IP camera stream address.
- `MODEL_PATH`: Location of the trained model weights.
- `CONF_THRESHOLD`: Minimum detection confidence.
- `SERIAL_PORT`: Serial communication port, when using the serial integration.

Set the appropriate communication configuration for your hardware setup.

### 7. Run Plant Detection

```bash
python scripts/detect.py
```

The application displays the live camera feed with detection boxes, confidence scores, and system status.

Press `ESC` to exit.

## 🔌 ESP32 Configuration

1. Open `esp32/esp32_sprayer.ino` in Arduino IDE.
2. Select the appropriate ESP32 board and port.
3. Configure the Wi-Fi credentials.
4. Set the PC receiver IP and UDP port.
5. Configure the sprayer output pin and relay polarity.
6. Upload the firmware to the ESP32.

### Available HTTP Endpoints

| Endpoint | Method | Function |
|---|---|---|
| `/status` | GET | Returns ESP32 connectivity and sprayer status |
| `/spray?ms=1000` | POST | Activates spraying for the requested duration |
| `/stop` | POST | Immediately stops spraying |

The firmware limits the requested spray duration to a maximum of 5 seconds and automatically switches off the output when the timer expires.

## 🌾 Potential Applications

- Precision agriculture
- Automated crop monitoring
- Targeted agricultural spraying
- Smart farming systems
- AI-assisted agricultural robotics
- Resource-efficient crop management

## 🔮 Future Improvements

- Weed-versus-crop classification for selective spraying.
- Integration with wheel encoders for synchronized spraying on a moving robot.
- Improved spray timing based on camera-to-nozzle distance and vehicle movement.
- Real-time monitoring dashboard.
- Field coverage and spraying analytics.
- Integration with GPS for location-based agricultural operations.
- Edge AI deployment for independent onboard inference.
- Improved hardware communication and fault handling.

## ⚠️ Current Implementation Notes

- The detection pipeline currently expects an IP camera stream.
- A trained model file (`best.pt`) must be available at the configured model path.
- Dataset files and training outputs are maintained locally and are not included in the repository.
- The current detection script uses a serial-trigger configuration, while the ESP32 firmware implements HTTP spray-control endpoints and UDP telemetry. An integration layer is required to connect these communication paths.
- Hardware operation should be tested with appropriate electrical protection and a safe test setup before connecting the pump or spraying mechanism.

## 👨‍💻 Author

**Syam Doppasani**

AI & Systems Engineer | Robotics | Computer Vision | Intelligent Automation

- GitHub: [Syam-Doppasani](https://github.com/Syam-Doppasani)
- LinkedIn: [Syam Doppasani](https://www.linkedin.com/in/syam-doppasani-engineer)

---

**Building intelligent systems for smarter and more sustainable agriculture.** 🌱
