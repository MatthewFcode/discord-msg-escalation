# Use Python 3.12 (slim version for smaller image size)
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/server

# Set work directory
WORKDIR /app

# Install system dependencies (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Ensure start.sh is executable
RUN chmod +x start.sh

# Expose port (Dokku uses PORT env var, but 8000 is a common default)
EXPOSE 8000

# Run the startup script
CMD ["./start.sh"]
