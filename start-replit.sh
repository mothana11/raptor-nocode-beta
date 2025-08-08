#!/usr/bin/env bash

echo "🚀 Starting Travel Chatbot for Replit..."

# Install backend dependencies
echo "📦 Installing Python dependencies..."
cd backend
python3 -m pip install -r requirements.txt
cd ..

# Install and build frontend (if npm is available)
echo "📦 Installing and building frontend..."
cd frontend
if command -v npm &> /dev/null; then
    npm install --silent
    npm run build --silent
    echo "✅ Frontend built successfully"
else
    echo "⚠️  npm not found, skipping frontend build"
fi
cd ..

# Create a simple .env file for Replit (without sensitive keys)
echo "🔧 Creating environment file..."
cd backend
if [ ! -f .env ]; then
    cat > .env << 'EOF'
# Replit Demo Environment
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your_secret_key_here
DATABASE_URL=sqlite:///travel_chatbot.db
RAPID_API_KEY=your_rapid_api_key_here
AMADEUS_CLIENT_ID=your_amadeus_client_id_here
AMADEUS_CLIENT_SECRET=your_amadeus_client_secret_here
AMADEUS_ACCESS_TOKEN=your_amadeus_access_token_here
EOF
    echo "✅ Environment file created"
else
    echo "✅ Environment file already exists"
fi
cd ..

# Start the FastAPI server
echo "🌟 Starting server on port 8000..."
export PORT=8000
cd backend
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check Python syntax
echo "🔍 Checking Python syntax..."
python3 check_syntax.py

python3 -m uvicorn main:app --host 0.0.0.0 --port $PORT 