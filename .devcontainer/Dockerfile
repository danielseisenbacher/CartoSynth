# Start from official Python image
FROM python:3.8

# Set working directory inside container
WORKDIR /workspace

# Install system dependencies (FontForge + optional tools)
RUN apt-get update && apt-get install -y \
    fontforge \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt
