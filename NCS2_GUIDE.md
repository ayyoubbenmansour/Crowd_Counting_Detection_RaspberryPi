# ⚡ Accelerating with Intel NCS2 (Neural Compute Stick 2)

This guide explains how to use the Intel Neural Compute Stick 2 (NCS2) to accelerate object detection on your Raspberry Pi.

## 1. Prerequisites
- Intel NCS2 USB Stick plugged into a USB port (preferably USB 3.0/Blue port on Pi 4).
- The project setup script (`setup_rpi.sh`) must be completed first.

## 2. Export the Model
The YOLO model must be converted to OpenVINO format (FP16 is required for NCS2).

Run this command on your Raspberry Pi (or your PC and transfer the files):

```bash
yolo export model=yolo11n.pt format=openvino half=True
```
*`half=True` enables FP16 precision, which is **mandatory** for NCS2.*

This will create a directory named `yolo11n_openvino_model/`.

## 3. Configuring the Application
To usage the NCS2, you simply need to point the application to the exported model directory. The Ultralytics library automatically detects the OpenVINO format and attempts to use available hardware.

To explicitly force usage of the NCS2 (Myriad X VPU), you can use the command line:

```bash
python3 crowd_counting_rpi.py --model yolo11n_openvino_model/ --interactive
```

## 4. Troubleshooting
If the stick is not detected:
1.  **Rules**: Ensure udev rules are installed (the setup script should handle this via `openvino-dev` or manual step if needed).
    - If you see "Device not found" errors, run:
      ```bash
      sudo usermod -a -G users "$(whoami)"
      # You might need to install OpenVINO specific rules if not present
      ```
2.  **Power**: Monitor for under-voltage warnings. The NCS2 draws significant power.

## 5. Performance Note
The first run might take a minute to compile the network for the VPU (JIT compilation). Subsequent runs will be faster.
