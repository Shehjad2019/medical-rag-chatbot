FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (build-essential for some pip packages)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Run flask server using gunicorn for production
# Fallback to app.py if gunicorn isn't heavily configured
CMD ["python", "app.py"]
