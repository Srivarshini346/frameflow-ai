# Stage 1: Build React 18 Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python 3.11 Backend & FFmpeg Compositor
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies and FFmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy backend source
COPY backend/ /app/backend/
COPY cli/ /app/cli/

# Copy built frontend SPA assets
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

# Setup storage directory
RUN mkdir -p /app/storage

ENV PYTHONPATH=/app/backend
ENV HOST=0.0.0.0
ENV PORT=8000
ENV STORAGE_DIR=/app/storage

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
