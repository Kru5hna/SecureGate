# 🚗 Flagging Unregistered Vehicles — AI Access Control System

![Project Banner](https://img.shields.io/badge/AI-Powered_Security-blue?style=for-the-badge)
![Deep Learning](https://img.shields.io/badge/Deep_Learning-YOLOv8-green?style=for-the-badge)
![Web Dashboard](https://img.shields.io/badge/Web_UI-Flask-red?style=for-the-badge)

An advanced Deep Learning project designed for automated vehicle access control in restricted environments (like colleges or residential societies). It uses **YOLOv8** to detect vehicle license plates, **EasyOCR** to extract the alphanumeric characters, and a **Python/Flask Web Dashboard** to cross-verify the vehicle against a high-security, authorized SQLite database in real-time.

---

## 🌟 Key Features

- **Live Camera Scan:** Access your device's webcam directly from the browser to scan vehicles entering the gate.
- **Drag & Drop Uploads:** Upload static images (.jpg, .png) for quick processing.
- **YOLOv8 Precision Detection:** High-accuracy license plate bounding box extraction.
- **Smart OCR Engine:** Custom OpenCV preprocessing + EasyOCR with strictly enforced alphanumeric allowlists for Indian plate formats (XX-00-XX-0000).
- **Authorized Database Management:** Add, search, and delete registered vehicle plates directly from the UI.
- **Security Alerting:** Instantly flags unregistered vehicles in red, while granting green clearance to authorized owners.
- **Immutable Detection History:** Complete event log capturing cropped plate images, confidence scores, and timestamps.

---

## 🛠️ Technology Stack

| Component                            | Technology Used                                 |
| ------------------------------------ | ----------------------------------------------- |
| **Machine Learning**                 | YOLOv8 (Ultralytics)                            |
| **Optical Character Recognition**    | EasyOCR                                         |
| **Backend API Server**               | Flask (Python)                                  |
| **Computer Vision (Pre-processing)** | OpenCV, Pillow                                  |
| **Database**                         | SQLite (with WAL mode for concurrent writes)    |
| **Frontend UI**                      | HTML5, CSS3 (Glassmorphism), Vanilla JavaScript |

---

## 🚀 Setup & Installation

### 1. Prerequisites

- Python 3.8+ installed
- A camera connected to your device (for live scan)
- `best (1).pt` — The fine-tuned YOLOv8 License Plate Detection weights

### 2. Clone and Install

Open a terminal in the project directory and install the required dependencies:

```bash
pip install -r requirements.txt
```

_(Note: The first run may take some time to download the EasyOCR language models in the background)._

### 3. Run the Server

Launch the Flask backend server:

```bash
python app.py
```

### 4. Access the Dashboard

Open your web browser and go to:
**[http://localhost:5000](http://localhost:5000)**

---

## 🧠 How It Works (Methodology)

1. **Input:** An image feed is received via webcam capture or file upload on the frontend.
2. **Detection Phase:** The YOLOv8 model runs inference to locate the bounding box (x, y, w, h) of the license plate within the frame.
3. **Pre-Processing pipeline:** The detected plate is cropped and passed through OpenCV. We apply:
   - Grayscale conversion
   - 2x Scale magnification
   - Bilateral Filtering (Noise reduction)
   - Adaptive & Otsu Thresholding (Binarization)
4. **Extraction Phase:** The enhanced variations are fed into EasyOCR (restricted to `A-Z` and `0-9`). The confidence scores are aggregated to reconstruct the final text.
5. **Logic Engine:** The parsed alphanumeric string is cleaned and checked against the `registered_vehicles` table in an SQLite database.
6. **Result Generation:** The web dashboard updates instantly, logging the event and flashing the security clearance (Allowed / Flagged).

---

## 👥 Project Team

**Shri Ramdeobaba College of Engineering and Management, Nagpur**  
_B.Tech. in Electronics and Computer Science (Deep Learning Project)_

- **Krushna Raut**
- **Vikram Jaiswal**
- **Sankalp Choubey**

**Guided by:** _Prof. Vikas Gupta_

---

## 🛡️ License

Built for academic and research purposes.
