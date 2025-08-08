#!/bin/bash

echo "🚀 Setting up Travel Chatbot for Replit..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
cd backend
pip install -r requirements.txt
cd ..

# Install frontend dependencies and build
echo "📦 Installing and building frontend..."
cd frontend
npm install --silent
npm run build --silent
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

echo "🎉 Setup complete! Ready for Replit deployment."
echo "📝 To start the server, run: cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000" 