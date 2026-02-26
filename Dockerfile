# Use a lightweight Python base image
FROM python:3.10-slim

# Install system dependencies required for OpenCV, EasyOCR, and Tesseract
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files (Frontend + Backend + Model)
COPY . .

# Create the uploads directory required by the backend
RUN mkdir -p static/uploads && chmod 777 static/uploads

# Expose the standard port Hugging Face Spaces uses
EXPOSE 7860

# Start the application using Gunicorn (production server)
CMD ["gunicorn", "-b", "0.0.0.0:7860", "app:app"]
