FROM python:3.11-slim

# Set a working directory
WORKDIR /app

# Install system deps required for some Python packages (lightweight)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt ./
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . /app

ENV PYTHONUNBUFFERED=1

# Expose Gradio port
EXPOSE 7860

# Default command to run the app
CMD ["python", "app.py"]
