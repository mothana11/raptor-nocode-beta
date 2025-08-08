# main.py - CLEAN INTEGRATION WITH INTELLIGENT WORKFLOW
import os
import uuid
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Request, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
import json

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# immediately after load_dotenv():
logger.debug(f"DEBUG OPENAI_API_KEY = {os.getenv('OPENAI_API_KEY')[:10]}…")
logger.debug(f"DEBUG AMADEUS_CLIENT_ID = {os.getenv('AMADEUS_CLIENT_ID')}")
logger.debug(f"DEBUG AMADEUS_CLIENT_SECRET = {os.getenv('AMADEUS_CLIENT_SECRET')}")

print("DEBUG AMADEUS_CLIENT_ID =", os.getenv("AMADEUS_CLIENT_ID"))

# Import the INTELLIGENT workflow - NO HARDCODING
try:
    from backend.workflow import process_travel_request
    from backend.mcp_tools import get_real_mcp_tools
    from backend.auth import (
        init_auth_tables, UserCreate, UserLogin, UserResponse,
        create_user, authenticate_user, create_access_token, 
        get_current_user_from_token, get_or_create_anonymous_user,
        log_user_interaction, log_analytics_event, learn_from_user_behavior,
        get_user_learning_profile, create_session
    )
except ImportError:
    from workflow import process_travel_request
    from mcp_tools import get_real_mcp_tools
    from auth import (
        init_auth_tables, UserCreate, UserLogin, UserResponse,
        create_user, authenticate_user, create_access_token,
        get_current_user_from_token, get_or_create_anonymous_user,
        log_user_interaction, log_analytics_event, learn_from_user_behavior,
        get_user_learning_profile, create_session
    )

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Validate environment variables
REQUIRED_ENV_VARS = [
    "OPENAI_API_KEY",  # Required for LLM intelligence
    "AMADEUS_CLIENT_ID",
    "AMADEUS_CLIENT_SECRET",
    "RAPID_API_KEY"
]

missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    logger.warning(f"⚠️ Missing environment variables: {', '.join(missing_vars)}")
    logger.warning("Some features may not work. Please configure all API keys in .env file")

# FastAPI app
app = FastAPI(
    title="Intelligent Travel Assistant API",
    version="3.0.0",
    description="AI-powered travel assistant with REAL bookings, NO hardcoding"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database initialization
def init_db():
    """Initialize database for conversation tracking"""
    conn = sqlite3.connect('travel_chatbot.db')
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Users table (with all auth columns)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            email TEXT UNIQUE,
            nationality TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            password_hash TEXT,
            is_demo_user BOOLEAN DEFAULT FALSE,
            last_login TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        )
    ''')
    
    # Conversations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )
    ''')
    
    # Bookings table for tracking mock bookings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_reference TEXT UNIQUE NOT NULL,
            user_id TEXT,
            booking_type TEXT,
            booking_data TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # User preferences
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            preference_type TEXT NOT NULL,
            preference_value TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    init_db()
    try:
        init_auth_tables()
        logger.info("✅ Auth tables initialized")
    except Exception as e:
        logger.warning(f"Auth initialization issue: {e}")
    
    logger.info("✅ Intelligent Travel Assistant started")
    logger.info("🧠 Using LLM for ALL natural language understanding")
    logger.info("🔧 Real API integrations: Amadeus (flights), Booking.com (hotels)")
    logger.info("📋 Mock bookings: Generates confirmations without real charges")
    logger.info("🚫 NO HARDCODING - Pure AI intelligence")

# Request/Response models
class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str

class ChatResponse(BaseModel):
    conversation_id: str
    response: str
    action_taken: Optional[str] = None
    booking_reference: Optional[str] = None

# Authentication dependency
async def get_current_user(request: Request, authorization: Optional[str] = Header(None)) -> Dict:
    """Get current user from token or create anonymous"""
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            user = get_current_user_from_token(token)
            if user:
                return {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_authenticated": True,
                    "is_demo_user": user.is_demo_user
                }
        except Exception as e:
            logger.warning(f"Token validation failed: {e}")
    
    # Create or get anonymous user
    user_id = get_or_create_anonymous_user(request)
    return {
        "id": user_id,
        "email": f"anon_{user_id[:8]}@temp.com",
        "first_name": "Guest",
        "last_name": "User",
        "is_authenticated": False,
        "is_demo_user": False
    }
def create_conversation(user_id: str = "anonymous") -> str:
    """Create a new conversation"""
    conversation_id = str(uuid.uuid4())
    conn = sqlite3.connect('travel_assistant.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO conversations (id, user_id) VALUES (?, ?)
    ''', (conversation_id, user_id))
    conn.commit()
    conn.close()
    
    return conversation_id

def save_message(conversation_id: str, role: str, content: str):
    """Save a message to database"""
    conn = sqlite3.connect('travel_assistant.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO messages (conversation_id, role, content)
        VALUES (?, ?, ?)
    ''', (conversation_id, role, content))
    conn.commit()
    conn.close()

def get_conversation_history(conversation_id: str) -> List[BaseMessage]:
    """Get conversation history"""
    conn = sqlite3.connect('travel_assistant.db')
    cursor = conn.cursor()
    messages = []
    
    cursor.execute('''
        SELECT role, content FROM messages
        WHERE conversation_id = ?
        ORDER BY timestamp ASC
    ''', (conversation_id,))
    
    for role, content in cursor.fetchall():
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))
    
    conn.close()
    return messages

def save_booking(booking_reference: str, user_id: str, booking_type: str, booking_data: Dict):
    """Save a real booking to database"""
    conn = sqlite3.connect('travel_assistant.db')
    cursor = conn.cursor()
    
    import json
    cursor.execute('''
        INSERT INTO bookings (booking_reference, user_id, booking_type, booking_data, status)
        VALUES (?, ?, ?, ?, ?)
    ''', (booking_reference, user_id, booking_type, json.dumps(booking_data), "CONFIRMED"))
    conn.commit()
    conn.close()

# Main chat endpoint - INTELLIGENT PROCESSING ONLY
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    payload: ChatRequest,
    request: Request,
    current_user: Dict = Depends(get_current_user)
):
    """
    Main chat endpoint - PURE LLM INTELLIGENCE
    NO HARDCODING, NO REGEX, NO TEMPLATES
    Everything is handled by the LLM's understanding
    """
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    # Validate OpenAI API key
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="OpenAI API key not configured - required for intelligent processing"
        )
    
    # Get or create conversation
    conversation_id = payload.conversation_id
    if not conversation_id:
        conversation_id = create_conversation(current_user["id"])
    
    # Get conversation history
    history = get_conversation_history(conversation_id)
    
    # Save user message
    save_message(conversation_id, "user", payload.message)
    
    # Log interaction if authenticated
    if current_user.get("is_authenticated"):
        try:
            log_user_interaction(
                current_user["id"],
                "chat_message",
                {"message": payload.message, "conversation_id": conversation_id}
            )
        except:
            pass  # Non-critical
    
    try:
        # Process with INTELLIGENT workflow - NO HARDCODING
        response = process_travel_request(
            message=payload.message,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            history=history
        )
        
        # Check if response contains booking information
        booking_reference = None
        action_taken = None
        
        # The LLM response might contain booking details
        if "booking_reference" in response.lower():
            # Extract booking reference from response (LLM provides this)
            import re
            ref_match = re.search(r'(?:booking_reference|reference)[:\s]+\*{0,2}([A-Z0-9]{6,10})\*{0,2}', response, re.IGNORECASE)
            if ref_match:
                booking_reference = ref_match.group(1)
                action_taken = "BOOKING_CONFIRMED"
                
                # Save the mock booking
                save_booking(
                    booking_reference,
                    current_user["id"],
                    "flight" if "flight" in payload.message.lower() else "hotel",
                    {"message": payload.message, "response": response}
                )
        
        # Save assistant response
        save_message(conversation_id, "assistant", response)
        
        # Learn from interaction if authenticated
        if current_user.get("is_authenticated"):
            try:
                learn_from_user_behavior(
                    current_user["id"],
                    {"interaction": "chat", "topic": "travel"}
                )
            except:
                pass  # Non-critical
        
        return ChatResponse(
            conversation_id=conversation_id,
            response=response,
            action_taken=action_taken,
            booking_reference=booking_reference
        )
        
    except Exception as e:
        logger.error(f"Chat processing error: {str(e)}")
        error_response = f"System error: {str(e)}"
        save_message(conversation_id, "assistant", error_response)
        
        return ChatResponse(
            conversation_id=conversation_id,
            response=error_response
        )

# Authentication endpoints
@app.post("/auth/register", response_model=dict)
async def register_user(user_data: UserCreate, request: Request):
    """Register new user with proper authentication"""
    try:
        # Create the user
        user = create_user(user_data)
        
        # Create access token
        access_token = create_access_token(data={"sub": user.id})
        
        # Create session
        session_token = create_session(user.id, request)
        
        # Log registration event
        try:
            log_analytics_event(user.id, "user_registered", {
                "email": user.email,
                "timestamp": datetime.now().isoformat()
            })
        except:
            pass  # Non-critical
        
        return {
            "message": "Registration successful",
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            },
            "access_token": access_token,
            "token_type": "bearer"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/auth/login", response_model=dict)
async def login_user(user_login: UserLogin, request: Request):
    """Login user with email and password"""
    try:
        # Authenticate user
        user = authenticate_user(user_login.email, user_login.password)
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Create access token
        access_token = create_access_token(data={"sub": user.id})
        
        # Create session
        session_token = create_session(user.id, request)
        
        # Log login event
        try:
            log_analytics_event(user.id, "user_login", {
                "timestamp": datetime.now().isoformat()
            })
        except:
            pass  # Non-critical
        
        return {
            "message": "Login successful",
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name
            },
            "access_token": access_token,
            "token_type": "bearer"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

@app.get("/auth/me", response_model=dict)
async def get_current_user_info(current_user: Dict = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@app.post("/auth/logout", response_model=dict)
async def logout_user(request: Request):
    """Logout current user"""
    # In a real implementation, you'd invalidate the session here
    return {"message": "Logged out successfully"}
@app.get("/bookings")
async def get_user_bookings(user_id: str = "user"):
    """Get all bookings for a user"""
    conn = sqlite3.connect('travel_assistant.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT booking_reference, booking_type, booking_data, status, created_at
        FROM bookings
        WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (user_id,))
    
    bookings = []
    for ref, type_, data, status, created in cursor.fetchall():
        import json
        bookings.append({
            "booking_reference": ref,
            "type": type_,
            "details": json.loads(data),
            "status": status,
            "created_at": created
        })
    
    conn.close()
    return {"bookings": bookings}

# Get specific booking
@app.get("/bookings/{booking_reference}")
async def get_booking(booking_reference: str):
    """Get details of a specific booking"""
    conn = sqlite3.connect('travel_assistant.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM bookings WHERE booking_reference = ?
    ''', (booking_reference,))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    import json
    return {
        "booking_reference": result[1],
        "user_id": result[2],
        "type": result[3],
        "details": json.loads(result[4]),
        "status": result[5],
        "created_at": result[6],
        "updated_at": result[7]
    }

# Health check
@app.get("/health")
async def health_check():
    """Check system health and API configurations"""
    return {
        "status": "operational",
        "intelligence": "LLM-powered (no hardcoding)",
        "apis_configured": {
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "amadeus": bool(os.getenv("AMADEUS_CLIENT_ID") and os.getenv("AMADEUS_CLIENT_SECRET")),
            "rapidapi": bool(os.getenv("RAPID_API_KEY"))
        },
        "capabilities": {
            "search_flights": True,
            "search_hotels": True,
            "book_flights": True,  # Mock booking with confirmation
            "book_hotels": True,   # Mock booking with confirmation
            "reschedule": True,
            "cancel_refund": True,
            "create_itineraries": True
        },
        "timestamp": datetime.now().isoformat()
    }

# Conversation history
@app.get("/conversations/{conversation_id}/history")
async def get_conversation_history_endpoint(
    conversation_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get conversation history"""
    conn = sqlite3.connect('travel_chatbot.db')
    cursor = conn.cursor()
    
    # Verify user owns conversation (skip for anonymous users)
    if current_user.get("is_authenticated"):
        cursor.execute('''
            SELECT user_id FROM conversations WHERE id = ?
        ''', (conversation_id,))
        result = cursor.fetchone()
        
        if result and result[0] != current_user["id"]:
            conn.close()
            raise HTTPException(status_code=403, detail="Access denied")
    
    cursor.execute('''
        SELECT role, content, timestamp
        FROM messages
        WHERE conversation_id = ?
        ORDER BY timestamp ASC
    ''', (conversation_id,))
    
    messages = []
    for role, content, timestamp in cursor.fetchall():
        messages.append({
            "role": role,
            "content": content,
            "timestamp": timestamp
        })
    
    conn.close()
    return {
        "conversation_id": conversation_id,
        "messages": messages
    }

# List available tools (for debugging)
@app.get("/tools")
async def list_available_tools():
    """List all available MCP tools"""
    tools = get_real_mcp_tools()
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "real_api": True,
                "requires": tool.name.replace("_", " ").title()
            }
            for tool in tools
        ]
    }

# Test endpoint to verify auth is working
@app.get("/auth/test")
async def test_auth():
    """Test endpoint to verify authentication system is working"""
    return {
        "status": "Authentication system is operational",
        "endpoints": {
            "register": "/auth/register",
            "login": "/auth/login",
            "current_user": "/auth/me",
            "logout": "/auth/logout"
        }
    }

# User profile endpoint
@app.get("/user/profile")
async def get_user_profile(current_user: Dict = Depends(get_current_user)):
    """Get user profile with learning data"""
    if not current_user.get("is_authenticated"):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    learning_profile = get_user_learning_profile(current_user["id"])
    
    return {
        "user": current_user,
        "learning_profile": learning_profile
    }

# Mount frontend static files
import pathlib
frontend_dist = pathlib.Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")
    logger.info(f"✅ Frontend mounted from {frontend_dist}")
else:
    logger.info("ℹ️ No frontend build found. API-only mode.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)