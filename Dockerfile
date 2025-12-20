# Use Python 3.11 as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies and compilers
# - build-essential: gcc, g++, make
# - default-jdk: Java
# - nodejs/npm: JavaScript/TypeScript
# - golang: Go
# - rustc: Rust
# - mono-complete: C#
RUN apt-get update && apt-get install -y \
    build-essential \
    default-jdk \
    nodejs \
    npm \
    golang-go \
    rustc \
    mono-complete \
    && rm -rf /var/lib/apt/lists/*

# Install TypeScript runner globally
RUN npm install -g ts-node typescript

# Copy requirements first for caching
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ backend/

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
