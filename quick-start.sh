#!/bin/bash

echo "🚀 Travel Chatbot - Quick Start"
echo "================================="
echo ""
echo "🌟 This advanced travel chatbot includes:"
echo "   • 12 comprehensive travel tools (flights, hotels, car rentals, activities, insurance, etc.)"
echo "   • Voice input and image analysis capabilities"
echo "   • User registration and personalized learning"
echo "   • LangGraph AI workflow orchestration"
echo ""

# Function to check prerequisites
check_prerequisites() {
    echo "🔍 Checking prerequisites..."
    
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 is required but not installed."
        echo "   Please install Python 3.9+ from https://python.org"
        exit 1
    fi
    
    if ! command -v node &> /dev/null; then
        echo "❌ Node.js is required but not installed." 
        echo "   Please install Node.js 16+ from https://nodejs.org"
        exit 1
    fi
    
    echo "✅ Prerequisites check passed"
}

# Function to find available port
find_available_port() {
    local start_port=$1
    local port=$start_port
    
    while lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; do
        port=$((port + 1))
    done
    
    echo $port
}

# Function to setup backend
setup_backend() {
    echo ""
    echo "🔧 Setting up backend..."
    cd backend
    
    # Create virtual environment
    if [ ! -d ".venv" ]; then
        echo "   Creating Python virtual environment..."
        python3 -m venv .venv
    fi
    
    # Activate virtual environment
    echo "   Activating virtual environment..."
    source .venv/bin/activate
    
    # Install dependencies
    echo "   Installing Python dependencies..."
    pip install -r requirements.txt
    
    # Initialize database without fake data
    echo "   Initializing database..."
    python -c "
from main import init_db
from auth import init_auth_tables
print('Initializing database...')
init_db()
try:
    init_auth_tables()
    print('✅ Database initialized successfully')
except Exception as e:
    print(f'✅ Database already initialized: {e}')
"
    
    # Create .env file if needed
    if [ ! -f ".env" ]; then
        echo "   Creating environment file..."
        echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
        echo ""
        echo "⚠️  IMPORTANT: You need to add your OpenAI API key!"
        echo "   1. Get your API key from: https://platform.openai.com/api-keys"
        echo "   2. Edit backend/.env and replace 'your_openai_api_key_here' with your actual key"
        echo ""
        read -p "Press Enter after you've added your API key to backend/.env..."
    fi
    
    cd ..
}

# Function to setup frontend
setup_frontend() {
    echo ""
    echo "🔧 Setting up frontend..."
    cd frontend
    
    echo "   Installing Node.js dependencies..."
    npm install
    
    cd ..
}

# Function to start services
start_services() {
    echo ""
    echo "🚀 Starting services..."
    
    # Find available ports
    BACKEND_PORT=$(find_available_port 8000)
    FRONTEND_PORT=$(find_available_port 5173)
    
    echo ""
    echo "Using ports: Backend=$BACKEND_PORT, Frontend=$FRONTEND_PORT"
    echo ""
    
    # Start backend in background
    cd backend
    source .venv/bin/activate
    echo "Starting backend on http://localhost:$BACKEND_PORT..."
    uvicorn main:app --reload --port $BACKEND_PORT &
    BACKEND_PID=$!
    cd ..
    
    # Wait a moment for backend to start
    sleep 3
    
    echo "Starting frontend on http://localhost:$FRONTEND_PORT..."
    
    # Start frontend
    cd frontend
    npm run dev -- --port $FRONTEND_PORT &
    FRONTEND_PID=$!
    cd ..
    
    echo ""
    echo "✅ Services started successfully!"
    echo ""
    echo "🌐 Access the chatbot at: http://localhost:$FRONTEND_PORT"
    echo ""
    echo "🎯 Features to test:"
    echo "   • Create a new account or browse anonymously"
    echo "   • Voice input (microphone button)"
    echo "   • Image upload (travel documents)"
    echo "   • Multi-tool workflows with 12 travel tools"
    echo "   • Personalized responses that learn from your interactions"
    echo ""
    echo "🛠️ Available tools:"
    echo "   • Flight search and hotel booking"
    echo "   • Car rentals and activity booking"
    echo "   • Travel insurance and visa requirements"
    echo "   • Currency conversion and weather forecasts"
    echo "   • Travel alerts and booking management"
    echo ""
    echo "Press Ctrl+C to stop all services"
    
    # Wait for interrupt
    trap "echo ''; echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; exit 0" INT
    wait
}

# Main execution
check_prerequisites
setup_backend
setup_frontend
start_services 