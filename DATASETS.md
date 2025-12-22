# 📊 Recommended Public Datasets for Crowd Counting & Detection

Since you are using **YOLO11n** (a detection model), you need datasets that provide **bounding box annotations** (not just density maps).

## 🚀 Top Recommendations (YOLO Ready)

### 1. **CrowdHuman Dataset** (Highly Recommended)
-   **Description:** Specifically robust for crowded scenes with heavy occlusion (people blocking each other). Perfect for crowded hallways.
-   **Format:** Native is `.odgt`, but widely available in **YOLO format** on Kaggle.
-   **Size:** ~15,000 images, ~470k persons.
-   **Download:** [CrowdHuman in YOLO format on Kaggle](https://www.kaggle.com/datasets/katielink/crowdhuman-yolo-format) (or search "CrowdHuman YOLO" on Kaggle).

### 2. **Roboflow Universe: "Surveillance Person Detection"**
-   **Description:** Multiple community-contributed datasets specifically from CCTV/Surveillance cameras.
-   **Format:** **Native YOLOv8/v11 export**. This is the easiest path.
-   **Search Term:** Search "Person Detection Surveillance" on [universe.roboflow.com](https://universe.roboflow.com/).
-   **Example:** "Surveillance Object Detection" dataset.

### 3. **Caltech Pedestrian Dataset**
-   **Description:** Calculated for street scenes, but good for "overhead" angles.
-   **Size:** Very large.
-   **Note:** Good for general purpose, but might need conversion tools if not downloading a pre-processed version.

### 4. **ShanghaiTech (Converted to Detection)**
-   **Description:** Originally for density maps (dots), but some versions exist with converted bounding boxes.
-   **Use Case:** Only if you need extreme crowd density (thousands of people). For a hallway, CrowdHuman is better.

## 💡 How to Use These?
1.  **Download** the dataset (look for `images` and `labels` folders).
2.  **Combine** it with your own small dataset (from `TRAINING_GUIDE.md`) for the best results.
    -   *Strategy:* Use 80% public data + 20% your own specific hallway data.
3.  **Train** in Google Colab using the same steps in the Training Guide.
