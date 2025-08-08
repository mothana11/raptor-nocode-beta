#!/usr/bin/env python3
"""
Simple utility to check OpenAI API quota status
"""
import os
from openai import OpenAI

def check_openai_quota():
    """Check if OpenAI API is working and has quota available"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OPENAI_API_KEY found in environment")
        return False
    
    client = OpenAI(api_key=api_key)
    
    try:
        # Make a simple, low-cost API call with gpt-4o-mini
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Using the cheapest GPT-4 model
            messages=[{"role": "user", "content": "Say 'OK'"}],
            max_tokens=5
        )
        
        print("✅ OpenAI API is working!")
        print(f"📊 Response: {response.choices[0].message.content}")
        print(f"🔑 API Key: {api_key[:10]}...{api_key[-5:]}")
        return True
        
    except Exception as e:
        error_str = str(e)
        print(f"❌ OpenAI API Error: {error_str}")
        
        if "429" in error_str or "quota" in error_str.lower():
            print("\n🚨 QUOTA EXCEEDED - Here's how to fix it:")
            print("1. Visit: https://platform.openai.com/billing")
            print("2. Add payment method and purchase credits")
            print("3. Or create new API key with available quota")
            print("4. Update backend/.env with new key")
        elif "401" in error_str:
            print("\n🔑 INVALID API KEY:")
            print("1. Check your API key is correct")
            print("2. Visit: https://platform.openai.com/api-keys")
            print("3. Create a new API key if needed")
        
        return False

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv("backend/.env")
    
    print("🔍 Checking OpenAI API quota status...\n")
    check_openai_quota() 