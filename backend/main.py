import os
import uuid
import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request, Response, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage
import shutil
import mimetypes
import base64
import json
from openai import OpenAI

try:
    # For Railway deployment (running from project root)
    from backend.workflow import build_travel_workflow
    from backend.auth import (
        init_auth_tables, UserCreate, UserLogin, UserResponse, OnboardingData,
        create_user, authenticate_user, create_access_token, get_current_user_from_token,
        get_or_create_anonymous_user, create_session, log_user_interaction,
        log_analytics_event, learn_from_user_behavior, get_user_learning_profile,
        security
    )
except ImportError:
    # For local development (running from backend directory)
    from workflow import build_travel_workflow
    from auth import (
        init_auth_tables, UserCreate, UserLogin, UserResponse, OnboardingData,
        create_user, authenticate_user, create_access_token, get_current_user_from_token,
        get_or_create_anonymous_user, create_session, log_user_interaction,
        log_analytics_event, learn_from_user_behavior, get_user_learning_profile,
        security
    )

# Load environment variables
load_dotenv()

app = FastAPI(title="Travel Chatbot Backend", version="0.1.0")

# Allow the React frontend to call the API from any origin during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create uploads directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Mount static files for serving uploaded files
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# NOTE: Static frontend mount moved to end of file to not interfere with API routes

# Initialize OpenAI client for image processing
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize database
def init_db():
    conn = sqlite3.connect('travel_chatbot.db')
    cursor = conn.cursor()
    
    # Existing tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS message_attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER,
            filename TEXT,
            original_name TEXT,
            file_path TEXT,
            file_type TEXT,
            file_size INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (message_id) REFERENCES messages (id)
        )
    ''')
    
    # New tables for user context
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            email TEXT UNIQUE,
            phone TEXT,
            date_of_birth DATE,
            nationality TEXT,
            passport_number TEXT,
            frequent_flyer_number TEXT,
            loyalty_tier TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            preference_type TEXT,
            preference_value TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            booking_type TEXT,
            status TEXT,
            confirmation_number TEXT,
            booking_date DATE,
            travel_date_start DATE,
            travel_date_end DATE,
            total_amount DECIMAL(10,2),
            currency TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS travel_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            destination TEXT,
            country TEXT,
            trip_purpose TEXT,
            trip_date DATE,
            duration_days INTEGER,
            rating INTEGER,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    
    # Initialize authentication tables
    try:
        init_auth_tables()
        print("✅ Authentication tables initialized")
    except Exception as e:
        print(f"⚠️  Auth tables already exist or error: {e}")

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_db()
    print("🚀 Travel Chatbot Backend started successfully!")

# Add user context functions after the init_db function
def get_user_context(user_id: str) -> dict:
    """Retrieve comprehensive user context for personalized responses"""
    conn = sqlite3.connect('travel_chatbot.db')
    cursor = conn.cursor()
    
    try:
        # Get user profile
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user_row = cursor.fetchone()
        if not user_row:
            return {"error": "User not found"}
        
        user_cols = [desc[0] for desc in cursor.description]
        user_profile = dict(zip(user_cols, user_row))
        
        # Get user preferences
        cursor.execute("SELECT preference_type, preference_value FROM user_preferences WHERE user_id = ?", (user_id,))
        preferences = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get recent travel history (last 5 trips)
        cursor.execute("""
            SELECT destination, country, trip_purpose, trip_date, duration_days, rating, notes 
            FROM travel_history WHERE user_id = ? 
            ORDER BY trip_date DESC LIMIT 5
        """, (user_id,))
        travel_history = []
        for row in cursor.fetchall():
            travel_history.append({
                'destination': row[0],
                'country': row[1],
                'trip_purpose': row[2],
                'trip_date': row[3],
                'duration_days': row[4],
                'rating': row[5],
                'notes': row[6]
            })
        
        # Get active bookings
        cursor.execute("""
            SELECT booking_type, status, confirmation_number, travel_date_start, 
                   travel_date_end, total_amount, currency, details 
            FROM bookings WHERE user_id = ? AND status IN ('confirmed', 'pending')
            ORDER BY travel_date_start
        """, (user_id,))
        active_bookings = []
        for row in cursor.fetchall():
            active_bookings.append({
                'booking_type': row[0],
                'status': row[1],
                'confirmation_number': row[2],
                'travel_date_start': row[3],
                'travel_date_end': row[4],
                'total_amount': row[5],
                'currency': row[6],
                'details': row[7]
            })
        
        return {
            'profile': user_profile,
            'preferences': preferences,
            'travel_history': travel_history,
            'active_bookings': active_bookings
        }
    
    finally:
        conn.close()

def format_user_context_for_ai(user_context: dict) -> str:
    """Format user context into a string for AI consumption"""
    if "error" in user_context:
        return "No user context available."
    
    profile = user_context['profile']
    preferences = user_context['preferences']
    travel_history = user_context['travel_history']
    active_bookings = user_context['active_bookings']
    
    context_str = f"""
USER PROFILE:
- Name: {profile['first_name']} {profile['last_name']}
- Email: {profile['email']}
- Nationality: {profile['nationality']}
- Loyalty Status: {profile.get('loyalty_tier', 'None')}
- Frequent Flyer: {profile.get('frequent_flyer_number', 'None')}

PREFERENCES:
"""
    
    for pref_type, pref_value in preferences.items():
        context_str += f"- {pref_type.replace('_', ' ').title()}: {pref_value}\n"
    
    if travel_history:
        context_str += "\nRECENT TRAVEL HISTORY:\n"
        for trip in travel_history:
            context_str += f"- {trip['destination']}, {trip['country']} ({trip['trip_date']}) - {trip['trip_purpose']}, {trip['duration_days']} days, rated {trip['rating']}/5\n"
    
    if active_bookings:
        context_str += "\nACTIVE BOOKINGS:\n"
        for booking in active_bookings:
            context_str += f"- {booking['booking_type'].title()}: {booking['confirmation_number']} ({booking['status']}) - {booking['travel_date_start']} to {booking['travel_date_end']}\n"
    
    return context_str

def format_user_context_for_ai_with_learning(enhanced_context: dict) -> str:
    """Format user context including learning data for AI consumption"""
    if "error" in enhanced_context:
        return "No user context available."
    
    # Get basic profile (existing logic)
    basic_context = format_user_context_for_ai(enhanced_context)
    
    # Add learning insights
    learning_data = enhanced_context.get('learned_preferences', {})
    interaction_patterns = enhanced_context.get('interaction_patterns', {})
    
    learning_insights = []
    
    # High-confidence learned preferences
    for pref_key, pref_data in learning_data.items():
        if isinstance(pref_data, dict) and pref_data.get('confidence', 0) > 0.7:
            learning_insights.append(f"- Learned preference: {pref_key} = {pref_data.get('value')}")
    
    # Interaction patterns
    if interaction_patterns:
        most_common = max(interaction_patterns.items(), key=lambda x: x[1])
        learning_insights.append(f"- Most common interaction: {most_common[0]} ({most_common[1]} times)")
    
    if learning_insights:
        learning_section = "\n\nLEARNED USER BEHAVIOR:\n" + "\n".join(learning_insights)
        return basic_context + learning_section
    
    return basic_context

def format_learning_insights(learning_profile: dict) -> str:
    """Format learning insights for AI prompt"""
    learned_prefs = learning_profile.get('learned_preferences', {})
    patterns = learning_profile.get('interaction_patterns', {})
    
    insights = []
    
    # High confidence preferences
    for key, data in learned_prefs.items():
        if isinstance(data, dict) and data.get('confidence', 0) > 0.6:
            insights.append(f"{key}: {data.get('value')} (confidence: {data.get('confidence'):.1f})")
    
    # Behavioral patterns
    if patterns:
        top_pattern = max(patterns.items(), key=lambda x: x[1])
        insights.append(f"Primary interaction type: {top_pattern[0]}")
    
    return "; ".join(insights) if insights else "No strong learned preferences yet"

def learn_from_conversation(user_id: str, user_message: str, ai_response: str):
    """Extract learning data from conversation"""
    learning_data = {}
    
    # Analyze user message for preferences
    message_lower = user_message.lower()
    
    # Travel style preferences
    if any(word in message_lower for word in ['luxury', 'premium', 'first class', 'high-end']):
        learning_data['preferred_travel_style'] = 'luxury'
    elif any(word in message_lower for word in ['budget', 'cheap', 'affordable', 'economy']):
        learning_data['preferred_travel_style'] = 'budget'
    elif any(word in message_lower for word in ['business', 'work', 'conference']):
        learning_data['preferred_travel_style'] = 'business'
    
    # Destination interests - expanded list
    destinations = ['paris', 'tokyo', 'japan', 'london', 'new york', 'rome', 'barcelona', 'amsterdam', 
                   'italy', 'france', 'spain', 'germany', 'australia', 'thailand', 'india', 'china']
    for dest in destinations:
        if dest in message_lower:
            learning_data['interested_destinations'] = dest
    
    # Travel companion patterns
    if any(word in message_lower for word in ['brother', 'sister', 'family', 'wife', 'husband', 'partner']):
        learning_data['travel_companion_type'] = 'family'
    elif any(word in message_lower for word in ['friend', 'friends', 'buddy']):
        learning_data['travel_companion_type'] = 'friends'
    elif any(word in message_lower for word in ['solo', 'alone', 'myself']):
        learning_data['travel_companion_type'] = 'solo'
    
    # Trip purpose
    if any(word in message_lower for word in ['vacation', 'holiday', 'leisure', 'fun', 'relax']):
        learning_data['trip_purpose'] = 'leisure'
    elif any(word in message_lower for word in ['business', 'work', 'conference', 'meeting']):
        learning_data['trip_purpose'] = 'business'
    elif any(word in message_lower for word in ['honeymoon', 'anniversary']):
        learning_data['trip_purpose'] = 'romantic'
    
    # Activity preferences
    if any(word in message_lower for word in ['museum', 'art', 'culture', 'history']):
        learning_data['activity_preference'] = 'cultural'
    elif any(word in message_lower for word in ['beach', 'relax', 'spa']):
        learning_data['activity_preference'] = 'relaxation'
    elif any(word in message_lower for word in ['adventure', 'hiking', 'extreme', 'sports']):
        learning_data['activity_preference'] = 'adventure'
    elif any(word in message_lower for word in ['shopping', 'mall', 'store']):
        learning_data['activity_preference'] = 'shopping'
    elif any(word in message_lower for word in ['food', 'restaurant', 'cuisine', 'dining']):
        learning_data['activity_preference'] = 'culinary'
    
    # Communication style
    if len(user_message) > 100:
        learning_data['communication_style'] = 'detailed'
    elif '?' in user_message:
        learning_data['communication_style'] = 'inquisitive'
    
    # Time preferences
    if any(word in message_lower for word in ['morning', 'early']):
        learning_data['time_preference'] = 'morning'
    elif any(word in message_lower for word in ['evening', 'night']):
        learning_data['time_preference'] = 'evening'
    
    # Save learning data
    if learning_data:
        learn_from_user_behavior(user_id, learning_data)

def get_simple_travel_response(user_message: str, current_user) -> str:
    """
    Simple travel assistant responses without OpenAI API calls
    """
    message_lower = user_message.lower()
    user_name = current_user.first_name if current_user.first_name else "there"
    
    # Flight searches
    if any(word in message_lower for word in ['flight', 'fly', 'plane', 'airline']):
        return f"""Hi {user_name}! I'd be happy to help you search for flights. 

To find the best flight options for you, I'll need a few details:
• Where would you like to fly from?
• What's your destination?
• When would you like to travel?
• How many passengers?

Once you provide these details, I can search for available flights with real-time prices and schedules!"""

    # Hotel searches
    elif any(word in message_lower for word in ['hotel', 'stay', 'accommodation', 'room']):
        return f"""Hi {user_name}! I can help you find great hotel options.

To search for the perfect accommodation, please let me know:
• Which city or area are you looking at?
• Check-in and check-out dates?
• Number of guests?
• Any preferences (budget, luxury, specific amenities)?

I'll find hotels that match your needs and budget!"""

    # Greetings
    elif any(word in message_lower for word in ['hi', 'hello', 'hey', 'good morning', 'good evening']):
        return f"""Hello {user_name}! Welcome to your personal travel assistant. I'm here to help you with all your travel needs:

✈️ **Flight Booking** - Search and book flights worldwide
🏨 **Hotel Reservations** - Find accommodations that fit your style
🌤️ **Weather Updates** - Get forecasts for your destinations  
🎒 **Travel Planning** - Tips and recommendations for your trips
📋 **Booking Management** - Modify or cancel existing reservations

What travel plans are you working on today?"""

    # General travel help
    elif any(word in message_lower for word in ['help', 'travel', 'trip', 'vacation', 'plan']):
        return f"""I'm here to help with your travel planning, {user_name}! Here's what I can assist you with:

🔍 **Search & Book:**
• Flights to any destination
• Hotels and accommodations
• Compare prices and options

📅 **Manage Bookings:**
• Reschedule flights or hotels
• Cancel reservations
• Check booking status

🌍 **Travel Information:**
• Weather forecasts
• Travel tips and recommendations
• Destination guides

What specific travel assistance do you need today?"""

    # Default helpful response
    else:
        return f"""Hi {user_name}! I'm your travel assistant, and I'm here to help you plan amazing trips!

I can assist you with flights, hotels, weather information, and travel planning. What would you like to help you with today?

Just tell me what you're looking for - like "I need a flight to Paris" or "Find me a hotel in Tokyo" - and I'll get started right away!"""

def extract_tools_from_response(response: str) -> list:
    """Extract which tools were likely used based on response content"""
    tools_used = []
    
    response_lower = response.lower()
    
    if any(word in response_lower for word in ['flight', 'airline', 'departure', 'arrival']):
        tools_used.append('search_flights')
    if any(word in response_lower for word in ['hotel', 'room', 'reservation', 'check-in']):
        tools_used.append('book_hotel')
    if any(word in response_lower for word in ['car rental', 'vehicle', 'rental']):
        tools_used.append('search_car_rentals')
    if any(word in response_lower for word in ['tour', 'activity', 'restaurant', 'show']):
        tools_used.append('book_activities')
    if any(word in response_lower for word in ['insurance', 'coverage', 'premium']):
        tools_used.append('get_travel_insurance')
    if any(word in response_lower for word in ['visa', 'passport', 'embassy']):
        tools_used.append('check_visa_requirements')
    if any(word in response_lower for word in ['currency', 'exchange', 'convert']):
        tools_used.append('convert_currency')
    if any(word in response_lower for word in ['weather', 'temperature', 'forecast']):
        tools_used.append('get_weather_forecast')
    if any(word in response_lower for word in ['alert', 'warning', 'advisory']):
        tools_used.append('get_travel_alerts')
    if any(word in response_lower for word in ['booking', 'confirmation', 'status']):
        tools_used.append('check_booking_status')
    if any(word in response_lower for word in ['recommendation', 'suggest', 'advice']):
        tools_used.append('get_travel_recommendations')
    if any(word in response_lower for word in ['cancel', 'modify', 'change']):
        tools_used.append('cancel_or_modify_booking')
    
    return tools_used

def save_message_with_attachments(conversation_id: str, role: str, content: str, attachments: list):
    """Save message with file attachments"""
    conn = sqlite3.connect('travel_chatbot.db')
    cursor = conn.cursor()
    
    # Save message
    cursor.execute('''
        INSERT INTO messages (conversation_id, role, content) VALUES (?, ?, ?)
    ''', (conversation_id, role, content))
    
    message_id = cursor.lastrowid
    
    # Save attachments
    for attachment in attachments:
        cursor.execute('''
            INSERT INTO message_attachments 
            (message_id, filename, original_name, file_path, file_type, file_size)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (message_id, attachment['filename'], attachment['original_name'],
              attachment['file_path'], attachment['file_type'], attachment['file_size']))
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Initialize LangChain components
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.7,
    api_key=os.getenv("OPENAI_API_KEY")
)

# Travel domain system prompt
TRAVEL_SYSTEM_PROMPT = """You are a helpful travel assistant specializing in hotel and flight bookings, rescheduling, and refund requests. 

Your capabilities include:
1. **Hotel Booking**: Help users find and book hotels based on location, dates, budget, and preferences
2. **Flight Booking**: Assist with flight searches and bookings for domestic and international travel
3. **Rescheduling**: Help modify existing bookings (flights, hotels, car rentals)
4. **Refund Requests**: Guide users through refund processes for cancellations

When users ask about bookings, rescheduling, or refunds:
- Ask for necessary details (dates, locations, booking references, etc.)
- Provide step-by-step guidance
- Offer to help them through the process
- Be friendly and professional

For actual bookings, explain the process and what information you'll need. For now, you're providing guidance and information rather than making actual bookings.

When users share images or files:
- Acknowledge that you've received the files
- If they appear to be travel-related documents (tickets, confirmations, etc.), offer to help with related questions
- Be helpful in interpreting any travel information they share
- If images contain text or travel documents, analyze and extract relevant information

Always be helpful, clear, and provide actionable next steps."""

prompt = ChatPromptTemplate.from_messages([
    ("system", TRAVEL_SYSTEM_PROMPT),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])

class ChatRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str

class ChatResponse(BaseModel):
    conversation_id: str
    response: str

def encode_image_to_base64(image_path: str) -> str:
    """Convert image file to base64 string"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_image_with_openai(image_path: str, user_message: str = "") -> str:
    """Analyze image using OpenAI's vision model"""
    try:
        # Encode image to base64
        base64_image = encode_image_to_base64(image_path)
        
        # Determine image format
        image_format = mimetypes.guess_type(image_path)[0] or "image/jpeg"
        
        # Create the vision prompt
        vision_prompt = f"""Analyze this image in the context of travel assistance. The user said: "{user_message}"

Please:
1. Describe what you see in the image
2. If it's a travel document (ticket, booking confirmation, receipt, etc.), extract key information like:
   - Booking references/confirmation numbers
   - Dates and times
   - Locations (airports, hotels, etc.)
   - Passenger/guest names
   - Prices or costs
   - Any issues or problems visible
3. Provide helpful travel assistance based on what you see
4. Suggest next steps if applicable

Be specific and helpful in your analysis."""

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": vision_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{image_format};base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        print(f"Error analyzing image: {e}")
        return f"I can see you've uploaded an image, but I'm having trouble analyzing it right now. Could you describe what's in the image or let me know how I can help with your travel needs?"

def get_conversation_user_id(conversation_id: str) -> Optional[str]:
    """Get the user_id associated with a conversation"""
    conn = sqlite3.connect('travel_chatbot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id FROM conversations WHERE id = ?
    ''', (conversation_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def create_welcome_message_for_user(user: UserResponse) -> str:
    """Create a concise welcome message listing chatbot capabilities"""
    first_name = user.first_name or "Traveler"
    return (
        f"Hello {first_name}! I'm your personal travel assistant. I can help you with:\n"
        f"• Booking flights and hotels\n"
        f"• Rescheduling existing bookings\n"
        f"• Requesting refunds or cancellations\n\n"
        f"How can I assist you today?"
    )

def get_user_context_with_welcome(user_id: str) -> dict:
    """Get user context and determine if welcome message is needed"""
    # Get basic user context
    user_context = get_user_context(user_id)
    
    # Check if user has had conversations before
    conn = sqlite3.connect('travel_chatbot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM conversations 
        WHERE user_id = ?
    ''', (user_id,))
    conversation_count = cursor.fetchone()[0]
    conn.close()
    
    # Add welcome flag if this is their first conversation
    user_context['is_first_conversation'] = conversation_count == 0
    return user_context

def get_conversation_history(conversation_id: str) -> List[dict]:
    """Retrieve conversation history from database"""
    conn = sqlite3.connect('travel_chatbot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT role, content FROM messages 
        WHERE conversation_id = ? 
        ORDER BY timestamp ASC
    ''', (conversation_id,))
    messages = cursor.fetchall()
    conn.close()
    
    history = []
    for role, content in messages:
        if role == "user":
            history.append(HumanMessage(content=content))
        elif role == "assistant":
            history.append(AIMessage(content=content))
    
    return history

def save_message(conversation_id: str, role: str, content: str) -> int:
    """Save a message to the database and return the message ID"""
    conn = sqlite3.connect('travel_chatbot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO messages (conversation_id, role, content)
        VALUES (?, ?, ?)
    ''', (conversation_id, role, content))
    message_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return message_id

def save_attachment(message_id: int, filename: str, original_name: str, file_path: str, file_type: str, file_size: int):
    """Save file attachment information to database"""
    conn = sqlite3.connect('travel_chatbot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO message_attachments 
        (message_id, filename, original_name, file_path, file_type, file_size)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (message_id, filename, original_name, file_path, file_type, file_size))
    conn.commit()
    conn.close()

def create_conversation_for_user(user_id: str) -> str:
    """Create a new conversation for a specific user and return its ID"""
    conversation_id = str(uuid.uuid4())
    
    conn = sqlite3.connect('travel_chatbot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO conversations (id, user_id) VALUES (?, ?)
    ''', (conversation_id, user_id))
    conn.commit()
    conn.close()
    return conversation_id

# Authentication helper function (moved here to be available for chat endpoints)
async def get_current_user(request: Request, authorization: Optional[str] = Header(None)) -> Optional[UserResponse]:
    """Get current user from token or create anonymous user"""
    print(f"DEBUG: Authorization header: {authorization}")
    
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        print(f"DEBUG: Token found: {token[:20]}...")
        user = get_current_user_from_token(token)
        if user:
            print(f"DEBUG: Authenticated user found: {user.email}")
            return user
        else:
            print("DEBUG: Token validation failed")
    else:
        print("DEBUG: No authorization header or invalid format")
    
    # Create or get anonymous user
    print("DEBUG: Creating anonymous user")
    anonymous_user_id = get_or_create_anonymous_user(request)
    return UserResponse(
        id=anonymous_user_id,
        email=f"anon_{anonymous_user_id[:8]}@temp.com",
        first_name="Anonymous",
        last_name="User",
        nationality=None,
        created_at=datetime.now().isoformat(),
        is_demo_user=False
    )

# Add global conversation rate limiting
_last_conversation_call = 0
_conversation_call_interval = 3.0  # 3 seconds between conversation API calls
_daily_conversation_count = 0
_last_conversation_reset = None
_max_daily_conversations = 20  # Maximum 20 conversation API calls per day

def _check_conversation_quota() -> tuple[bool, str]:
    """Check if we can make a conversation API call"""
    global _daily_conversation_count, _last_conversation_reset, _last_conversation_call
    import time
    from datetime import datetime
    
    # Reset daily count
    today = datetime.now().date()
    if _last_conversation_reset != today:
        _daily_conversation_count = 0
        _last_conversation_reset = today
    
    # Check daily limit
    if _daily_conversation_count >= _max_daily_conversations:
        return False, "Daily conversation limit reached. The AI assistant has reached its daily capacity. Please try again tomorrow."
    
    # Check rate limiting
    time_since_last = time.time() - _last_conversation_call
    if time_since_last < _conversation_call_interval:
        wait_time = _conversation_call_interval - time_since_last
        return False, f"Please wait {wait_time:.1f} seconds before sending another message. This helps manage API usage."
    
    return True, ""

def _record_conversation_call():
    """Record that we made a conversation API call"""
    global _daily_conversation_count, _last_conversation_call
    import time
    _daily_conversation_count += 1
    _last_conversation_call = time.time()
    print(f"📊 Conversation API call #{_daily_conversation_count}/20 today")

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest, request: Request, current_user: UserResponse = Depends(get_current_user)):
    """Chat endpoint that processes user messages and returns AI responses with learning"""
    if not payload.message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Check conversation quota BEFORE making any API calls
    can_proceed, quota_message = _check_conversation_quota()
    if not can_proceed:
        return ChatResponse(
            conversation_id=payload.conversation_id or "quota_limited", 
            response=quota_message
        )

    # Get or create conversation ID
    conversation_id = payload.conversation_id
    if not conversation_id:
        conversation_id = create_conversation_for_user(current_user.id)

    # Get conversation history
    history = get_conversation_history(conversation_id)

    # Get user context with learning - now uses real user data or learned preferences
    user_context = get_user_context_with_welcome(current_user.id)
    learning_profile = get_user_learning_profile(current_user.id)
    
    # Check if this is a new conversation and user is truly new (not just new conversation)
    if len(history) == 0:
        # Check if user has had previous conversations
        conn = sqlite3.connect('travel_chatbot.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM conversations WHERE user_id = ?
        ''', (current_user.id,))
        conversation_count = cursor.fetchone()[0]
        conn.close()
        
        # Only send welcome message for truly new users (first ever conversation)
        if conversation_count <= 1:  # This is their first conversation
            welcome_message = create_welcome_message_for_user(current_user)
            
            # Save welcome message to history
            save_message(conversation_id, "assistant", welcome_message)
            
            # Add welcome message to history for this conversation
            history.append({"role": "assistant", "content": welcome_message})
            
            # Log welcome event
            log_analytics_event(current_user.id, "welcome_message_sent", {
                "user_type": "registered" if not current_user.email.startswith("anon_") else "anonymous",
                "is_first_time": True
            })
        # For returning users starting new conversations, don't send welcome message
    
    # Combine real user data with learned preferences
    enhanced_context = {**user_context, **learning_profile}
    context_str = format_user_context_for_ai_with_learning(enhanced_context)

    # Log user interaction for learning
    log_user_interaction(current_user.id, "chat_message", {
        "message": payload.message,
        "conversation_id": conversation_id,
        "message_length": len(payload.message),
        "has_context": bool(user_context and "error" not in user_context)
    })

    # Build or reuse LangGraph workflow
    workflow = build_travel_workflow(os.getenv("OPENAI_API_KEY"))

    # Enhance message with user context and learning data
    enhanced_message = f"""{payload.message}

--- USER CONTEXT ---
{context_str}

--- LEARNING PROFILE ---
Based on past interactions, the user has shown preferences for:
{format_learning_insights(learning_profile)}

--- CONVERSATION CONTEXT ---
This is {'a new' if len(history) <= 1 else 'an ongoing'} conversation. {'The user is a returning customer.' if len(history) > 1 else 'This may be their first interaction.'}

--- CRITICAL INSTRUCTIONS ---
You are a professional human travel agent having a natural conversation. Follow these rules:

1. NEVER send welcome messages to returning users - if this is an ongoing conversation, continue naturally
2. ALWAYS respect user choices - if they say "option 3", use exactly option 3 from your previous search results  
3. MAINTAIN context throughout conversation - remember departure cities, travel companions, dates
4. When user corrects information (like departure city), acknowledge and use the correct information
5. Use search_flights tool to show options, then book_flight tool with exact option number when user chooses
6. Don't make up flight data - use tools to get consistent information
7. Remember travel companions mentioned (brother, family) for all bookings
8. Be specific and accurate - no generic or inconsistent details
9. For returning users: acknowledge you remember them briefly, then focus on their current request
10. Ask clarifying questions when needed, but prioritize taking action on clear requests
11. No markdown formatting - write in natural flowing paragraphs

EXAMPLE OF CORRECT BEHAVIOR:
New user: "help me book flight" → Ask for departure, destination, dates
Returning user: "help me book flight" → "I can help you with that! Where would you like to fly from and to?"

User: "option 3" → Use book_flight tool with option_number="3" for the exact flight they chose

Respond as a knowledgeable, efficient, and friendly human travel agent who pays attention to details and follows user instructions precisely."""

    # Prepare initial state
    initial_state = {
        "messages": history + [HumanMessage(content=enhanced_message)]
    }

    try:
        # Record that we're making a conversation API call
        _record_conversation_call()
        
        result_state = workflow.invoke(initial_state)
        final_msg = result_state["messages"][-1]
        ai_response = final_msg.content if isinstance(final_msg, (AIMessage,)) else str(final_msg)

        # Save both user message and AI response
        save_message(conversation_id, "user", payload.message)
        save_message(conversation_id, "assistant", ai_response)

        # Extract learning data from the conversation
        learn_from_conversation(current_user.id, payload.message, ai_response)

        # Log analytics
        log_analytics_event(current_user.id, "chat_completion", {
            "response_length": len(ai_response),
            "conversation_id": conversation_id,
            "tools_used": extract_tools_from_response(ai_response),
            "user_type": "registered" if not current_user.is_demo_user else "anonymous"
        })

        # FIXED: Don't combine welcome messages - just return the AI response
        return ChatResponse(conversation_id=conversation_id, response=ai_response)
    
    except Exception as e:
        error_str = str(e)
        print(f"Error generating response: {e}")
        
        # Check if it's a rate limit error
        is_rate_limit = "429" in error_str or "quota" in error_str.lower() or "rate limit" in error_str.lower()
        
        # Log error for debugging
        log_analytics_event(current_user.id, "chat_error", {
            "error": error_str,
            "conversation_id": conversation_id,
            "is_rate_limit": is_rate_limit
        })
        
        # Provide specific error messages for rate limits
        if is_rate_limit:
            error_response = "I'm experiencing high demand right now. Please wait a few seconds and try again. The AI-powered travel tools have built-in rate limiting to ensure quality service."
        else:
            error_response = "I apologize, but I'm having trouble processing your request right now. Please try again in a moment."
            
        return ChatResponse(conversation_id=conversation_id, response=error_response)

@app.post("/chat-with-files", response_model=ChatResponse)
async def chat_with_files_endpoint(
    message: str = Form(...),
    conversation_id: Optional[str] = Form(None),
    files: List[UploadFile] = File(default=[]),
    request: Request = None,
    current_user: UserResponse = Depends(get_current_user)
):
    """Enhanced chat endpoint with file uploads and user learning"""
    
    # Get or create conversation ID
    if not conversation_id:
        conversation_id = create_conversation_for_user(current_user.id)

    # Process uploaded files
    file_descriptions = []
    saved_files = []
    image_analyses = []
    
    for file in files:
        if file.filename:
            # Generate unique filename
            file_extension = os.path.splitext(file.filename)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = os.path.join(UPLOAD_DIR, unique_filename)
            
            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Get file info
            file_size = os.path.getsize(file_path)
            file_type = mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
            
            saved_files.append({
                "filename": unique_filename,
                "original_name": file.filename,
                "file_path": file_path,
                "file_type": file_type,
                "file_size": file_size
            })
            
            # Add to message description and analyze if it's an image
            if file_type.startswith('image/'):
                file_descriptions.append(f"📷 Image: {file.filename}")
                # Analyze image with OpenAI Vision
                try:
                    analysis = analyze_image_with_openai(file_path, message)
                    image_analyses.append(f"\n📷 Analysis of {file.filename}:\n{analysis}")
                except Exception as e:
                    print(f"Error analyzing image {file.filename}: {e}")
                    image_analyses.append(f"\n📷 Image {file.filename} uploaded but couldn't be analyzed.")
            else:
                file_descriptions.append(f"📄 File: {file.filename}")

    # Get user context for this conversation
    user_id = get_conversation_user_id(conversation_id)
    user_context = get_user_context(user_id) if user_id else {}
    context_str = format_user_context_for_ai(user_context)

    # Enhance message with file information, image analyses, and user context
    enhanced_message = message
    if file_descriptions:
        enhanced_message += f"\n\nAttached files:\n" + "\n".join(file_descriptions)
    
    # Add user context
    enhanced_message += f"\n\n--- USER CONTEXT ---\n{context_str}"
    
    # Add image analyses to the message
    if image_analyses:
        enhanced_message += "\n\n" + "\n".join(image_analyses)

    # Get conversation history
    history = get_conversation_history(conversation_id)

    # Build workflow
    workflow = build_travel_workflow(os.getenv("OPENAI_API_KEY"))

    # Prepare initial state
    initial_state = {
        "messages": history + [HumanMessage(content=enhanced_message)]
    }

    try:
        result_state = workflow.invoke(initial_state)
        final_msg = result_state["messages"][-1]
        ai_response = final_msg.content if isinstance(final_msg, (AIMessage,)) else str(final_msg)

        # Save user message
        user_message_id = save_message(conversation_id, "user", message)
        
        # Save file attachments
        for file_info in saved_files:
            save_attachment(
                user_message_id,
                file_info["filename"],
                file_info["original_name"],
                file_info["file_path"],
                file_info["file_type"],
                file_info["file_size"]
            )

        # Save AI response
        save_message(conversation_id, "assistant", ai_response)

        return ChatResponse(conversation_id=conversation_id, response=ai_response)
    
    except Exception as e:
        print(f"Error generating response: {e}")
        # Clean up uploaded files on error
        for file_info in saved_files:
            try:
                os.remove(file_info["file_path"])
            except:
                pass
        
        error_response = "I apologize, but I'm having trouble processing your request right now. Please try again in a moment."
        return ChatResponse(conversation_id=conversation_id, response=error_response)

@app.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/conversations/{conversation_id}/history")
async def get_conversation_history_endpoint(conversation_id: str):
    """Get the full history of a conversation"""
    conn = sqlite3.connect('travel_chatbot.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT role, content, timestamp FROM messages 
        WHERE conversation_id = ? 
        ORDER BY timestamp ASC
    ''', (conversation_id,))
    messages = cursor.fetchall()
    conn.close()
    
    return {
        "conversation_id": conversation_id,
        "messages": [
            {"role": role, "content": content, "timestamp": timestamp}
            for role, content, timestamp in messages
        ]
    } 

# Authentication Endpoints
@app.post("/auth/register", response_model=dict)
async def register_user(user_data: UserCreate, request: Request):
    """Register a new user account"""
    try:
        user = create_user(user_data)
        
        # Create access token
        access_token = create_access_token(data={"sub": user.id})
        
        # Create session
        session_token = create_session(user.id, request)
        
        # Log registration event
        log_analytics_event(user.id, "user_registered", {
            "email": user.email,
            "nationality": user.nationality,
            "registration_time": datetime.now().isoformat()
        })
        
        return {
            "message": "User registered successfully",
            "user": user,
            "access_token": access_token,
            "token_type": "bearer"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/login", response_model=dict)
async def login_user(user_login: UserLogin, request: Request):
    """Login user with email and password"""
    user = authenticate_user(user_login.email, user_login.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create access token
    access_token = create_access_token(data={"sub": user.id})
    
    # Create session
    session_token = create_session(user.id, request)
    
    # Log login event
    log_analytics_event(user.id, "user_login", {
        "email": user.email,
        "login_time": datetime.now().isoformat()
    })
    
    return {
        "message": "Login successful",
        "user": user,
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.get("/auth/me")
async def get_current_user_info(authorization: Optional[str] = Header(None)):
    """Get current authenticated user info - for token validation"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No valid authorization header")
    
    token = authorization.split(" ")[1]
    user = get_current_user_from_token(token)
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user

@app.post("/auth/onboarding")
async def complete_onboarding(
    onboarding_data: OnboardingData,
    current_user: UserResponse = Depends(get_current_user)
):
    """Complete user onboarding with travel preferences"""
    try:
        conn = sqlite3.connect('travel_chatbot.db')
        cursor = conn.cursor()
        
        # Save travel preferences
        for pref_type, pref_value in onboarding_data.travel_preferences.items():
            cursor.execute('''
                INSERT OR REPLACE INTO user_preferences (user_id, preference_type, preference_value)
                VALUES (?, ?, ?)
            ''', (current_user.id, pref_type, str(pref_value)))
        
        # Save additional onboarding data
        for destination in onboarding_data.frequent_destinations:
            cursor.execute('''
                INSERT INTO user_preferences (user_id, preference_type, preference_value)
                VALUES (?, ?, ?)
            ''', (current_user.id, "frequent_destination", destination))
        
        conn.commit()
        conn.close()
        
        # Log onboarding completion
        log_analytics_event(current_user.id, "onboarding_completed", {
            "travel_style": onboarding_data.travel_style,
            "budget_range": onboarding_data.budget_range,
            "preferences_count": len(onboarding_data.travel_preferences)
        })
        
        return {"message": "Onboarding completed successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user/profile")
async def get_user_profile(current_user: UserResponse = Depends(get_current_user)):
    """Get user profile with preferences and learning data"""
    try:
        # Get user context (existing function)
        user_context = get_user_context(current_user.id)
        
        # Get learning profile
        learning_profile = get_user_learning_profile(current_user.id)
        
        return {
            "user": current_user,
            "context": user_context,
            "learning_profile": learning_profile
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/dashboard")
async def get_analytics_dashboard():
    """Get analytics dashboard data (admin endpoint)"""
    try:
        conn = sqlite3.connect('travel_chatbot.db')
        cursor = conn.cursor()
        
        # User stats
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_demo_user = FALSE")
        real_users_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_demo_user = TRUE")
        demo_users_count = cursor.fetchone()[0]
        
        # Interaction stats
        cursor.execute("""
            SELECT interaction_type, COUNT(*) as count 
            FROM user_interactions 
            GROUP BY interaction_type 
            ORDER BY count DESC
        """)
        interaction_stats = dict(cursor.fetchall())
        
        # Popular tools
        cursor.execute("""
            SELECT 
                JSON_EXTRACT(interaction_data, '$.tool_name') as tool_name,
                COUNT(*) as usage_count
            FROM user_interactions 
            WHERE interaction_type = 'tool_usage'
            GROUP BY tool_name
            ORDER BY usage_count DESC
        """)
        tool_usage = dict(cursor.fetchall())
        
        # Recent activity
        cursor.execute("""
            SELECT event_type, COUNT(*) as count
            FROM user_analytics
            WHERE timestamp > datetime('now', '-7 days')
            GROUP BY event_type
            ORDER BY count DESC
        """)
        recent_activity = dict(cursor.fetchall())
        
        conn.close()
        
        return {
            "user_stats": {
                "real_users": real_users_count,
                "demo_users": demo_users_count,
                "total_users": real_users_count + demo_users_count
            },
            "interaction_stats": interaction_stats,
            "tool_usage": tool_usage,
            "recent_activity": recent_activity
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount the built React frontend LAST so it doesn't interfere with API routes
import pathlib
frontend_dist_path = pathlib.Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist_path), html=True), name="static") 