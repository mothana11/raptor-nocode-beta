#!/usr/bin/env python3
"""
Test script to verify chatbot fixes work correctly
"""

import requests
import json

def test_chatbot_consistency():
    """Test that the chatbot maintains consistency and respects user choices"""
    
    base_url = "http://localhost:8000"
    
    # Test user authentication
    print("🔍 Testing chatbot fixes...")
    
    # Login as Tony
    login_data = {
        "email": "mrbingona@gmail.com", 
        "password": "password123"
    }
    
    try:
        login_response = requests.post(f"{base_url}/auth/login", json=login_data)
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            print("✅ Login successful")
        else:
            print("❌ Login failed")
            return
    except Exception as e:
        print(f"❌ Login error: {e}")
        return
    
    # Test 1: Flight search consistency
    print("\n🛫 Test 1: Flight search consistency")
    chat_data = {"message": "I want flights from Detroit to Kyoto on July 22"}
    
    try:
        response1 = requests.post(f"{base_url}/chat", json=chat_data, headers=headers)
        if response1.status_code == 200:
            response_text1 = response1.json()["response"]
            print("✅ First flight search:", response_text1[:200] + "...")
            
            # Test same search again - should be consistent
            response2 = requests.post(f"{base_url}/chat", json=chat_data, headers=headers)
            if response2.status_code == 200:
                response_text2 = response2.json()["response"]
                print("✅ Second flight search:", response_text2[:200] + "...")
                
                # Check if responses contain similar flight info
                if "Detroit" in response_text1 and "Detroit" in response_text2:
                    print("✅ Consistency test PASSED - Origin city maintained")
                else:
                    print("❌ Consistency test FAILED - Origin city not maintained")
            else:
                print("❌ Second search failed")
        else:
            print("❌ First search failed")
    except Exception as e:
        print(f"❌ Flight search error: {e}")
    
    # Test 2: User choice handling
    print("\n🎯 Test 2: User choice handling")
    choice_data = {"message": "option 3"}
    
    try:
        choice_response = requests.post(f"{base_url}/chat", json=choice_data, headers=headers)
        if choice_response.status_code == 200:
            choice_text = choice_response.json()["response"]
            print("✅ Choice response:", choice_text[:200] + "...")
            
            if "option 3" in choice_text.lower() or "third" in choice_text.lower():
                print("✅ Choice handling PASSED - AI acknowledged option 3")
            else:
                print("❌ Choice handling FAILED - AI didn't acknowledge option 3")
        else:
            print("❌ Choice response failed")
    except Exception as e:
        print(f"❌ Choice handling error: {e}")
    
    # Test 3: Context memory
    print("\n🧠 Test 3: Context memory")
    context_data = {"message": "I want to bring my brother too"}
    
    try:
        context_response = requests.post(f"{base_url}/chat", json=context_data, headers=headers)
        if context_response.status_code == 200:
            context_text = context_response.json()["response"]
            print("✅ Context response:", context_text[:200] + "...")
            
            if "brother" in context_text.lower() or "two" in context_text.lower():
                print("✅ Context memory PASSED - AI remembered brother")
            else:
                print("❌ Context memory FAILED - AI forgot about brother")
        else:
            print("❌ Context response failed")
    except Exception as e:
        print(f"❌ Context memory error: {e}")
    
    print("\n🎉 Chatbot fix testing complete!")
    print("\n📋 Expected improvements:")
    print("• Flight options should be consistent between searches")
    print("• AI should respect user choice of 'option 3'")
    print("• AI should remember travel companions (brother)")
    print("• AI should maintain departure city (Detroit) throughout conversation")

if __name__ == "__main__":
    test_chatbot_consistency() 