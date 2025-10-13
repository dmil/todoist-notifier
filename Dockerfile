# Use Python 3.11 slim image
FROM python:3.11-slim

# Install system dependencies for Tkinter and display
RUN apt-get update && apt-get install -y \
    python3-tk \
    x11-apps \
    fonts-noto-color-emoji \
    fontconfig \
    && rm -rf /var/lib/apt/lists/* \
    && fc-cache -f -v

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose webhook port
EXPOSE 5000

# Set display environment variable (will be overridden by docker-compose)
ENV DISPLAY=:0

# Run the application
CMD ["python", "main.py"]
