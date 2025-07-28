# Use Python 3.9 slim base image
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies with cleanup
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# First install only torch with CPU-only version to avoid CUDA downloads
COPY requirements_torch.txt .
RUN pip install --no-cache-dir \
    --default-timeout=300 \
    --retries 5 \
    -r requirements_torch.txt

# Then install remaining requirements
COPY requirements.txt .
RUN pip install --no-cache-dir \
    --default-timeout=300 \
    --retries 5 \
    -r requirements.txt

# Copy application files
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV MODEL_NAME=all-MiniLM-L6-v2

# Entry point
ENTRYPOINT ["python", "main.py"]