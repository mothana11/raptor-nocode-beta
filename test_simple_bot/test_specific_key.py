#!/usr/bin/env python3
"""
Test the specific new API key from backend/.env
"""
import os
from openai import OpenAI

# The new API key from your .env file
NEW_API_KEY = "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"

def test_new_key():
    """Test the new API key specifically"""
    print("🔍 Testing NEW API Key from .env file...")
    print(f"🔑 Key: {NEW_API_KEY[:10]}...{NEW_API_KEY[-5:]}")
    
    client = OpenAI(api_key=NEW_API_KEY)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'OK'"}],
            max_tokens=5
        )
        
        print("✅ NEW API Key - WORKING!")
        print(f"📝 Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        error_str = str(e)
        print(f"❌ NEW API Key - FAILED: {error_str}")
        
        if "429" in error_str or "quota" in error_str.lower():
            print("🚨 This NEW API key also has quota issues!")
            print("💡 This means:")
            print("   1. The new key is from the same account (same quota)")
            print("   2. OR the new account also has no credits")
            print("   3. You need to add credits to the account with this key")
        elif "401" in error_str:
            print("🔑 Invalid API key format")
        
        return False

if __name__ == "__main__":
    test_new_key() 