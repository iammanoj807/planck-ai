# Stage 1: Build React Frontend
FROM node:18-alpine as build-step

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python Backend with Static Files
FROM python:3.11-slim-bookworm

# Install system dependencies (Poppler for PDF, Tesseract for OCR if needed)
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy backend requirements
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Copy built frontend from Stage 1 to backend/static
COPY --from=build-step /app/frontend/dist ./backend/static

# Set Environment Variables
ENV PORT=7860
ENV PYTHONPATH=/app/backend

# Run FastAPI (Serving Frontend + Backend)
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
