# Multi-stage build for React frontend and Python backend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ ./
RUN npm run build

# Python backend stage
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend code
COPY backend/ ./backend/
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist ./backend/static

# Create uploads directory
RUN mkdir -p /app/backend/uploads

# Set working directory to backend
WORKDIR /app/backend

# Expose port
EXPOSE $PORT

# Start command
CMD python -m uvicorn main:app --host 0.0.0.0 --port $PORT 