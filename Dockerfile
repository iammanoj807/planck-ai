# -----------------------------------------------------------------------------
# Stage 1: Build Frontend
# -----------------------------------------------------------------------------
FROM node:18-slim AS frontend-builder

WORKDIR /app
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 2: Runtime Environment (Backend + Static Frontend)
# -----------------------------------------------------------------------------
FROM python:3.11-slim

WORKDIR /app

# Install System Dependencies & Compilers for Code Execution
# - build-essential: gcc, g++, make
# - default-jdk: Java
# - nodejs/npm: JavaScript/TypeScript execution (runtime)
# - golang: Go
RUN apt-get update && apt-get install -y \
    build-essential \
    default-jdk \
    nodejs \
    npm \
    golang-go \
    && rm -rf /var/lib/apt/lists/*
# Install TypeScript runner (globally available for code_executor)
# We use 'tsx' for better ESM/CJS compatibility
RUN npm install -g tsx typescript

# Install Python Dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Backend Code
COPY backend/ backend/

# Copy Built Frontend from Stage 1
# Backend expects it at /app/frontend/dist
COPY --from=frontend-builder /app/dist /app/frontend/dist

# Set permissions and path
ENV PYTHONPATH=/app:/app/backend

# Expose Hugging Face compatible port
EXPOSE 7860

# Run the application
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]