# Stage 1: Build Frontend
FROM node:18-alpine as frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Runtime
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Backend Code
COPY backend/ ./backend

# Copy Frontend Build from Stage 1
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# Expose port 7860 (Standard for HF Spaces)
EXPOSE 7860

# Run the app
# Note: We run from root, so module is backend.main
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
