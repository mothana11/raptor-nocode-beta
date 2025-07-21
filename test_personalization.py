#!/usr/bin/env python3
"""
Demo script showing the travel chatbot's personalization features
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_anonymous_user():
    """Test anonymous user experience"""
    print("🤖 TESTING ANONYMOUS USER EXPERIENCE")
    print("=" * 50)
    
    # First message as anonymous user
    response = requests.post(f"{BASE_URL}/chat", json={
        "message": "Hi there!"
    })
    
    if response.status_code == 200:
        data = response.json()
        print("💬 First Message Response:")
        print(f"   {data['response']}")
        conversation_id = data['conversation_id']
        
        # Second message to see if it encourages registration
        print("\n💬 Second Message Response:")
        response2 = requests.post(f"{BASE_URL}/chat", json={
            "message": "I need help planning a trip",
            "conversation_id": conversation_id
        })
        
        if response2.status_code == 200:
            data2 = response2.json()
            print(f"   {data2['response']}")
        
        return conversation_id
    else:
        print(f"❌ Error: {response.status_code}")
        return None

def test_user_registration():
    """Test user registration and personalized experience"""
    print("\n\n👤 TESTING USER REGISTRATION")
    print("=" * 50)
    
    # Register a new user
    user_data = {
        "email": "john.doe@example.com",
        "password": "testpassword123",
        "first_name": "John",
        "last_name": "Doe",
        "nationality": "US"
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    
    if response.status_code == 200:
        data = response.json()
        token = data['access_token']
        print("✅ User registered successfully!")
        
        # Test authenticated chat
        headers = {"Authorization": f"Bearer {token}"}
        
        # First message as registered user
        response2 = requests.post(f"{BASE_URL}/chat", 
                                 json={"message": "Hello!"},
                                 headers=headers)
        
        if response2.status_code == 200:
            data2 = response2.json()
            print("💬 Welcome Message for Registered User:")
            print(f"   {data2['response']}")
            
            conversation_id = data2['conversation_id']
            
            # Send a few messages to build learning profile
            learning_messages = [
                "I love luxury travel and staying in 5-star hotels",
                "I'm interested in visiting Paris and Tokyo",
                "I prefer morning flights and cultural activities like museums"
            ]
            
            print("\n🧠 BUILDING LEARNING PROFILE...")
            for i, msg in enumerate(learning_messages, 1):
                print(f"\n   Message {i}: {msg}")
                response3 = requests.post(f"{BASE_URL}/chat",
                                        json={"message": msg, "conversation_id": conversation_id},
                                        headers=headers)
                if response3.status_code == 200:
                    data3 = response3.json()
                    print(f"   AI Response: {data3['response'][:100]}...")
                
                time.sleep(1)  # Brief pause between messages
            
            # Test personalized response
            print(f"\n💡 TESTING PERSONALIZED RESPONSE:")
            response4 = requests.post(f"{BASE_URL}/chat",
                                    json={"message": "Help me plan a trip", "conversation_id": conversation_id},
                                    headers=headers)
            
            if response4.status_code == 200:
                data4 = response4.json()
                print(f"   Personalized Response: {data4['response']}")
            
            # Get user profile to show learning data
            profile_response = requests.get(f"{BASE_URL}/user/profile", headers=headers)
            if profile_response.status_code == 200:
                profile_data = profile_response.json()
                print(f"\n📊 LEARNED USER PREFERENCES:")
                learning_profile = profile_data.get('learning_profile', {})
                for key, value in learning_profile.items():
                    print(f"   {key}: {value}")
        
        return token
    else:
        print(f"❌ Registration failed: {response.status_code} - {response.text}")
        return None

def test_returning_user(token):
    """Test returning user experience"""
    print("\n\n🔄 TESTING RETURNING USER EXPERIENCE")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Start new conversation as returning user
    response = requests.post(f"{BASE_URL}/chat",
                           json={"message": "Hi, I'm back!"},
                           headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        print("💬 Returning User Welcome:")
        print(f"   {data['response']}")
    else:
        print(f"❌ Error: {response.status_code}")

def main():
    """Run all tests"""
    print("🚀 TRAVEL CHATBOT PERSONALIZATION DEMO")
    print("=" * 60)
    print("This demo shows how the chatbot handles different user types:")
    print("1. Anonymous users (encouraged to register)")
    print("2. New registered users (personalized welcome)")
    print("3. Learning from conversations")
    print("4. Returning users (contextual responses)")
    print("=" * 60)
    
    # Test anonymous user
    conversation_id = test_anonymous_user()
    
    # Test registration and learning
    token = test_user_registration()
    
    if token:
        # Test returning user
        test_returning_user(token)
        
        # Show analytics
        print(f"\n📈 SYSTEM ANALYTICS:")
        analytics_response = requests.get(f"{BASE_URL}/analytics/dashboard")
        if analytics_response.status_code == 200:
            analytics = analytics_response.json()
            print(f"   Real Users: {analytics['user_stats']['real_users']}")
            print(f"   Total Interactions: {sum(analytics['interaction_stats'].values())}")
            print(f"   Recent Activity: {analytics['recent_activity']}")
    
    print(f"\n✅ Demo complete! The chatbot now:")
    print(f"   • Properly welcomes anonymous users")
    print(f"   • Encourages registration for personalization")
    print(f"   • Learns from every conversation")
    print(f"   • Provides contextual responses to returning users")
    print(f"   • Tracks comprehensive analytics")

if __name__ == "__main__":
    print("⏳ Waiting for backend to start...")
    time.sleep(3)  # Wait for backend to start
    
    try:
        # Check if backend is running
        response = requests.get(f"{BASE_URL}/analytics/dashboard")
        if response.status_code == 200:
            main()
        else:
            print("❌ Backend not responding. Make sure it's running on http://localhost:8000")
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Make sure it's running on http://localhost:8000")
        print("💡 Run: cd backend && uvicorn main:app --reload") 