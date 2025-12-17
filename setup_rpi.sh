#!/bin/bash
# Raspberry Pi Setup Script for Hallway Monitor

echo "=================================="
echo "🍓 Raspberry Pi Hallway Monitor"
echo "   Installation Script"
echo "=================================="
echo ""

# Update system
echo "📦 Updating system packages..."
sudo apt update

# Install system dependencies
echo "📦 Installing system dependencies..."
sudo apt install -y python3-pip python3-opencv libcamera-dev python3-libcamera

# Install picamera2 (for Raspberry Pi Camera)
echo "📷 Installing picamera2..."
sudo apt install -y python3-picamera2

# Install Python packages
echo "🐍 Installing Python packages..."
pip3 install --upgrade pip
pip3 install ultralytics opencv-python-headless numpy

# Verify installations
echo ""
echo "=================================="
echo "✅ Verifying installations..."
echo "=================================="

echo -n "Python: "
python3 --version

echo -n "Ultralytics: "
python3 -c "import ultralytics; print(ultralytics.__version__)" 2>/dev/null && echo "✓ Installed" || echo "✗ Failed"

echo -n "OpenCV: "
python3 -c "import cv2; print(cv2.__version__)" 2>/dev/null && echo "✓ Installed" || echo "✗ Failed"

echo -n "Picamera2: "
python3 -c "from picamera2 import Picamera2; print('✓ Installed')" 2>/dev/null || echo "⚠️  Not available (will use OpenCV)"

echo ""
echo "=================================="
echo "🎉 Setup Complete!"
echo "=================================="
echo ""
echo "To run the monitor:"
echo "  python3 hallway_monitor_rpi.py --interactive"
echo ""
