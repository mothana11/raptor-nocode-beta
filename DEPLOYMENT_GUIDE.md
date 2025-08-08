# 🚀 Travel Chatbot Demo Deployment Guide

## Quick Start for Colleagues

### Option 1: Replit Demo (Recommended)
1. **Visit the Replit**: [Your Replit URL will be here]
2. **Click "Run"** - The server will start automatically
3. **Access the demo**: The frontend will be available at the Replit URL
4. **Test the chatbot**: Try these demo messages:
   - "Hi" - Basic greeting
   - "Search for flights from New York to London" - Flight search
   - "Find hotels in Paris" - Hotel search
   - "Help me plan a trip to Tokyo" - Trip planning

### Option 2: Local Setup
1. **Clone the repository**:
   ```bash
   git clone https://github.com/mothana11/raptor-nocode-beta.git
   cd raptor-nocode-beta
   ```

2. **Set up environment**:
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure API keys** (optional for demo):
   ```bash
   cp .env.example .env
   # Edit .env with your API keys if needed
   ```

4. **Start the server**:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

5. **Access the demo**: http://localhost:8000

## Demo Features

### 🤖 AI-Powered Travel Assistant
- **Natural Language Understanding**: No hardcoded patterns, pure AI intelligence
- **Real API Integration**: Amadeus for flights, Booking.com for hotels
- **Smart Tool Selection**: AI decides when to use tools vs. respond conversationally

### ✈️ Flight Features
- Search real flights with live pricing
- Filter by dates, passengers, airlines
- Get detailed flight information
- Mock booking confirmations

### 🏨 Hotel Features
- Search real hotels with availability
- Filter by location, dates, guests
- Get hotel details and amenities
- Mock booking confirmations

### 📋 Trip Planning
- Create custom itineraries
- Manage bookings and reservations
- Get travel recommendations

## Demo Script

### Basic Interaction
```
User: "Hi"
Bot: "Hello! How can I assist you today?"
```

### Flight Search
```
User: "I need a flight from New York to London next week"
Bot: [Searches real flights via Amadeus API and presents options]
```

### Hotel Search
```
User: "Find me hotels in Paris for next month"
Bot: [Searches real hotels via Booking.com API and presents options]
```

### Trip Planning
```
User: "Help me plan a trip to Tokyo"
Bot: [Provides comprehensive travel planning assistance]
```

## Technical Architecture

### Backend (FastAPI + Python)
- **Intelligent Workflow**: LangGraph-based AI workflow
- **Real APIs**: Amadeus (flights), Booking.com (hotels)
- **Authentication**: JWT-based user management
- **Database**: SQLite with user profiles and booking history

### Frontend (React + TypeScript)
- **Modern UI**: Clean, responsive design
- **Real-time Chat**: WebSocket-based chat interface
- **User Management**: Login/registration system
- **Booking Management**: View and manage reservations

### AI Features
- **LLM-Powered**: GPT-4 for natural language understanding
- **Tool Integration**: Smart tool selection based on user intent
- **Context Awareness**: Maintains conversation context
- **Error Handling**: Graceful error recovery

## API Endpoints

### Core Endpoints
- `POST /chat` - Main chat interface
- `GET /health` - System health check
- `POST /auth/login` - User authentication
- `GET /auth/me` - Get current user

### Travel APIs
- `GET /api/flights/search` - Search flights
- `GET /api/hotels/search` - Search hotels
- `POST /api/bookings` - Create bookings

## Demo Tips

1. **Start Simple**: Begin with "Hi" to show basic functionality
2. **Show Real Data**: Demonstrate actual flight/hotel searches
3. **Highlight AI**: Point out natural language understanding
4. **Show Integration**: Demonstrate real API calls
5. **Error Handling**: Show graceful error recovery

## Troubleshooting

### Common Issues
- **API Rate Limits**: If you hit rate limits, the system gracefully handles it
- **Network Issues**: The system retries failed requests
- **Missing Data**: AI asks for clarification when information is incomplete

### Support
- Check the logs in the Replit console for detailed error information
- The system provides user-friendly error messages
- All errors are logged for debugging

## Next Steps

1. **Deploy to Replit**: Use the existing configuration
2. **Share the URL**: Send the Replit URL to your colleagues
3. **Demo the Features**: Walk through the key capabilities
4. **Gather Feedback**: Collect input for improvements

---

**Ready for Demo! 🎉**
Your travel chatbot is now ready to impress your colleagues with its AI-powered travel assistance capabilities. 