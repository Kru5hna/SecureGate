// DOM Elements
const navLinks = document.querySelectorAll(".nav-links li");
const slideTabs = document.querySelectorAll(".tab-content");
const toastContainer = document.getElementById("toast-container");

// State
let allVehicles = [];

// Initialize
document.addEventListener("DOMContentLoaded", () => {
  // Setup Navigation
  navLinks.forEach((link) => {
    link.addEventListener("click", () => {
      navLinks.forEach((l) => l.classList.remove("active"));
      link.classList.add("active");

      const tabId = link.getAttribute("data-tab");
      swtichTab(tabId);
    });
  });

  // Setup Scanner
  setupScannerModes();
  setupCameraCapture();
  setupDragAndDrop();

  // Initial Data Fetch
  fetchDashboardStats();
  fetchRegisteredVehicles();
  fetchDetectionHistory();

  // Set auto-refresh interval for stats (every 30s)
  setInterval(fetchDashboardStats, 30000);
});

// Tab Switching Logic
function swtichTab(tabId) {
  slideTabs.forEach((tab) => tab.classList.remove("active"));
  document.getElementById(`tab-${tabId}`).classList.add("active");

  // Update active nav link (if triggered from elsewhere)
  navLinks.forEach((l) => {
    l.classList.toggle("active", l.getAttribute("data-tab") === tabId);
  });

  // Refresh data depending on tab
  if (tabId === "dashboard") fetchDashboardStats();
  if (tabId === "database") fetchRegisteredVehicles();
  if (tabId === "history") fetchDetectionHistory();
}

// ==========================================
// SCANNER LOGIC (Camera & Upload)
// ==========================================
let currentFile = null;
let stream = null;

function handleFileSelection(file) {
  const dropZone = document.getElementById("drop-zone");
  const cameraZone = document.getElementById("camera-zone");
  const previewContainer = document.getElementById("preview-container");
  const imagePreview = document.getElementById("image-preview");

  if (!file.type.startsWith("image/")) {
    showToast("Please upload an image file.", "error");
    return;
  }

  currentFile = file;
  const reader = new FileReader();
  reader.onload = (e) => {
    imagePreview.src = e.target.result;
    dropZone.style.display = "none";
    cameraZone.style.display = "none";
    previewContainer.style.display = "block";
    document.getElementById("results-panel").style.display = "none"; // hide old results
    stopCamera(); // Stop camera when previewing
  };
  reader.readAsDataURL(file);
}

function setupScannerModes() {
  const btnCamera = document.getElementById("btn-mode-camera");
  const btnUpload = document.getElementById("btn-mode-upload");
  const cameraZone = document.getElementById("camera-zone");
  const uploadZone = document.getElementById("drop-zone");
  const previewContainer = document.getElementById("preview-container");

  btnCamera.addEventListener("click", () => {
    btnCamera.classList.replace("btn-secondary", "btn-primary");
    btnUpload.classList.replace("btn-primary", "btn-secondary");
    cameraZone.style.display = "block";
    uploadZone.style.display = "none";
    previewContainer.style.display = "none";
    currentFile = null;
    startCamera();
  });

  btnUpload.addEventListener("click", () => {
    btnUpload.classList.replace("btn-secondary", "btn-primary");
    btnCamera.classList.replace("btn-primary", "btn-secondary");
    uploadZone.style.display = "block";
    cameraZone.style.display = "none";
    previewContainer.style.display = "none";
    currentFile = null;
    stopCamera();
  });

  // Stop camera when leaving scan tab
  navLinks.forEach((link) => {
    link.addEventListener("click", () => {
      if (link.getAttribute("data-tab") !== "scan") {
        stopCamera();
      } else if (btnCamera.classList.contains("btn-primary")) {
        startCamera();
      }
    });
  });
}

function startCamera() {
  const video = document.getElementById("camera-video");
  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: "environment" } })
      .then((s) => {
        stream = s;
        video.srcObject = stream;
        video.play();
      })
      .catch((err) => {
        console.error(err);
        showToast("Cannot access camera.", "error");
      });
  }
}

function stopCamera() {
  if (stream) {
    stream.getTracks().forEach((track) => track.stop());
    stream = null;
  }
}

function setupCameraCapture() {
  const btnCapture = document.getElementById("btn-capture-scan");
  const video = document.getElementById("camera-video");
  const canvas = document.getElementById("camera-canvas");

  btnCapture.addEventListener("click", () => {
    if (!stream) return;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob(
      (blob) => {
        const file = new File([blob], "camera_capture.jpg", {
          type: "image/jpeg",
        });
        handleFileSelection(file);
      },
      "image/jpeg",
      0.95,
    );
  });

  // Start it on first load since Camera is default active
  startCamera();
}

function setupDragAndDrop() {
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("file-input");
  const cancelBtn = document.getElementById("btn-cancel-scan");
  const btnProcess = document.getElementById("btn-process-scan");

  ["dragenter", "dragover", "dragleave", "drop"].forEach((eventName) => {
    dropZone.addEventListener(
      eventName,
      (e) => {
        e.preventDefault();
        e.stopPropagation();
      },
      false,
    );
  });

  ["dragenter", "dragover"].forEach((eventName) => {
    dropZone.addEventListener(
      eventName,
      () => dropZone.classList.add("dragover"),
      false,
    );
  });

  ["dragleave", "drop"].forEach((eventName) => {
    dropZone.addEventListener(
      eventName,
      () => dropZone.classList.remove("dragover"),
      false,
    );
  });

  dropZone.addEventListener("drop", (e) => {
    handleFileSelection(e.dataTransfer.files[0]);
  });

  fileInput.addEventListener("change", function () {
    if (this.files && this.files.length > 0) {
      handleFileSelection(this.files[0]);
    }
  });

  if (cancelBtn) {
    cancelBtn.addEventListener("click", () => {
      currentFile = null;
      fileInput.value = "";
      document.getElementById("preview-container").style.display = "none";

      // Restore previous UI
      if (
        document
          .getElementById("btn-mode-camera")
          .classList.contains("btn-primary")
      ) {
        document.getElementById("camera-zone").style.display = "block";
        startCamera();
      } else {
        dropZone.style.display = "block";
      }
    });
  }

  btnProcess.addEventListener("click", () => {
    if (!currentFile) return;
    processImageScan(currentFile);
  });
}

// ==========================================
// API CALLS
// ==========================================

async function processImageScan(file) {
  const formData = new FormData();
  formData.append("image", file);

  const spinner = document.getElementById("loading-spinner");
  const resultsPanel = document.getElementById("results-panel");
  const resultsContent = document.getElementById("scan-results-content");

  resultsPanel.style.display = "block";
  spinner.style.display = "block";
  resultsContent.innerHTML =
    '<p class="text-center">Processing image with YOLO AI...</p>';

  try {
    const response = await fetch("/api/detect", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) throw new Error(data.error || "Server error");

    renderScanResults(data);

    // Refresh dashboard stats quietly in background
    fetchDashboardStats();
  } catch (err) {
    showToast(err.message, "error");
    resultsContent.innerHTML = `<p class="error-text">Failed: ${err.message}</p>`;
  } finally {
    spinner.style.display = "none";
  }
}

async function fetchDashboardStats() {
  try {
    const res = await fetch("/api/stats");
    const data = await res.json();

    document.getElementById("stat-total-scans").textContent =
      data.total_detections;
    document.getElementById("stat-registered-hits").textContent =
      data.registered_hits;
    document.getElementById("stat-flagged").textContent = data.flagged_count;
    document.getElementById("stat-db-size").textContent =
      data.total_registered_vehicles;

    // Render Recent Flags on Dashboard
    const tbody = document.getElementById("recent-flags-tbody");
    tbody.innerHTML = "";

    if (data.recent_flagged.length === 0) {
      tbody.innerHTML =
        '<tr><td colspan="3" class="text-center text-muted">No recent security alerts</td></tr>';
    } else {
      data.recent_flagged.forEach((f) => {
        const tr = document.createElement("tr");
        const date = new Date(f.detected_at).toLocaleString();
        tr.innerHTML = `
                    <td><strong>${f.plate_number}</strong></td>
                    <td>${date}</td>
                    <td><span class="badge badge-danger">Unregistered</span></td>
                `;
        tbody.appendChild(tr);
      });
    }
  } catch (e) {
    console.error("Could not stats:", e);
  }
}

async function fetchRegisteredVehicles() {
  try {
    const res = await fetch("/api/vehicles");
    const data = await res.json();
    allVehicles = data.vehicles;
    renderVehiclesTable(allVehicles);
  } catch (e) {
    console.error(e);
  }
}

async function fetchDetectionHistory() {
  try {
    const res = await fetch("/api/logs?limit=100");
    const data = await res.json();
    renderHistoryTable(data.logs);
  } catch (e) {
    console.error(e);
  }
}

// ==========================================
// RENDERING UI
// ==========================================

function renderScanResults(data) {
  const container = document.getElementById("scan-results-content");

  if (data.total_plates_found === 0) {
    container.innerHTML = `
            <div class="result-card" style="text-align:center;">
                <h3><i class="fa-solid fa-circle-xmark text-muted"></i> No License Plate Detected</h3>
                <p class="text-muted" style="margin-top:10px;">Please try another image with a clearer view of the vehicle plate.</p>
            </div>
        `;
    return;
  }

  let html = `<div class="annotated-img-wrap"><img src="/static/uploads/${data.annotated_image}" alt="Annotated Image"></div>`;

  data.detections.forEach((det, i) => {
    const isReg = det.is_registered;
    const cardClass = isReg ? "success-card" : "danger-card";
    const icon = isReg
      ? '<i class="fa-solid fa-shield-check"></i>'
      : '<i class="fa-solid fa-siren-on"></i>';
    const statusText = isReg
      ? "AUTHORIZED VEHICLE"
      : "UNREGISTERED VEHICLE FLAG";

    // Owner Info block
    let ownerHtml = "";
    if (isReg && det.vehicle_info) {
      ownerHtml = `
                <div style="margin-top: 15px; padding: 10px; background: rgba(0,0,0,0.2); border-radius: 6px;">
                    <strong>Owner:</strong> ${det.vehicle_info.owner_name} <br>
                    <strong>Type:</strong> ${det.vehicle_info.vehicle_type}
                </div>
            `;
    } else {
      ownerHtml = `
                <div style="margin-top: 15px; padding: 10px; background: rgba(248, 81, 73, 0.1); border-radius: 6px; color: var(--danger);">
                    <strong>Action Required:</strong> Vehicle is not in authorized database. Stop and verify manually.
                </div>
            `;
    }

    html += `
            <div class="result-card ${cardClass}">
                <div class="flex-between">
                    <h4>Plate #${i + 1}</h4>
                    <span class="badge ${isReg ? "badge-success" : "badge-danger"}">
                        ${icon} ${statusText}
                    </span>
                </div>
                
                <div style="text-align: center;">
                    <br>
                    <p class="text-muted">Extracted Text</p>
                    <div class="plate-large">${det.plate_text || "UNKNOWN"}</div>
                    <p class="text-muted">OCR Confidence: ${(det.ocr_confidence * 100).toFixed(1)}%</p>
                </div>
                ${ownerHtml}
            </div>
        `;
  });

  container.innerHTML = html;
}

function renderVehiclesTable(vehicles) {
  const tbody = document.getElementById("db-tbody");
  tbody.innerHTML = "";

  if (vehicles.length === 0) {
    tbody.innerHTML =
      '<tr><td colspan="5" style="text-align:center;">No vehicles registered yet.</td></tr>';
    return;
  }

  vehicles.forEach((v) => {
    const tr = document.createElement("tr");
    const date = new Date(v.added_on).toLocaleDateString();
    tr.innerHTML = `
            <td><strong>${v.plate_number}</strong></td>
            <td>${v.owner_name}</td>
            <td>${v.vehicle_type}</td>
            <td>${date}</td>
            <td>
                <button class="btn btn-danger btn-sm" onclick="deleteVehicle('${v.plate_number}')">
                    <i class="fa-solid fa-trash"></i>
                </button>
            </td>
        `;
    tbody.appendChild(tr);
  });
}

function renderHistoryTable(logs) {
  const tbody = document.getElementById("history-tbody");
  tbody.innerHTML = "";

  if (logs.length === 0) {
    tbody.innerHTML =
      '<tr><td colspan="5" style="text-align:center;">No history available.</td></tr>';
    return;
  }

  logs.forEach((log) => {
    const tr = document.createElement("tr");
    const date = new Date(log.detected_at).toLocaleString();
    tr.innerHTML = `
            <td>
                <a href="/static/uploads/${log.image_path}" target="_blank" style="color:var(--primary); text-decoration:none;">
                    <i class="fa-solid fa-image"></i> View Crop
                </a>
            </td>
            <td><strong>${log.plate_number || "UNKNOWN"}</strong></td>
            <td>${(log.confidence * 100).toFixed(1)}%</td>
            <td>${date}</td>
            <td>
                <span class="badge ${log.is_registered ? "badge-success" : "badge-danger"}">
                    ${log.is_registered ? "Registered" : "Flagged"}
                </span>
            </td>
        `;
    tbody.appendChild(tr);
  });
}

// ==========================================
// MODAL & CRUD Operations
// ==========================================
const modal = document.getElementById("add-modal");
document
  .getElementById("btn-add-vehicle")
  .addEventListener("click", () => modal.classList.add("active"));
document
  .getElementById("close-modal")
  .addEventListener("click", () => modal.classList.remove("active"));
document
  .getElementById("btn-modal-cancel")
  .addEventListener("click", () => modal.classList.remove("active"));

document
  .getElementById("add-vehicle-form")
  .addEventListener("submit", async (e) => {
    e.preventDefault();

    const plate = document
      .getElementById("in-plate")
      .value.toUpperCase()
      .replace(/\s/g, "");
    const owner = document.getElementById("in-owner").value;
    const type = document.getElementById("in-type").value;

    const btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true;

    try {
      const res = await fetch("/api/vehicles", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          plate_number: plate,
          owner_name: owner,
          vehicle_type: type,
        }),
      });

      const data = await res.json();
      if (res.ok) {
        showToast(data.message, "success");
        modal.classList.remove("active");
        e.target.reset();
        fetchRegisteredVehicles(); // refresh table
        fetchDashboardStats();
      } else {
        showToast(data.message || data.error, "error");
      }
    } catch (err) {
      showToast("Network error while saving.", "error");
    } finally {
      btn.disabled = false;
    }
  });

async function deleteVehicle(plate) {
  if (
    !confirm(
      `Are you sure you want to remove ${plate} from the authorized directory?`,
    )
  )
    return;

  try {
    const res = await fetch(`/api/vehicles/${plate}`, { method: "DELETE" });
    const data = await res.json();

    if (res.ok) {
      showToast(data.message, "success");
      fetchRegisteredVehicles();
      fetchDashboardStats();
    } else {
      showToast(data.message || data.error, "error");
    }
  } catch (err) {
    showToast("Error deleting vehicle.", "error");
  }
}

// Simple search filter for DB
document.getElementById("db-search").addEventListener("input", (e) => {
  const term = e.target.value.toLowerCase();
  const filtered = allVehicles.filter(
    (v) =>
      v.plate_number.toLowerCase().includes(term) ||
      v.owner_name.toLowerCase().includes(term),
  );
  renderVehiclesTable(filtered);
});

// Toast Utility
function showToast(msg, type = "success") {
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  el.innerHTML = `
        <i class="fa-solid ${type === "success" ? "fa-check-circle" : "fa-triangle-exclamation"}"></i>
        <span>${msg}</span>
    `;
  toastContainer.appendChild(el);

  setTimeout(() => {
    el.style.opacity = "0";
    setTimeout(() => el.remove(), 300);
  }, 3000);
}
