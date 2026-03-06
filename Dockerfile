FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies if needed (e.g. for cryptography)
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the panel folder contents into /app
COPY new_panel/ /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the application
# Railway provides the PORT env var
CMD ["sh", "-c", "uvicorn app.main:sio_app --host 0.0.0.0 --port ${PORT:-8000}"]
