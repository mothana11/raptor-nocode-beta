# Enhanced Travel Chatbot with MCP & LangGraph

A sophisticated travel assistant chatbot built with React, FastAPI, and LangGraph that supports **text messages**, **file uploads**, **image attachments**, and **voice input**. Now featuring **12 comprehensive travel tools** for complete trip planning!

## ✨ NEW: Advanced Travel Tools

### 🛠️ Complete Travel Service Suite (12 Tools)
- ✈️ **Flight Search & Hotel Booking** - Multi-airline search with realistic pricing
- 🚗 **Car Rental Search** - 6 vehicle categories across major rental companies  
- 🎭 **Activity Booking** - Tours, attractions, restaurants, shows with confirmations
- 🛡️ **Travel Insurance** - 3 coverage tiers with dynamic pricing
- 🌍 **Visa Requirements** - Smart visa checking with application guidance
- 💱 **Currency Converter** - Real-time exchange rates for major currencies
- 🌦️ **Weather Forecast** - Conditions with packing recommendations
- 🚨 **Travel Alerts** - Health, security, weather, transportation warnings
- 📋 **Booking Management** - Check status, modify, cancel with realistic fees
- 🎯 **Travel Recommendations** - Personalized destination advice
- 🔄 **Multi-tool Workflows** - Complex trip planning across services

### 🎭 Rich User Personalization
- **10 Demo Users** with complete travel profiles and history
- **46+ Travel Preferences** across 8 preference categories
- **46+ Past Trips** with ratings and destination experiences
- **25+ Active Bookings** across all travel service types
- **Loyalty Integration** - Bronze, Silver, Gold, Platinum benefits

## ✨ Core Features

### Enhanced Input Methods
- 📎 **File Attachments**: Upload PDFs, documents, and text files
- 🖼️ **Image Uploads**: Share images with the assistant (travel docs, tickets, etc.)
- 🎤 **Voice Input**: Speak to the chatbot using Web Speech API
- ⌨️ **Text Input**: Traditional typing interface

### Technical Architecture
- 🔧 **LangGraph Workflow**: Advanced AI reasoning with ReAct pattern
- 🛠️ **MCP Integration**: 12 comprehensive travel tools
- 📁 **File Management**: Secure file storage and serving
- 🎯 **Type Safety**: Full TypeScript support
- 🗄️ **Rich Context**: Persistent user profiles and conversation history

## 🚀 Quick Start for Demo

### Super Quick Setup (Recommended)
```bash
# Clone and run automated setup
git clone <your-repo-url>
cd raptor-nocode-beta
chmod +x quick-start.sh
./quick-start.sh
```

The automated script handles everything: prerequisites, dependencies, demo data, and service startup!

### Prerequisites
- Python 3.9+
- Node.js 16+
- OpenAI API key

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
cd backend
   ```

2. **Create and activate virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   Create a `.env` file in the backend directory:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

5. **Start the server**:
   ```bash
   python -m uvicorn main:app --reload --port 8000
   ```

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
npm install
   ```

3. **Start development server**:
   ```bash
npm run dev
```

4. **Open your browser**:
   Visit `http://localhost:5173`

## 📋 How to Use

### Text Messages
- Type your travel-related questions in the input field
- Ask about hotel bookings, flight reservations, rescheduling, or refunds
- The AI will provide helpful guidance and step-by-step instructions

### File Attachments
1. Click the **📎 attachment button**
2. Select files (PDFs, documents, images)
3. Files will appear in the preview area
4. Send your message with attachments
5. The AI will acknowledge receipt and offer relevant help

### Voice Input
1. Click the **🎤 microphone button** to start recording
2. Speak your question clearly
3. Click **⏹️ stop button** to finish
4. Your speech will be converted to text automatically
5. Review and send the message

### Image Uploads
1. Use the attachment button to select images
2. Supported formats: JPG, PNG, GIF, WebP
3. Images will display inline in your messages
4. Perfect for sharing travel documents, tickets, or itineraries

## 🛠️ API Endpoints

### Core Endpoints
- `POST /chat` - Send text messages
- `POST /chat-with-files` - Send messages with file attachments
- `GET /health` - Health check
- `GET /conversations/{id}/history` - Get conversation history

### File Handling
- Files are stored in `backend/uploads/` directory
- Served via `/uploads/{filename}` static route
- Metadata stored in SQLite database
- Automatic cleanup on errors

## 🏗️ Architecture

### Frontend (React + TypeScript)
```
frontend/
├── src/
│   ├── components/
│   │   └── Chat.tsx          # Main chat component
│   ├── App.tsx               # App entry point
│   └── main.tsx              # React entry point
├── index.html
└── package.json
```

### Backend (FastAPI + Python)
```
backend/
├── main.py                   # FastAPI application
├── workflow.py               # LangGraph workflow
├── mcp_tools.py             # Mock travel tools
├── requirements.txt
├── uploads/                 # File storage
└── travel_chatbot.db       # SQLite database
```

### Database Schema
- **conversations**: Conversation metadata
- **messages**: Chat messages with timestamps
- **message_attachments**: File attachment metadata

## 🎯 Use Cases

### Travel Planning
- "Help me find hotels in Paris for next week"
- "I need to reschedule my flight to Tokyo"
- "What's the refund policy for my booking?"

### Document Assistance
- Upload booking confirmations for help with changes
- Share travel documents for review
- Attach receipts for refund requests

### Voice Queries
- Quick questions while on the go
- Hands-free interaction
- Accessible for users with typing difficulties

## 🔧 Development

### Adding New Tools
1. Create tool functions in `mcp_tools.py`
2. Add to `ALL_TOOLS` dictionary
3. Tools automatically available in LangGraph workflow

### Customizing UI
- Modify `Chat.tsx` for interface changes
- Update styling with inline styles or CSS
- Add new input methods or message types

### Extending Backend
- Add new endpoints in `main.py`
- Extend database schema for new features
- Integrate additional AI services

## 🚨 Notes

### Voice Input
- Uses Web Speech API (Chrome/Edge recommended)
- Requires microphone permissions
- Falls back to audio recording on unsupported browsers

### File Uploads
- Max file size handled by FastAPI defaults
- Supported types: images, PDFs, docs, text files
- Files are stored locally (consider cloud storage for production)

### Security
- No authentication implemented (add for production)
- Files are publicly accessible via URL
- Consider adding virus scanning for uploads

## 🐛 Troubleshooting

### Common Issues

**Server won't start:**
- Check if port 8000 is available
- Verify OpenAI API key is set
- Ensure virtual environment is activated

**Voice input not working:**
- Check browser compatibility (Chrome/Edge recommended)
- Grant microphone permissions
- Try refreshing the page

**File uploads failing:**
- Check file size limits
- Verify file types are supported
- Ensure uploads directory exists and is writable

**Frontend build errors:**
- Clear node_modules: `rm -rf node_modules && npm install`
- Check Node.js version compatibility
- Verify all dependencies are installed

## 📞 Support

For issues or questions:
1. Check the console for error messages
2. Verify all dependencies are installed
3. Ensure environment variables are set correctly
4. Test with simple text messages first before trying advanced features

---

Built with ❤️ using React, FastAPI, LangGraph, and OpenAI 