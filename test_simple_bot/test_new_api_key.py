#!/usr/bin/env python3
"""
Test script to troubleshoot new API key issues
"""
import os
from openai import OpenAI

def test_api_key(api_key: str, description: str):
    """Test a specific API key"""
    print(f"\n🔍 Testing {description}...")
    print(f"🔑 Key: {api_key[:10]}...{api_key[-5:]}")
    
    client = OpenAI(api_key=api_key)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'OK'"}],
            max_tokens=5
        )
        
        print(f"✅ {description} - WORKING!")
        print(f"📝 Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        error_str = str(e)
        print(f"❌ {description} - FAILED: {error_str}")
        
        if "429" in error_str or "quota" in error_str.lower():
            print(f"   🚨 Quota exceeded for {description}")
        elif "401" in error_str:
            print(f"   🔑 Invalid API key for {description}")
        elif "model" in error_str.lower():
            print(f"   🤖 Model not available")
        
        return False

def troubleshoot_new_key():
    """Troubleshoot new API key issues"""
    print("🔧 Troubleshooting New API Key")
    print("=" * 50)
    
    # Test the old key first
    old_key = "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"
    test_api_key(old_key, "OLD API Key")
    
    # Ask for new key
    print("\n" + "=" * 50)
    print("📝 Please enter your NEW API key:")
    print("(It should start with 'sk-' and be different from the old one)")
    new_key = input("New API Key: ").strip()
    
    if not new_key:
        print("❌ No API key entered")
        return
    
    if new_key == old_key:
        print("❌ You entered the same old API key!")
        print("💡 Make sure you're using a completely new key from OpenAI")
        return
    
    # Test the new key
    test_api_key(new_key, "NEW API Key")
    
    # Check if keys are different
    print("\n" + "=" * 50)
    print("🔍 COMPARISON:")
    print(f"Old key: {old_key[:10]}...{old_key[-5:]}")
    print(f"New key: {new_key[:10]}...{new_key[-5:]}")
    
    if old_key == new_key:
        print("❌ Keys are identical - you need a different API key!")
    else:
        print("✅ Keys are different - good!")
    
    print("\n💡 TROUBLESHOOTING TIPS:")
    print("1. Make sure you created a NEW API key (not copied the old one)")
    print("2. Check if the new key has credits/usage limits")
    print("3. Verify the key format starts with 'sk-'")
    print("4. Try creating a key from a different OpenAI account")

if __name__ == "__main__":
    troubleshoot_new_key() 