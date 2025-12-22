# 🚀 Real-time Crowd Counting Detection System

<div align="center">

**AI-powered bidirectional people counting and occupancy monitoring with YOLO11**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![YOLO11](https://img.shields.io/badge/YOLO-v11-brightgreen.svg)](https://docs.ultralytics.com/)
[![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-Compatible-red.svg)](https://www.raspberrypi.org/)
[![Intel NCS2](https://img.shields.io/badge/Intel-NCS2%20Ready-blue.svg)](https://www.intel.com/)
[![License](https://img.shields.io/badge/License-AGPL--3.0-yellow.svg)](LICENSE)

</div>

---

## 📖 Overview

A production-ready AI system for **real-time people counting** and **occupancy monitoring** using state-of-the-art **YOLO11** object detection. Perfect for hallways, entrances, retail spaces, and smart building management.

**Key Capabilities:**
- 🎯 **High-Speed Detection**: Optimized YOLO11n model.
- ⚡ **Intel NCS2 Acceleration**: Full support for OpenVINO FP16 acceleration.
- 👥 **Real-Time Counting**: Accurate "IN" and "OUT" tracking.
- 🍓 **Raspberry Pi Native**: Built for Pi 4/5 with `picamera2` support.
- 📊 **Ultra-Compact UI**: Minimalist dashboard with "OUT" and "NOW" metrics.
- ⚙️ **Auto-Start**: Systemd service for 24/7 autonomous operation.

---

## 🚀 Quick Start

### 1. Installation on Raspberry Pi
We provide a single script to set up everything (Python, OpenCV, OpenVINO, Service).

```bash
# Clone the repository
git clone https://github.com/ayyoubbenmansour/Crowd_Counting_Detection_RaspberryPi.git
cd Crowd_Counting_Detection_RaspberryPi

# Run the auto-setup script
chmod +x setup_rpi.sh
./setup_rpi.sh
```

### 2. Run the Application
You can run it manually or as a background service.

**Manual Start (for testing):**
```bash
python3 app.py
```
*Access the dashboard at `http://<YOUR-PI-IP>:5000`*

**Background Service (Auto-start on boot):**
```bash
sudo systemctl start crowd_counting.service
```

---

## ⚡ Intel NCS2 Acceleration
To get maximum FPS on a Raspberry Pi 4, we recommend using the Intel Neural Compute Stick 2.

**1. Export the Model:**
```bash
yolo export model=yolo11n.pt format=openvino half=True
```

**2. Run with Acceleration:**
```bash
python3 crowd_counting_rpi.py --model yolo11n_openvino_model/ --interactive
```

*See [NCS2_GUIDE.md](NCS2_GUIDE.md) for full details.*

---

## 📊 Dashboard Metrics

The UI is designed to be unobtrusive overlaying the video feed.

| Metric | Description |
|--------|-------------|
| **OUT** | Total number of people who have walked **OUT** of the zone. |
| **NOW** | Current **Occupancy** (people currently inside the zone). |
| **Zone Status** | Color-coded status (Green=OK, Orange=Warn, Red=Critical). |

---

## 💻 Advanced Usage

### Custom Line Setup
Run in interactive mode to click-and-draw your counting zone.
```bash
python3 crowd_counting_rpi.py --interactive
```

### Headless Mode (SSH)
Run without a GUI window, perfect for remote servers.
```bash
python3 crowd_counting_rpi.py --no-display --output debug_session.mp4
```

### Optimize for Speed
Reduce resolution to gain FPS.
```bash
python3 crowd_counting_rpi.py --resolution 640 360
```

---

## 📂 Project Structure

Crowd_Counting_Detection_RaspberryPi/
├── app.py                      # Flask Web Application (Video Streaming)
├── crowd_counting_rpi.py       # Core AI Logic & Processing
├── setup_rpi.sh                # One-click Installation Script
├── crowd_counting.service      # Systemd Auto-start Service
├── DEPLOYMENT.md               # Detailed Pi Deployment Guide
├── NCS2_GUIDE.md               # Intel NCS2 Acceleration Guide
├── TRAINING_GUIDE.md           # Guide to Fine-Tune Model
├── DATASETS.md                 # List of Public Datasets
├── logs.json                   # Local Log Storage (Generated at runtime)
├── templates/                  # Web Interface Templates (layout, index, settings, logs)
├── yolo11n.pt                  # YOLO Model Weights
└── README.md                   # Documentation
```

---

## 🤝 Contributing

Contributions welcome!
- 🐛 Report bugs via Issues
- 💡 Suggest features
- 🔧 Submit pull requests

---

<div align="center">

**© 2025/2026 Real-time Crowd Counting**

</div>