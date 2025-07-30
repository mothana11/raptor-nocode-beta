#!/usr/bin/env python3
"""
Direct OpenAI API test (no agents SDK)
"""
import os
from openai import OpenAI

# Set API key directly
os.environ["OPENAI_API_KEY"] = "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"

def test_direct_openai():
    """Test OpenAI API directly"""
    print("🔍 Testing OpenAI API directly...")
    
    client = OpenAI()
    
    try:
        print("📤 Making direct API call...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Write a haiku about recursion in programming."}],
            max_tokens=100
        )
        
        print("✅ Direct OpenAI API call successful!")
        print(f"📝 Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        error_str = str(e)
        print(f"❌ Direct API Error: {error_str}")
        
        if "429" in error_str or "quota" in error_str.lower():
            print("\n🚨 QUOTA EXCEEDED:")
            print("1. Your OpenAI API key has reached its usage limit")
            print("2. Visit: https://platform.openai.com/billing")
            print("3. Add payment method and purchase credits")
            print("4. Or create a new API key with available quota")
        
        return False

if __name__ == "__main__":
    test_direct_openai() 