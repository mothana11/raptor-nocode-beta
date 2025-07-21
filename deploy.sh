#!/bin/bash

echo "🚀 Deploying Travel Chatbot for Public Demo..."

# Check if we're in the right directory
if [ ! -f "backend/main.py" ] || [ ! -f "frontend/package.json" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Create deployment directory
echo "📁 Setting up deployment directory..."
mkdir -p deployment
cd deployment

# Copy backend files
echo "🔧 Setting up backend..."
cp -r ../backend .
cd backend

# Create production requirements
cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
pydantic[email]==2.5.0
openai==1.3.7
langchain==0.1.0
langchain-openai==0.0.5
langgraph==0.0.20
aiofiles==23.2.1
python-dotenv==1.0.0
sqlite3
EOF

# Create production config
cat > .env << 'EOF'
OPENAI_API_KEY=your-openai-api-key-here
SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
EOF

# Create production startup script
cat > start_backend.sh << 'EOF'
#!/bin/bash
echo "🔧 Starting Travel Chatbot Backend..."
python -m uvicorn main:app --host 0.0.0.0 --port 8000
EOF
chmod +x start_backend.sh

cd ..

# Copy frontend files
echo "🎨 Setting up frontend..."
cp -r ../frontend .
cd frontend

# Update frontend to use production backend URL
sed -i '' 's|http://localhost:8000|https://your-backend-domain.com|g' src/components/Chat.tsx
sed -i '' 's|http://localhost:8000|https://your-backend-domain.com|g' src/components/AuthModal.tsx

# Create production build
echo "🏗️ Building frontend for production..."
npm install
npm run build

cd ..

# Create deployment instructions
cat > DEPLOYMENT_GUIDE.md << 'EOF'
# 🚀 Travel Chatbot Deployment Guide

## Quick Deploy Options:

### Option 1: Railway (Recommended - Free)
1. Go to [railway.app](https://railway.app)
2. Connect your GitHub repository
3. Add environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `SECRET_KEY`: A secure random string
4. Deploy!

### Option 2: Render (Free Tier)
1. Go to [render.com](https://render.com)
2. Create new Web Service
3. Connect your GitHub repo
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Option 3: Heroku
1. Install Heroku CLI
2. Run: `heroku create your-chatbot-name`
3. Run: `git push heroku main`

### Option 4: Vercel (Frontend) + Railway (Backend)
1. Deploy backend to Railway
2. Deploy frontend to Vercel
3. Update frontend URLs to point to Railway backend

## Environment Variables Needed:
- `OPENAI_API_KEY`: Your OpenAI API key
- `SECRET_KEY`: JWT secret key (generate with: `openssl rand -hex 32`)
- `ALGORITHM`: HS256
- `ACCESS_TOKEN_EXPIRE_MINUTES`: 1440

## Demo Link Format:
Once deployed, your demo link will be:
- Railway: `https://your-app-name.railway.app`
- Render: `https://your-app-name.onrender.com`
- Heroku: `https://your-app-name.herokuapp.com`

## Features Available:
✅ User registration and login
✅ Personalized travel recommendations
✅ 12 travel tools (flights, hotels, etc.)
✅ Voice input and file uploads
✅ Learning from user interactions
✅ Real-time chat interface

## Admin Features:
- View all users: `https://your-domain.com/analytics/dashboard`
- User data inspection scripts included
EOF

# Create Docker setup for easy deployment
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./backend:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      - REACT_APP_API_URL=http://localhost:8000
EOF

# Create backend Dockerfile
cat > backend/Dockerfile << 'EOF'
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Create frontend Dockerfile
cat > frontend/Dockerfile << 'EOF'
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
EOF

echo "✅ Deployment setup complete!"
echo ""
echo "📋 Next Steps:"
echo "1. Choose a deployment platform (Railway recommended)"
echo "2. Set your OpenAI API key in environment variables"
echo "3. Deploy and share the link!"
echo ""
echo "📖 See DEPLOYMENT_GUIDE.md for detailed instructions"
echo ""
echo "🔗 Quick Deploy Commands:"
echo "  Railway:  railway up"
echo "  Render:   render deploy"
echo "  Heroku:   heroku create && git push heroku main" 