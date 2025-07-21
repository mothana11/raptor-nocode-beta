#!/bin/bash

echo "🚀 Travel Chatbot - Production Deployment"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if running as root (for some cloud deployments)
if [[ $EUID -eq 0 ]]; then
   print_warning "Running as root - ensure this is intended for your deployment environment"
fi

# Environment setup
print_info "Setting up production environment..."

# Create production environment file
if [ ! -f "backend/.env.production" ]; then
    echo "Creating production environment template..."
    cat > backend/.env.production << EOF
# Production Environment Configuration
OPENAI_API_KEY=your_openai_api_key_here
JWT_SECRET=\$(openssl rand -hex 32)
DATABASE_URL=sqlite:///app/data/travel_chatbot.db
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
CORS_ORIGINS=["http://localhost:3000"]
LOG_LEVEL=INFO
MAX_UPLOAD_SIZE=10485760
RATE_LIMIT_PER_MINUTE=60
EOF
    print_warning "Created backend/.env.production - PLEASE UPDATE WITH REAL VALUES!"
fi

# Install production dependencies
print_info "Installing production dependencies..."

# Backend dependencies
cd backend
if [ ! -d ".venv" ]; then
    print_info "Creating Python virtual environment..."
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install -r requirements.txt
print_status "Backend dependencies installed"

# Initialize database with auth tables
print_info "Initializing production database..."
python -c "
from main import init_db
from auth import init_auth_tables
init_db()
try:
    init_auth_tables()
    print('✅ Database initialized successfully')
except Exception as e:
    print(f'⚠️  Database already initialized: {e}')
"

cd ..

# Frontend dependencies and build
print_info "Building frontend for production..."
cd frontend
npm ci --production
npm run build
print_status "Frontend built successfully"
cd ..

# Create production data directory
mkdir -p data uploads logs
print_status "Created production directories"

# Set permissions
chmod 755 data uploads logs
print_status "Set directory permissions"

# Create systemd service file (for Linux systems)
if command -v systemctl &> /dev/null; then
    print_info "Creating systemd service..."
    
    cat > travel-chatbot.service << EOF
[Unit]
Description=Travel Chatbot Backend
After=network.target

[Service]
Type=simple
User=\$USER
WorkingDirectory=\$(pwd)/backend
Environment=PATH=\$(pwd)/backend/.venv/bin
ExecStart=\$(pwd)/backend/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --env-file .env.production
Restart=always
RestartSec=3
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    print_warning "Systemd service file created. To install:"
    echo "  sudo cp travel-chatbot.service /etc/systemd/system/"
    echo "  sudo systemctl daemon-reload"
    echo "  sudo systemctl enable travel-chatbot"
    echo "  sudo systemctl start travel-chatbot"
fi

# Create Docker production setup
print_info "Creating production Docker configuration..."

cat > docker-compose.production.yml << EOF
version: '3.8'

services:
  travel-chatbot:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=\${OPENAI_API_KEY}
      - JWT_SECRET=\${JWT_SECRET}
      - DATABASE_URL=sqlite:///app/data/travel_chatbot.db
    volumes:
      - ./data:/app/data
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./frontend/dist:/usr/share/nginx/html
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - travel-chatbot
    restart: unless-stopped

volumes:
  data:
  uploads:
  logs:
EOF

# Create nginx configuration
cat > nginx.conf << EOF
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server travel-chatbot:8000;
    }
    
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    server {
        listen 80;
        server_name localhost;
        
        # Frontend
        location / {
            root /usr/share/nginx/html;
            index index.html;
            try_files \$uri \$uri/ /index.html;
        }
        
        # Backend API
        location /api/ {
            proxy_pass http://backend/;
            proxy_set_header Host \$host;
            proxy_set_header X-Real-IP \$remote_addr;
            proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto \$scheme;
        }
        
        # WebSocket support (if needed)
        location /ws {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade \$http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host \$host;
        }
    }
}
EOF

print_status "Production Docker configuration created"

# Create monitoring script
cat > monitor.sh << 'EOF'
#!/bin/bash

echo "🔍 Travel Chatbot - Health Monitor"
echo "================================="

# Check backend health
echo "Checking backend health..."
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ "$BACKEND_STATUS" -eq 200 ]; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend is down (HTTP $BACKEND_STATUS)"
fi

# Check database
echo "Checking database..."
if [ -f "data/travel_chatbot.db" ]; then
    echo "✅ Database file exists"
    DB_SIZE=$(du -h data/travel_chatbot.db | cut -f1)
    echo "📊 Database size: $DB_SIZE"
else
    echo "❌ Database file not found"
fi

# Check logs
echo "Checking recent logs..."
if [ -f "logs/app.log" ]; then
    echo "📝 Recent log entries:"
    tail -5 logs/app.log
else
    echo "⚠️  No log file found"
fi

# Check disk space
echo "Checking disk space..."
df -h | grep -E '(Filesystem|/$)'

# Check memory usage
echo "Checking memory usage..."
free -h
EOF

chmod +x monitor.sh
print_status "Health monitoring script created"

# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash

BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "🔄 Creating backup in $BACKUP_DIR..."

# Backup database
cp data/travel_chatbot.db "$BACKUP_DIR/"
echo "✅ Database backed up"

# Backup uploads
cp -r uploads "$BACKUP_DIR/"
echo "✅ Uploads backed up"

# Backup configuration
cp backend/.env.production "$BACKUP_DIR/"
echo "✅ Configuration backed up"

# Create archive
tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"
rm -rf "$BACKUP_DIR"

echo "✅ Backup completed: $BACKUP_DIR.tar.gz"

# Keep only last 7 backups
ls -t backups/*.tar.gz | tail -n +8 | xargs -r rm
echo "🧹 Old backups cleaned up"
EOF

chmod +x backup.sh
print_status "Backup script created"

# Create analytics dashboard HTML
mkdir -p public
cat > public/analytics.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Travel Chatbot Analytics</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .card { background: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
        .stat { text-align: center; }
        .stat-number { font-size: 2rem; font-weight: bold; color: #3b82f6; }
        .stat-label { color: #6b7280; margin-top: 5px; }
        .chart-container { height: 400px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌟 Travel Chatbot Analytics Dashboard</h1>
        
        <div class="card">
            <h2>📊 Key Metrics</h2>
            <div class="stats" id="stats">
                <div class="stat">
                    <div class="stat-number" id="totalUsers">-</div>
                    <div class="stat-label">Total Users</div>
                </div>
                <div class="stat">
                    <div class="stat-number" id="realUsers">-</div>
                    <div class="stat-label">Registered Users</div>
                </div>
                <div class="stat">
                    <div class="stat-number" id="totalInteractions">-</div>
                    <div class="stat-label">Total Interactions</div>
                </div>
                <div class="stat">
                    <div class="stat-number" id="activeToday">-</div>
                    <div class="stat-label">Active Today</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>🛠️ Tool Usage</h2>
            <div class="chart-container">
                <canvas id="toolChart"></canvas>
            </div>
        </div>
        
        <div class="card">
            <h2>📈 Activity Over Time</h2>
            <div class="chart-container">
                <canvas id="activityChart"></canvas>
            </div>
        </div>
    </div>
    
    <script>
        // Fetch analytics data
        async function fetchAnalytics() {
            try {
                const response = await fetch('/analytics/dashboard');
                const data = await response.json();
                updateDashboard(data);
            } catch (error) {
                console.error('Error fetching analytics:', error);
            }
        }
        
        function updateDashboard(data) {
            // Update stats
            document.getElementById('totalUsers').textContent = data.user_stats.total_users;
            document.getElementById('realUsers').textContent = data.user_stats.real_users;
            document.getElementById('totalInteractions').textContent = Object.values(data.interaction_stats).reduce((a, b) => a + b, 0);
            document.getElementById('activeToday').textContent = Object.values(data.recent_activity).reduce((a, b) => a + b, 0);
            
            // Tool usage chart
            const toolCtx = document.getElementById('toolChart').getContext('2d');
            new Chart(toolCtx, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(data.tool_usage),
                    datasets: [{
                        data: Object.values(data.tool_usage),
                        backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#84cc16', '#f97316']
                    }]
                }
            });
            
            // Activity chart
            const activityCtx = document.getElementById('activityChart').getContext('2d');
            new Chart(activityCtx, {
                type: 'line',
                data: {
                    labels: Object.keys(data.recent_activity),
                    datasets: [{
                        label: 'Events',
                        data: Object.values(data.recent_activity),
                        borderColor: '#3b82f6',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)'
                    }]
                }
            });
        }
        
        // Load data on page load
        fetchAnalytics();
        
        // Refresh every 30 seconds
        setInterval(fetchAnalytics, 30000);
    </script>
</body>
</html>
EOF

print_status "Analytics dashboard created"

print_info "Creating startup script..."
cat > start-production.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting Travel Chatbot in Production Mode"

# Source environment
if [ -f "backend/.env.production" ]; then
    export $(grep -v '^#' backend/.env.production | xargs)
fi

# Start backend
cd backend
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --env-file .env.production &
BACKEND_PID=$!

echo "✅ Backend started (PID: $BACKEND_PID)"

# Serve frontend (simple Python server for demo)
cd ../frontend/dist
python3 -m http.server 3000 &
FRONTEND_PID=$!

echo "✅ Frontend started (PID: $FRONTEND_PID)"

echo ""
echo "🌟 Travel Chatbot is running!"
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
echo "Analytics: http://localhost:3000/analytics.html"
echo ""
echo "Press Ctrl+C to stop all services"

# Trap Ctrl+C to clean up
trap "echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID; exit 0" INT

# Wait for interrupt
wait
EOF

chmod +x start-production.sh

echo ""
print_status "Production deployment setup complete!"
echo ""
print_info "📋 Next Steps:"
echo "1. Update backend/.env.production with your API keys and configuration"
echo "2. For local production test: ./start-production.sh"
echo "3. For Docker deployment: docker-compose -f docker-compose.production.yml up"
echo "4. For cloud deployment: Use the systemd service or Docker setup"
echo ""
print_info "🔧 Management Commands:"
echo "- Health check: ./monitor.sh"
echo "- Create backup: ./backup.sh"
echo "- View analytics: Open http://localhost:3000/analytics.html"
echo ""
print_info "🚀 Your travel chatbot is now ready for production deployment!"

echo "=========================================="
echo "🎉 Production deployment setup complete!"
echo "==========================================" 