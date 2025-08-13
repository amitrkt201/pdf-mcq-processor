# Use Python 3.10 base image
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-hin \
    tesseract-ocr-eng \
    libgl1-mesa-glx \
    poppler-utils \
    ghostscript \
    libmupdf-dev \
    swig \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p uploads outputs

# Set environment variables
ENV PORT=10000
EXPOSE $PORT

# Start command
CMD ["gunicorn", "app:app", "-w", "2", "-b", "0.0.0.0:$PORT"]