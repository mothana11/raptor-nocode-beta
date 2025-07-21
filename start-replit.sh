#!/usr/bin/env bash

echo "🚀 Starting Travel Chatbot for Replit..."

# Install backend dependencies
echo "📦 Installing Python dependencies..."
cd backend
python -m pip install --user -r requirements.txt
cd ..

# Install and build frontend
echo "📦 Installing and building frontend..."
cd frontend
npm install --silent
npm run build --silent
cd ..

# Update backend to serve static files
echo "🔧 Configuring backend to serve frontend..."

# Start the FastAPI server
echo "🌟 Starting server on port 8000..."
export PORT=8000
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port $PORT 