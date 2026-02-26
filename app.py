"""
Flask backend for the Flagging Unregistered Vehicles system.
Serves the web dashboard and provides API endpoints for detection,
vehicle management, and statistics.
"""

import os
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory
from werkzeug.utils import secure_filename

import database as db
from detection import detect_and_read

# ─── App Setup ──────────────────────────────────────────────────────

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max upload

# Upload folder
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "webp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ─── Initialize Database ───────────────────────────────────────────

db.init_db()

# ─── Page Routes ────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the main dashboard page."""
    return render_template("index.html")


@app.route("/static/uploads/<path:filename>")
def serve_upload(filename):
    """Serve uploaded and processed images."""
    return send_from_directory(UPLOAD_FOLDER, filename)


# ─── Detection API ──────────────────────────────────────────────────

@app.route("/api/detect", methods=["POST"])
def detect():
    """
    Upload an image and run license plate detection + OCR.
    Returns detection results with registration status.
    """
    if "image" not in request.files:
        return jsonify({"error": "No image file provided."}), 400

    file = request.files["image"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

    # Save uploaded file with a unique name
    ext = file.filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex[:12]}.{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, unique_name)
    file.save(filepath)

    try:
        # Run detection pipeline
        result = detect_and_read(filepath)

        if "error" in result:
            return jsonify(result), 500

        # Check each detected plate against the database
        for detection in result["detections"]:
            plate_text = detection["plate_text"]
            if plate_text:
                vehicle_info = db.is_vehicle_registered(plate_text)
                detection["is_registered"] = vehicle_info is not None
                detection["vehicle_info"] = dict(vehicle_info) if vehicle_info else None

                # Log the detection
                db.add_detection_log(
                    plate_number=plate_text,
                    confidence=detection["ocr_confidence"],
                    is_registered=detection["is_registered"],
                    image_path=unique_name,
                )
            else:
                detection["is_registered"] = False
                detection["vehicle_info"] = None

        # Add the uploaded image filename to the result
        result["uploaded_image"] = unique_name

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Registered Vehicles API ────────────────────────────────────────

@app.route("/api/vehicles", methods=["GET"])
def get_vehicles():
    """Get all registered vehicles."""
    vehicles = db.get_all_vehicles()
    return jsonify({"vehicles": vehicles, "count": len(vehicles)})


@app.route("/api/vehicles", methods=["POST"])
def add_vehicle():
    """Add a new vehicle to the registered database."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided."}), 400

    plate_number = data.get("plate_number", "").strip()
    owner_name = data.get("owner_name", "").strip()
    vehicle_type = data.get("vehicle_type", "Car").strip()

    if not plate_number or not owner_name:
        return jsonify({"error": "plate_number and owner_name are required."}), 400

    result = db.add_vehicle(plate_number, owner_name, vehicle_type)
    status = 201 if result["success"] else 409
    return jsonify(result), status


@app.route("/api/vehicles/<plate_number>", methods=["DELETE"])
def remove_vehicle(plate_number):
    """Remove a vehicle from the registered database."""
    result = db.delete_vehicle(plate_number)
    status = 200 if result["success"] else 404
    return jsonify(result), status


# ─── Detection Logs API ─────────────────────────────────────────────

@app.route("/api/logs", methods=["GET"])
def get_logs():
    """Get all detection logs."""
    limit = request.args.get("limit", 50, type=int)
    logs = db.get_detection_logs(limit=limit)
    return jsonify({"logs": logs, "count": len(logs)})


# ─── Statistics API ──────────────────────────────────────────────────

@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Get dashboard statistics."""
    stats = db.get_stats()
    return jsonify(stats)


# ─── Run Server ──────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  Flagging Unregistered Vehicles - License Plate Detection")
    print("  Starting server at http://localhost:7860")
    print("=" * 60)
    app.run(debug=True, host="0.0.0.0", port=7860)
