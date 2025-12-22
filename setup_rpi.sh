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
pip3 install -r requirements.txt
pip3 install openvino


# Service Installation
echo "⚙️ Installing Systemd Service..."
# Check if service file exists in current directory
if [ -f "crowd_counting.service" ]; then
    sudo cp crowd_counting.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable crowd_counting.service
    echo "✅ Service installed and enabled!"
else
    echo "⚠️ Service file not found! Skipping service installation."
fi

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

echo -n "Flask: "
python3 -c "import flask; print(flask.__version__)" 2>/dev/null && echo "✓ Installed" || echo "✗ Failed"

echo -n "Picamera2: "
python3 -c "from picamera2 import Picamera2; print('✓ Installed')" 2>/dev/null || echo "⚠️  Not available (will use OpenCV)"

echo ""
echo "=================================="
echo "🎉 Setup Complete!"
echo "=================================="
echo ""
echo "To starting the service manually :"
echo "  sudo systemctl start crowd_counting.service"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u crowd_counting.service -f"
echo ""
