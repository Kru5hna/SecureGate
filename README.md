

<div align="center">

# 🛡️ SecureGate — Intelligent Vehicle Access Control

**Flagging Unregistered Vehicles Using License Plate Detection & Deep Learning**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-Backend-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Object_Detection-00FFFF?style=for-the-badge&logo=yolo&logoColor=black)](https://docs.ultralytics.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

> A next-generation campus security system that uses **YOLOv8** object detection,
> **EasyOCR + Tesseract** dual-engine OCR, and optional **Moonshot Kimi Vision AI**
> to detect, read, and flag unauthorized vehicle license plates in real time.

</div>

---

## 📸 Screenshots

| Landing Page | Dashboard Overview |
|:---:|:---:|
| ![Landing Page](output/landing_page.png) | ![Dashboard](output/dashboard.png) |

| Live Scan & Detection | Registered Vehicles DB |
|:---:|:---:|
| ![Live Scan](output/live_scan.png) | ![Vehicles DB](output/registered_vehicles.png) |

| Detection History | |
|:---:|:---:|
| ![History](output/detection_history.png) |

> 💡 *Add your own screenshots to the `output/` folder and update the filenames above.*

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     SecureGate System                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌──────────┐    ┌──────────────┐    ┌──────────────────┐  │
│   │  Browser  │───▶│  Flask API   │───▶│  YOLO v8 Model   │  │
│   │  (UI)     │◀──│  (app.py)    │◀──│  (detection.py)  │  │
│   └──────────┘    └──────┬───────┘    └────────┬─────────┘  │
│                          │                     │             │
│                   ┌──────▼───────┐    ┌────────▼─────────┐  │
│                   │  SQLite DB   │    │  OCR Pipeline     │  │
│                   │ (database.py)│    │  EasyOCR          │  │
│                   │              │    │  Tesseract         │  │
│                   │  • Vehicles  │    │  Kimi Vision (opt)│  │
│                   │  • Logs      │    └──────────────────┘  │
│                   └──────────────┘                           │
└─────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🎯 **YOLOv8 Detection** | Custom-trained YOLOv8 model for Indian license plate localization |
| 🔍 **Triple OCR Pipeline** | Kimi Vision AI → EasyOCR → Tesseract fallback chain for maximum accuracy |
| 📷 **Live Camera Scan** | Capture directly from webcam or upload saved images |
| 🗄️ **Vehicle Registry** | Full CRUD for managing authorized vehicles (SQLite) |
| 📊 **Real-time Dashboard** | Live stats, security alerts, detection history |
| 🇮🇳 **Indian Plate Format** | Smart validation for Indian license plate patterns (e.g., `MH31AB1234`) |
| 🐳 **Docker Ready** | One-command deployment via Docker / Hugging Face Spaces |
| 📱 **Responsive UI** | Works on desktop, tablet, and mobile devices |

---

## 📂 Project Structure

```
SecureGate/
├── app.py                  # Flask backend — routes & API endpoints
├── detection.py            # YOLO detection + OCR pipeline (EasyOCR, Tesseract, Kimi)
├── database.py             # SQLite database — vehicles CRUD & detection logs
├── best (1).pt             # Pre-trained YOLOv8 model weights for plate detection
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker build config (for HF Spaces / cloud deploy)
├── .env                    # API keys (KIMI_API_KEY) — NOT committed to Git
├── .gitignore              # Git ignore rules
├── vehicles.db             # SQLite database (auto-created on first run)
│
├── templates/
│   ├── landing.html        # Landing / intro page
│   └── index.html          # Main dashboard SPA (tabs: Dashboard, Scan, DB, History)
│
├── static/
│   ├── css/
│   │   └── style.css       # Dashboard styles (dark glassmorphism theme)
│   ├── js/
│   │   └── app.js          # Frontend logic (API calls, camera, drag-drop, rendering)
│   └── uploads/            # Runtime: uploaded & processed images (git-ignored)
│
└── output/                 # Sample output screenshots for documentation
    └── (add your screenshots here)
```

---

## 📦 Dataset

The model was trained on the **Indian Vehicle Dataset** from Kaggle.

🔗 **Dataset Link:** [https://www.kaggle.com/datasets/saisirishan/indian-vehicle-dataset/](https://www.kaggle.com/datasets/saisirishan/indian-vehicle-dataset/)

### Dataset Details
- Contains images of Indian vehicles with license plates
- Used for training the YOLOv8 object detection model
- The dataset folder is git-ignored due to its large size
- **To retrain the model**, download the dataset and place it in the project root as `indian vehicle license plate dataset/`

---

## ⚙️ Model Weights

The pre-trained YOLOv8 model weights are included in this repository:

| File | Size | Description |
|---|---|---|
| `best (1).pt` | ~6 MB | YOLOv8 weights trained on Indian vehicle license plate dataset |

> The model is automatically loaded on first API call (lazy loading) to reduce startup time.

---

## 🚀 How to Run — Step-by-Step

### Prerequisites

Make sure you have the following installed on your system:

| Tool | Version | Download |
|---|---|---|
| **Python** | 3.10+ | [python.org](https://www.python.org/downloads/) |
| **Tesseract OCR** | Latest | [GitHub Releases](https://github.com/UB-Mannheim/tesseract/wiki) |
| **Git** | Latest | [git-scm.com](https://git-scm.com/) |

> ⚠️ **Windows users:** After installing Tesseract, ensure it's at `C:\Program Files\Tesseract-OCR\tesseract.exe` or update the path in `detection.py` (line 24).

---

### Step 1 — Clone the Repository

```bash
git clone https://github.com/Kru5hna/SecureGate.git
cd SecureGate
```

### Step 2 — Create a Virtual Environment (recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows (PowerShell):
venv\Scripts\Activate.ps1

# On Windows (CMD):
venv\Scripts\activate.bat

# On macOS/Linux:
source venv/bin/activate
```

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Set Up Environment Variables (Optional — for Kimi Vision AI)

Create a `.env` file in the project root:

```env
KIMI_API_KEY=your_moonshot_kimi_api_key_here
```

> 📝 **Note:** Kimi Vision AI is **optional**. The system will automatically fall back to EasyOCR + Tesseract if no API key is provided.

### Step 5 — Run the Application

```bash
python app.py
```

You should see:
```
============================================================
  Flagging Unregistered Vehicles - License Plate Detection
  Starting server at http://localhost:7860
============================================================
 * Serving Flask app 'app'
 * Running on http://127.0.0.1:7860
```

### Step 6 — Open in Browser

```
http://localhost:7860
```

🎉 **That's it!** The landing page will load. Click **"Launch Dashboard"** to access the full system.

---

### 🐳 Docker Deployment (Alternative)

```bash
# Build the Docker image
docker build -t securegate .

# Run the container
docker run -p 7860:7860 securegate
```

Then open `http://localhost:7860` in your browser.

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Landing page |
| `GET` | `/dashboard` | Main dashboard |
| `POST` | `/api/detect` | Upload image → detect plates → return results |
| `GET` | `/api/vehicles` | List all registered vehicles |
| `POST` | `/api/vehicles` | Add a new registered vehicle |
| `DELETE` | `/api/vehicles/<plate>` | Remove a registered vehicle |
| `GET` | `/api/logs?limit=50` | Get recent detection logs |
| `GET` | `/api/stats` | Get dashboard statistics |

### Example — Detect a License Plate via cURL

```bash
curl -X POST -F "image=@test_car.jpg" http://localhost:7860/api/detect
```

### Example — Add a Vehicle

```bash
curl -X POST http://localhost:7860/api/vehicles \
  -H "Content-Type: application/json" \
  -d '{"plate_number": "MH31AB1234", "owner_name": "John Doe", "vehicle_type": "Car"}'
```

---

## 🧠 Detection Pipeline

```
Image Upload
    │
    ▼
┌─────────────────────┐
│  YOLOv8 Inference   │  ← License plate localization (conf > 0.25)
│  (best (1).pt)      │
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Crop & Preprocess  │  ← 7 image variants: grayscale, bilateral,
│  (OpenCV)           │     Otsu, adaptive threshold, morphological
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  OCR Engine Chain   │
│                     │
│  1. Kimi Vision AI  │  ← Best accuracy (confidence 0.99)
│     (if API key)    │
│         ↓ fallback  │
│  2. EasyOCR         │  ← Multi-variant OCR with allowlist
│         ↓ fallback  │
│  3. Tesseract OCR   │  ← Baseline fallback (confidence 0.6)
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Clean & Validate   │  ← Indian plate format regex matching
│  (clean_plate_text) │     Common OCR misread correction (O→0, I→1)
└────────┬────────────┘
         │
         ▼
┌─────────────────────┐
│  Database Lookup    │  ← Check registered_vehicles table
│  (SQLite)           │     Log detection result
└─────────────────────┘
         │
         ▼
    ✅ Authorized  /  🚨 Flagged
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3 (Glassmorphism), Vanilla JS, Font Awesome |
| **Backend** | Python, Flask, Gunicorn |
| **Object Detection** | YOLOv8 (Ultralytics) |
| **OCR** | EasyOCR, Pytesseract, Moonshot Kimi Vision AI |
| **Database** | SQLite3 |
| **Image Processing** | OpenCV, Pillow, NumPy |
| **Deployment** | Docker, Hugging Face Spaces |
| **Fonts** | Space Grotesk, Outfit (Google Fonts) |

---

## 👥 Team

| Name | Role |
|---|---|
| **Krushna Raut** | Developer |
| **Vikram Jaiswal** | Developer |
| **Sankalp Choubey** | Developer |

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

**Built with ❤️ for campus security**

⭐ Star this repo if you found it useful!

</div>
