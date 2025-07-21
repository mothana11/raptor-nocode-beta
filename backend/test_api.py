#!/usr/bin/env python3
"""
Simple test script for the Travel Chatbot API
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Health check: {response.status_code}")
        print(f"   Response: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_chat():
    """Test the chat endpoint"""
    try:
        # Test travel-related queries
        test_messages = [
            "I need help booking a hotel in New York for next weekend",
            "How do I reschedule my flight from tomorrow to next week?",
            "What's the process for requesting a refund on my hotel booking?",
            "Find me flights from Los Angeles to Tokyo in March"
        ]
        
        conversation_id = None
        
        for i, message in enumerate(test_messages, 1):
            print(f"\n🧪 Test {i}: {message}")
            
            payload = {
                "conversation_id": conversation_id,
                "message": message
            }
            
            response = requests.post(f"{BASE_URL}/chat", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                conversation_id = data["conversation_id"]
                print(f"✅ Response: {data['response'][:100]}...")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                return False
                
        return True
        
    except Exception as e:
        print(f"❌ Chat test failed: {e}")
        return False

def test_conversation_history(conversation_id):
    """Test the conversation history endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/conversations/{conversation_id}/history")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Conversation history: {len(data['messages'])} messages")
            return True
        else:
            print(f"❌ History error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ History test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Travel Chatbot API")
    print("=" * 40)
    
    # Test health endpoint
    if not test_health():
        print("\n❌ Health check failed. Is the server running?")
        return
    
    # Test chat functionality
    if not test_chat():
        print("\n❌ Chat functionality failed.")
        return
    
    print("\n✅ All tests passed! The API is working correctly.")
    print("\n💡 You can now start the frontend and test the full application.")

if __name__ == "__main__":
    main() 