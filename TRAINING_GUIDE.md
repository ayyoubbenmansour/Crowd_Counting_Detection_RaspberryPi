# 🎓 Training YOLO11n for Maximum Efficiency

To get the best performance (speed + accuracy) for your specific hallway, you should **fine-tune** the model. Using the default model finds *everything* (cars, dogs, umbrellas), but you only care about **people**.

## 🚀 Strategy: "Transfer Learning"
We will teach the model to ignore everything except humans and focus specifically on the camera angle of your hallway.

### Benefits
1.  **Higher Accuracy:** The model learns your specific lighting and background.
2.  **Faster Post-Processing:** By training for only **1 class** ('person'), the Pi does less math filtering out other objects.

---

## 🛠️ Step-by-Step Guide

### Phase 1: Data Collection (On Raspberry Pi)
Capture images from your actual deployed camera.
1.  Create a folder: `mkdir -p dataset/images`
2.  Run a simple script to save a frame every 5 seconds (or use `crowd_counting_rpi.py` and manually save interesting frames).
3.  **Aim for:** 100-200 images of people walking in your hallway. Varied clothing and lighting helps.

### Phase 2: Annotation (On PC)
Label your images.
1.  Move images to your PC.
2.  Use a tool like [Roboflow](https://roboflow.com/) (easiest, web-based) or [CVAT](https://cvat.ai/).
3.  Draw boxes around every person.
4.  **Export Dataset:** Choose "YOLOv8" format (compatible with YOLO11).

### Phase 3: Training (On Google Colab / PC with GPU)
**⚠️ DO NOT TRAIN ON RASPBERRY PI.** It is too slow. Use a Cloud GPU (free).

1.  Open [Google Colab](https://colab.research.google.com/).
2.  Select Runtime > Change runtime type > **T4 GPU**.
3.  Run this code:

```python
# 1. Install Ultralytics
!pip install ultralytics

# 2. Upload your dataset zip file from Roboflow/CVAT
# (Unzip it into a folder called 'datasets')

# 3. Train the model
from ultralytics import YOLO

# Load the nano model
model = YOLO('yolo11n.pt') 

# Train
results = model.train(
    data='/content/datasets/data.yaml',  # Path to your dataset config
    epochs=50,                           # 50-100 is usually enough for fine-tuning
    imgsz=640,                           # Maintain resolution
    device=0,                            # Use GPU
    project='hallway_monitor',
    name='v1'
)
```

### Phase 4: Deploy Back to Pi
1.  Download the trained `best.pt` file from Colab.
2.  Transfer it to your Raspberry Pi.
3.  **Export for NCS2 (Critical Step):**
    ```bash
    yolo export model=best.pt format=openvino half=True
    ```
4.  Update your `crowd_counting_rpi.py` to use your new model path or pass it via command line:
    ```bash
    python3 crowd_counting_rpi.py --model best_openvino_model/
    ```

## 📉 Advanced: Reducing Model Size (Quantization)
Since you are using Intel NCS2, you are already using FP16 (Half Precision).
For further speed (at cost of some accuracy), you can explore **INT8 Quantization** with the OpenVINO toolkit, but this is complex and usually not needed if you stick to the **Nano (n)** model.
