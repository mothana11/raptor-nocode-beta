"""
Authentication and User Management System
Handles user registration, login, session management, and learning from user interactions
"""

import uuid
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import json
import hashlib

from fastapi import HTTPException, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
import secrets

# Configuration
SECRET_KEY = secrets.token_urlsafe(32)  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 * 24 * 60  # 30 days

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    nationality: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    nationality: Optional[str]
    created_at: str
    is_demo_user: bool = False

class OnboardingData(BaseModel):
    travel_preferences: Dict[str, Any]
    travel_style: str
    budget_range: str
    frequent_destinations: list[str] = []

def init_auth_tables():
    """Initialize authentication and user tracking tables"""
    conn = sqlite3.connect('travel_chatbot.db')
    cursor = conn.cursor()
    
    # Add authentication columns to users table (handle existing columns)
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN password_hash TEXT;')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN is_demo_user BOOLEAN DEFAULT FALSE;')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN last_login TIMESTAMP;')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE;')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    # Sessions table for tracking user sessions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            session_token TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # User interactions table for learning
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            interaction_type TEXT,
            interaction_data TEXT,
            context TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            session_id TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # User learning data
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_learning_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            data_type TEXT,
            data_key TEXT,
            data_value TEXT,
            confidence_score REAL DEFAULT 0.5,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Analytics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            event_type TEXT,
            event_data TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            session_id TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Mark existing users as demo users
    cursor.execute('''
        UPDATE users SET is_demo_user = TRUE WHERE password_hash IS NULL;
    ''')
    
    conn.commit()
    conn.close()

def get_password_hash(password: str) -> str:
    """Hash a password for storing"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_user(user_data: UserCreate) -> UserResponse:
    """Create a new user account"""
    conn = sqlite3.connect('travel_chatbot.db')
    cursor = conn.cursor()
    
    try:
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (user_data.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create new user
        user_id = str(uuid.uuid4())
        password_hash = get_password_hash(user_data.password)
        
        cursor.execute('''
            INSERT INTO users (id, first_name, last_name, email, nationality, password_hash, is_demo_user)
            VALUES (?, ?, ?, ?, ?, ?, FALSE)
        ''', (user_id, user_data.first_name, user_data.last_name, user_data.email, 
              user_data.nationality, password_hash))
        
        conn.commit()
        
        # Get created user
        cursor.execute('''
            SELECT id, email, first_name, last_name, nationality, created_at, is_demo_user
            FROM users WHERE id = ?
        ''', (user_id,))
        
        user_row = cursor.fetchone()
        if user_row:
            return UserResponse(
                id=user_row[0],
                email=user_row[1],
                first_name=user_row[2],
                last_name=user_row[3],
                nationality=user_row[4],
                created_at=user_row[5],
                is_demo_user=user_row[6]
            )
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()

def authenticate_user(email: str, password: str) -> Optional[UserResponse]:
    """Authenticate user with email and password"""
    conn = sqlite3.connect('travel_chatbot.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, email, first_name, last_name, nationality, password_hash, created_at, is_demo_user
            FROM users WHERE email = ? AND is_active = TRUE
        ''', (email,))
        
        user_row = cursor.fetchone()
        if not user_row:
            return None
        
        # Verify password
        if not verify_password(password, user_row[5]):
            return None
        
        # Update last login
        cursor.execute('''
            UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
        ''', (user_row[0],))
        conn.commit()
        
        return UserResponse(
            id=user_row[0],
            email=user_row[1],
            first_name=user_row[2],
            last_name=user_row[3],
            nationality=user_row[4],
            created_at=user_row[6],
            is_demo_user=user_row[7]
        )
        
    finally:
        conn.close()

def get_current_user_from_token(token: str) -> Optional[UserResponse]:
    """Get current user from JWT token"""
    print(f"DEBUG: Validating token: {token[:50]}...")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"DEBUG: Token decoded successfully: {payload}")
        user_id: str = payload.get("sub")
        if user_id is None:
            print("DEBUG: No 'sub' field in token payload")
            return None
        print(f"DEBUG: Extracted user_id: {user_id}")
    except JWTError as e:
        print(f"DEBUG: JWT decode error: {e}")
        return None
    
    # Get user from database
    conn = sqlite3.connect('travel_chatbot.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, email, first_name, last_name, nationality, created_at, is_demo_user
            FROM users WHERE id = ? AND is_active = TRUE
        ''', (user_id,))
        
        user_row = cursor.fetchone()
        if user_row:
            print(f"DEBUG: User found in database: {user_row[1]}")
            return UserResponse(
                id=user_row[0],
                email=user_row[1],
                first_name=user_row[2],
                last_name=user_row[3],
                nationality=user_row[4],
                created_at=user_row[5],
                is_demo_user=user_row[6]
            )
        else:
            print(f"DEBUG: No user found for ID: {user_id}")
            return None
    finally:
        conn.close()
    
    return None

def create_session(user_id: str, request: Request) -> str:
    """Create a new user session"""
    session_id = str(uuid.uuid4())
    session_token = secrets.token_urlsafe(32)
    
    conn = sqlite3.connect('travel_chatbot.db')
    cursor = conn.cursor()
    
    # Get client info
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    cursor.execute('''
        INSERT INTO user_sessions (id, user_id, session_token, ip_address, user_agent)
        VALUES (?, ?, ?, ?, ?)
    ''', (session_id, user_id, session_token, ip_address, user_agent))
    
    conn.commit()
    conn.close()
    
    return session_token

def get_or_create_anonymous_user(request: Request) -> str:
    """Get or create anonymous user based on session/fingerprint"""
    # Create fingerprint from IP + User Agent
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    fingerprint = hashlib.md5(f"{ip_address}:{user_agent}".encode()).hexdigest()
    
    conn = sqlite3.connect('travel_chatbot.db')
    cursor = conn.cursor()
    
    try:
        # Look for existing anonymous user with this fingerprint
        cursor.execute('''
            SELECT user_id FROM user_sessions 
            WHERE session_token = ? AND is_active = TRUE
        ''', (fingerprint,))
        
        result = cursor.fetchone()
        if result:
            return result[0]
        
        # Create new anonymous user
        user_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO users (id, first_name, last_name, email, is_demo_user, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, f"Anonymous", f"User", f"anon_{user_id[:8]}@temp.com", False, True))
        
        # Create session with fingerprint as token
        session_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT INTO user_sessions (id, user_id, session_token, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, user_id, fingerprint, ip_address, user_agent))
        
        conn.commit()
        return user_id
        
    finally:
        conn.close()

def log_user_interaction(user_id: str, interaction_type: str, interaction_data: Dict[str, Any], 
                        context: str = "", session_id: str = ""):
    """Log user interaction for learning purposes"""
    conn = sqlite3.connect('travel_chatbot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO user_interactions (user_id, interaction_type, interaction_data, context, session_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, interaction_type, json.dumps(interaction_data), context, session_id))
    
    conn.commit()
    conn.close()

def log_analytics_event(user_id: str, event_type: str, event_data: Dict[str, Any], session_id: str = ""):
    """Log analytics event"""
    conn = sqlite3.connect('travel_chatbot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO user_analytics (user_id, event_type, event_data, session_id)
        VALUES (?, ?, ?, ?)
    ''', (user_id, event_type, json.dumps(event_data), session_id))
    
    conn.commit()
    conn.close()

def learn_from_user_behavior(user_id: str, behavior_data: Dict[str, Any]):
    """Learn and update user preferences from behavior"""
    conn = sqlite3.connect('travel_chatbot.db')
    cursor = conn.cursor()
    
    for data_key, data_value in behavior_data.items():
        # Check if learning data exists
        cursor.execute('''
            SELECT id, confidence_score FROM user_learning_data 
            WHERE user_id = ? AND data_key = ?
        ''', (user_id, data_key))
        
        existing = cursor.fetchone()
        
        if existing:
            # Update confidence and value
            new_confidence = min(existing[1] + 0.1, 1.0)  # Increase confidence
            cursor.execute('''
                UPDATE user_learning_data 
                SET data_value = ?, confidence_score = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (str(data_value), new_confidence, existing[0]))
        else:
            # Create new learning entry
            cursor.execute('''
                INSERT INTO user_learning_data (user_id, data_type, data_key, data_value)
                VALUES (?, ?, ?, ?)
            ''', (user_id, "behavior", data_key, str(data_value)))
    
    conn.commit()
    conn.close()

def get_user_learning_profile(user_id: str) -> Dict[str, Any]:
    """Get learned user profile for personalization"""
    conn = sqlite3.connect('travel_chatbot.db')
    cursor = conn.cursor()
    
    # Get learning data
    cursor.execute('''
        SELECT data_key, data_value, confidence_score 
        FROM user_learning_data 
        WHERE user_id = ?
        ORDER BY confidence_score DESC
    ''', (user_id,))
    
    learning_data = {}
    for row in cursor.fetchall():
        learning_data[row[0]] = {
            "value": row[1],
            "confidence": row[2]
        }
    
    # Get interaction patterns
    cursor.execute('''
        SELECT interaction_type, COUNT(*) as count
        FROM user_interactions 
        WHERE user_id = ?
        GROUP BY interaction_type
        ORDER BY count DESC
    ''', (user_id,))
    
    interaction_patterns = dict(cursor.fetchall())
    
    conn.close()
    
    return {
        "learned_preferences": learning_data,
        "interaction_patterns": interaction_patterns,
        "user_id": user_id
    } 