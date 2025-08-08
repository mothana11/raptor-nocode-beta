#!/usr/bin/env bash
set -e                                              # bail on error

echo "🚀 Starting Travel Chatbot for Replit..."

# ── Backend deps ──────────────────────────────────────────────────────────
echo "📦 Installing Python dependencies..."
cd backend
python3 -m pip install --no-cache-dir -r requirements.txt   # ← drop --user
cd ..

# ── Front-end build (optional) ───────────────────────────────────────────
echo "📦 Installing and building frontend..."
cd frontend
if command -v npm &>/dev/null; then
  npm ci --silent               # faster/safer than npm install
  npm run build --silent
  echo "✅ Frontend built successfully"
else
  echo "⚠️  npm not found, skipping frontend build"
fi
cd ..

# ── .env scaffold  (first-run only) ───────────────────────────────────────
echo "🔧 Creating environment file..."
cd backend
if [[ ! -f .env ]]; then
  cat > .env <<'EOF'
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

# ── Launch server ─────────────────────────────────────────────────────────
echo "🌟 Starting server on port 8000..."
export PORT=8000
cd backend
python3 -m uvicorn main:app --host 0.0.0.0 --port "$PORT"
