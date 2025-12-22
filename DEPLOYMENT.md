# 🍓 Raspberry Pi Deployment Guide

This guide will help you deploy the **Realtime Crowd Counting & Detection** system on a Raspberry Pi.

## Prerequisites
- **Hardware**: Raspberry Pi 4 or 5 (recommended 4GB+ RAM).
- **Camera**: Raspberry Pi Camera Module 3 or similar (Picamera2 compatible) OR USB Webcam.
- **OS**: Raspberry Pi OS (64-bit Bookworm or newer recommended).

## Installation

1.  **Transfer Files**: Copy the entire project folder to your Raspberry Pi Desktop.
    ```bash
    /home/pi/Desktop/Realtime-Crowd-Counting-Detection
    ```

2.  **Run Setup Script**:
    Open a terminal in the project folder and run:
    ```bash
    cd /home/pi/Desktop/Realtime-Crowd-Counting-Detection
    chmod +x setup_rpi.sh
    ./setup_rpi.sh
    ```
    This script will:
    - Update system packages.
    - Install dependencies (Python, OpenCV, Picamera2).
    - Install the systemd service.

## Running the Application

### ✅ Automatic Start (Service)
The application is set to start automatically on boot.
- **Start**: `sudo systemctl start crowd_counting.service`
- **Stop**: `sudo systemctl stop crowd_counting.service`
- **Restart**: `sudo systemctl restart crowd_counting.service`
- **Check Status**: `sudo systemctl status crowd_counting.service`
- **View Logs**: `sudo journalctl -u crowd_counting.service -f`

### 🔧 Manual Run
To run the server manually for debugging:
```bash
python3 app.py
```
Access the web dashboard at: `http://<YOUR-PI-IP>:5000`

## Configuration

- **Zone Setup**: Go to `http://<YOUR-PI-IP>:5000/settings` to adjust the counting zone size.
- **Camera Selection**: The system automatically prioritizes the Pi Camera. If not found, it falls back to USB Webcam (index 0).

## Troubleshooting

- **Camera not detected?**
    Ensure camera cable is seated correctly and legacy camera stack is disabled (if using libcamera/picamera2).
- **Performance issues?**
    Use a smaller model (already using `yolo11n.pt`) or reduce resolution in `app.py`.
