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
OPENAI_API_KEY=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
SECRET_KEY=travel-chatbot-secret-key-for-jwt-tokens-2024
DATABASE_URL=sqlite:///travel_chatbot.db
RAPID_API_KEY=dfade5fd12mshc0d7bdfde01ee7dp19f143jsn38dda501a038
AMADEUS_CLIENT_ID=HL6VVtKrkMNEGJAt4bxb7pXaJj9lgAom
AMADEUS_CLIENT_SECRET=AA7v5azuULhZsb4O
AMADEUS_ACCESS_TOKEN=r8yMqAYqvVeiRqa1TFBjqNRrPgfF
EOF
    echo "✅ Environment file created"
else
    echo "✅ Environment file already exists"
fi
cd ..

echo "🎉 Setup complete! Ready for Replit deployment."
echo "📝 To start the server, run: cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000" 