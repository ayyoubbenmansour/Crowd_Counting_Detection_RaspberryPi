# 🚀 Real-time Crowd Counting Detection System

<div align="center">

**AI-powered bidirectional people counting and occupancy monitoring with YOLO11**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![YOLO11](https://img.shields.io/badge/YOLO-v11-brightgreen.svg)](https://docs.ultralytics.com/)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-Compatible-red.svg)](https://www.raspberrypi.org/)
[![License](https://img.shields.io/badge/License-AGPL--3.0-yellow.svg)](LICENSE)

</div>

---

## 📖 Overview

A production-ready AI system for **real-time people counting** and **occupancy monitoring** using state-of-the-art **YOLO11** object detection. Perfect for hallways, entrances, retail spaces, and smart building management.

**Key Capabilities:**
- 🎯 Real-time person detection with YOLO11
- ↔️ Bidirectional entry/exit counting
- 👥 Live occupancy tracking
- ⚠️ Automatic overcrowding alerts
- 🍓 Optimized for Raspberry Pi deployment
- 📊 Professional dashboard with metrics and visualizations

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **AI Detection** | YOLO11-powered person detection with object tracking |
| **Bidirectional Counting** | Separate tracking for entries and exits |
| **Live Occupancy** | Real-time calculation: `IN count - OUT count` |
| **Smart Alerts** | Visual warnings when occupancy exceeds threshold |
| **Interactive Setup** | Click-based UI for counting line placement |
| **Video Recording** | Save processed footage with overlays |
| **Professional Dashboard** | Rich UI with metrics, status indicators, and trends |
| **Raspberry Pi Ready** | Native camera support via picamera2 + OpenCV fallback |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Camera (Webcam, USB, or Raspberry Pi Camera Module)
- 4GB RAM minimum (8GB recommended for Raspberry Pi)

### Installation

**Standard Setup (Desktop/Laptop):**
```bash
# Clone the repository
git clone https://github.com/ayyoubbenmansour/Realtime-Crowd-Counting-Detection.git
cd Realtime-Crowd-Counting-Detection

# Install dependencies
pip install -r requirements.txt

# Run with interactive setup
python Crowd_Counting_rpi.py --interactive
```

**Raspberry Pi Setup:**
```bash
# Clone and navigate
git clone https://github.com/ayyoubbenmansour/Realtime-Crowd-Counting-Detection.git
cd Realtime-Crowd-Counting-Detection

# Auto-setup script
chmod +x setup_rpi.sh
./setup_rpi.sh

# Start monitoring
python3 Crowd_Counting_rpi.py --interactive
```

---

## 💻 Usage

### Basic Commands

```bash
# Interactive line setup (recommended for first run)
python3 Crowd_Counting_rpi.py --interactive

# Custom resolution
python3 Crowd_Counting_rpi.py --resolution 1280 720

# Save output video
python3 Crowd_Counting_rpi.py --output monitoring.mp4

# Headless mode (no display - perfect for SSH)
python3 Crowd_Counting_rpi.py --output monitoring.mp4 --no-display

# Custom alert threshold
python3 Crowd_Counting_rpi.py --threshold 15
```

### Advanced Examples

```bash
# Full configuration
python3 Crowd_Counting_rpi.py \
    --interactive \
    --resolution 1920 1080 \
    --threshold 20 \
    --output crowd_monitor.mp4

# Predefined counting line (skip interactive setup)
python3 Crowd_Counting_rpi.py \
    --line-start 100 240 \
    --line-end 540 240 \
    --threshold 10

# Force OpenCV mode (for USB cameras)
python3 Crowd_Counting_rpi.py --interactive --use-opencv
```

---

## ⚙️ Command-Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--model` | str | `yolo11n.pt` | Path to YOLO model weights |
| `--output` | str | `None` | Output video file path |
| `--threshold` | int | `10` | Overcrowding alert threshold |
| `--interactive` | flag | `False` | Enable click-based line setup |
| `--line-start` | int int | `None` | Start point coordinates (x y) |
| `--line-end` | int int | `None` | End point coordinates (x y) |
| `--resolution` | int int | `640 480` | Camera resolution (width height) |
| `--use-opencv` | flag | `False` | Force OpenCV instead of picamera2 |
| `--no-display` | flag | `False` | Headless mode (no GUI) |

---

## 🏗️ How It Works

### Detection Pipeline

```
Camera Feed → YOLO11 Detection → Object Tracking → Line Crossing → Occupancy Count → Dashboard
```

### Counting Algorithm

1. **Person Detection**: YOLO11 identifies people in each frame
2. **Object Tracking**: Each person receives a unique tracking ID
3. **Center Point Monitoring**: Track center coordinates across frames
4. **Line Crossing Detection**:
   - **Entry**: Center crosses from above to below → `IN++`
   - **Exit**: Center crosses from below to above → `OUT++`
5. **Occupancy Calculation**: `Current Occupancy = IN - OUT`

### Alert System

```python
if current_occupancy >= threshold:
    status = "WARNING"  # threshold ≤ occupancy < threshold+5
    status = "CRITICAL" # occupancy ≥ threshold+5
    trigger_visual_alert()
```

---

## 📊 Dashboard Components

### Top Panel
- 📌 System title and branding
- ⏱️ Real-time FPS counter
- 🕒 Timestamp

### Metric Cards
1. **📥 ENTERED** - Total entries (green)
2. **📤 EXITED** - Total exits (cyan)
3. **👥 OCCUPANCY** - Current count (color-coded)
4. **⚠️ ALERTS** - Alert count (orange)

### Visual Elements
- 🎯 Counting line with directional arrows
- 🔲 Bounding boxes with tracking IDs
- 🚦 Status indicator (NORMAL/WARNING/CRITICAL)
- ⚠️ Large overcrowding alert overlay

---

## 🍓 Raspberry Pi Guide

### Enable Camera

```bash
# For Raspberry Pi Camera Module
sudo raspi-config
# Navigate to: Interface Options → Camera → Enable
```

### Camera Modes

- **picamera2** (Recommended): Native Raspberry Pi camera library
- **OpenCV**: Universal fallback for USB cameras

### Performance Optimization

```bash
# Lower resolution for better FPS
python3 Crowd_Counting_rpi.py --resolution 640 480

# Headless for SSH sessions
python3 Crowd_Counting_rpi.py --no-display --output log.mp4

# Use nano model (fastest)
python3 Crowd_Counting_rpi.py --model yolo11n.pt
```

### Troubleshooting

**Camera not found:**
```bash
# Check camera status
vcgencmd get_camera
# Should show: supported=1 detected=1

# Test picamera2
python3 -c "from picamera2 import Picamera2; print('OK')"

# List video devices
ls /dev/video*
```

---

## 📁 Project Structure

```
Realtime-Crowd-Counting-Detection/
├── Crowd_Counting_rpi.py      # Main application (502 lines)
├── README.md                   # Documentation
├── requirements.txt            # Python dependencies
├── setup_rpi.sh               # Raspberry Pi setup script
├── yolo11n.pt                 # YOLO11 model weights
└── test_video.mp4             # Sample test video
```

---

## 🔧 Dependencies

**Core Libraries:**
- `ultralytics` - YOLO11 implementation
- `opencv-python` - Computer vision
- `numpy` - Numerical operations
- `torch` - Deep learning backend

**Optional (Raspberry Pi):**
- `picamera2` - Native Pi camera support

Install all dependencies:
```bash
pip install -r requirements.txt
```

---

## 🎨 Customization

### Modify Alert Thresholds

```python
# Via CLI
python3 Crowd_Counting_rpi.py --threshold 20

# Or edit in code (line 326)
alert_threshold = 20
```

### Change UI Colors

Edit color scheme in `Crowd_Counting_rpi.py` (lines 103-112):
```python
self.colors = {
    'primary': (255, 140, 0),   # Deep Sky Blue
    'success': (0, 255, 0),      # Green
    'danger': (0, 0, 255),       # Red
    # ... customize as needed
}
```

### Integration Examples

Extend the system to:
- 📧 Send email alerts on overcrowding
- 🔔 Trigger Slack/Discord notifications
- 💾 Log data to databases (PostgreSQL, MongoDB)
- 📊 Export analytics to CSV/Excel
- 🌐 Stream to IoT platforms (AWS, Azure)

---

## 🔍 Troubleshooting

### Low FPS
- Reduce resolution: `--resolution 640 480`
- Use YOLO11n (smallest model)
- Close background applications
- Ensure adequate lighting

### Permission Denied (Camera)
```bash
# Add user to video group
sudo usermod -a -G video $USER
# Logout and login again
```

### Model Not Found
```bash
# Download YOLO11n manually
wget https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11n.pt
```

---

## 📚 References

- [YOLO11 Documentation](https://docs.ultralytics.com/models/yolo11/)
- [Ultralytics Object Counting Guide](https://docs.ultralytics.com/guides/object-counting/)
- [Picamera2 Manual](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf)
- [Raspberry Pi Camera Setup](https://www.raspberrypi.com/documentation/computers/camera_software.html)

---

## 🤝 Contributing

Contributions welcome! Feel free to:
- 🐛 Report bugs via Issues
- 💡 Suggest features
- 🔧 Submit pull requests
- 📖 Improve documentation

---

## 📄 License

This project uses:
- **Ultralytics YOLO** - AGPL-3.0 License
- **OpenCV** - Apache 2.0 License

---

## 🙏 Acknowledgments

Built with:
- 🧠 **YOLO11** by Ultralytics
- 📷 **OpenCV** for computer vision
- 🍓 **Picamera2** for Raspberry Pi support

---

<div align="center">

**Made with ❤️ for smart building management**

[Report Bug](https://github.com/ayyoubbenmansour/Realtime-Crowd-Counting-Detection/issues) · 
[Request Feature](https://github.com/ayyoubbenmansour/Realtime-Crowd-Counting-Detection/issues)

</div>