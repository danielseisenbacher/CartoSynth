# Start from official Python image
FROM python:3.8

# Set working directory
WORKDIR /workspace

# Copy requirements file
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Install any system packages you need (optional)
RUN apt-get update && apt-get install -y \
    vim \
    && rm -rf /var/lib/apt/lists/*