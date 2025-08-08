#!/usr/bin/env python3
"""
Quick configuration checker for your travel chatbot
Run this to see what's configured and what's missing
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_amadeus_auth():
    """Test Amadeus authentication specifically"""
    print("\n🔍 Testing Amadeus Authentication...")
    
    client_id = os.getenv("AMADEUS_CLIENT_ID") or os.getenv("AMADEUS_API_KEY")
    client_secret = os.getenv("AMADEUS_CLIENT_SECRET") or os.getenv("AMADEUS_API_SECRET")
    
    if not client_id or not client_secret:
        print("❌ Missing Amadeus credentials")
        return False
    
    print(f"✅ Client ID: {client_id[:8]}...")
    print(f"✅ Client Secret: {client_secret[:8]}...")
    
    try:
        # Test the actual authentication
        import requests
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret
        }
        
        # Use test environment
        token_url = "https://test.api.amadeus.com/v1/security/oauth2/token"
        print(f"🔗 Testing: {token_url}")
        
        response = requests.post(token_url, headers=headers, data=data, timeout=10)
        
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            print("✅ Amadeus Authentication: SUCCESS")
            print(f"🎫 Token Type: {token_data.get('type', 'Bearer')}")
            print(f"⏰ Expires In: {token_data.get('expires_in', 'Unknown')} seconds")
            return True
        else:
            print("❌ Amadeus Authentication: FAILED")
            print(f"💥 Error: {response.text}")
            
            # Provide specific help based on error
            if response.status_code == 401:
                print("\n🔧 Fix: Check your CLIENT_ID and CLIENT_SECRET")
                print("   • Go to https://developers.amadeus.com/")
                print("   • Sign in and go to 'My Self-Service Workspace'") 
                print("   • Check your app credentials")
            elif response.status_code == 400:
                print("\n🔧 Fix: Request format issue - this should be fixed in the code")
            
            return False
            
    except Exception as e:
        print(f"❌ Authentication test failed: {e}")
        return False

def test_rapidapi_setup():
    """Test RapidAPI setup"""
    print("\n🔍 Testing RapidAPI Setup...")
    
    rapid_key = os.getenv("RAPID_API_KEY") or os.getenv("RAPIDAPI_KEY")
    
    if not rapid_key:
        print("❌ Missing RapidAPI key")
        return False
        
    print(f"✅ RapidAPI Key: {rapid_key[:8]}...")
    
    try:
        # Test using the correct API from the user's example
        import requests
        
        headers = {
            'x-rapidapi-key': rapid_key,  # lowercase as in the example
            'x-rapidapi-host': "booking-com15.p.rapidapi.com"  # correct host
        }
        
        # Test the searchDestination endpoint (from the user's example)
        url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchDestination"
        params = {"query": "new york"}
        
        print("🔗 Testing destination search endpoint...")
        print(f"   URL: {url}")
        print(f"   Headers: x-rapidapi-host: {headers['x-rapidapi-host']}")
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        print(f"📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get("data", [])
            print(f"✅ RapidAPI: SUCCESS - Found {len(results)} destinations")
            
            if results:
                # Show first result for verification
                first_result = results[0]
                dest_name = first_result.get("label", "Unknown")
                dest_id = first_result.get("dest_id", "Unknown")
                print(f"   Sample destination: {dest_name} (ID: {dest_id})")
            
            return True
        elif response.status_code == 429:
            print("⚠️ RapidAPI: Rate limit hit (this is normal for free tier)")
            print("   Your API key is working, just reached the limit")
            return True  # Still configured correctly
        elif response.status_code == 401:
            print("❌ RapidAPI: Unauthorized - Invalid API key")
            print(f"   Response: {response.text[:200]}...")
            print("\n🔧 Fix: Check your RapidAPI key")
            print("   • Go to https://rapidapi.com/")
            print("   • Check your dashboard for the correct key")
            print("   • Make sure you've subscribed to the Booking.com API")
            return False
        elif response.status_code == 403:
            print("❌ RapidAPI: Forbidden - Check your subscription")
            print("   You may need to subscribe to the Booking.com API")
            print("   Go to: https://rapidapi.com/tipsters/api/booking-com15/")
            return False
        else:
            print(f"⚠️ RapidAPI: Unexpected response {response.status_code}")
            print(f"Response: {response.text[:300]}...")
            print("\n💡 This might still work - some APIs return different status codes")
            return False
            
    except Exception as e:
        print(f"❌ RapidAPI test failed: {e}")
        print("\n🔧 Possible issues:")
        print("   • Network connectivity problems")
        print("   • API endpoint might be different")
        print("   • Check your internet connection")
        return False

def check_config():
    """Check current configuration status"""
    print("🔍 Travel Chatbot Configuration Check")
    print("=" * 50)
    
    # Check API keys with both old and new formats
    configs = [
        {
            "name": "OpenAI API Key",
            "keys": ["OPENAI_API_KEY"],
            "priority": "🔴 CRITICAL",
            "description": "Required for AI responses",
            "get_url": "https://platform.openai.com/api-keys"
        },
        {
            "name": "Amadeus Flight API",
            "keys": ["AMADEUS_CLIENT_ID", "AMADEUS_API_KEY"],
            "secondary_keys": ["AMADEUS_CLIENT_SECRET", "AMADEUS_API_SECRET"],
            "priority": "🟡 IMPORTANT", 
            "description": "Required for real flight data",
            "get_url": "https://developers.amadeus.com/"
        },
        {
            "name": "RapidAPI Hotel Key",
            "keys": ["RAPID_API_KEY", "RAPIDAPI_KEY"],
            "priority": "🟡 IMPORTANT",
            "description": "Required for real hotel data", 
            "get_url": "https://rapidapi.com/"
        },
        {
            "name": "JWT Secret Key",
            "keys": ["SECRET_KEY"],
            "priority": "🟢 OPTIONAL",
            "description": "For user authentication"
        }
    ]
    
    total_configured = 0
    total_configs = len(configs)
    
    for config in configs:
        # Check primary keys
        primary_value = None
        for key in config["keys"]:
            value = os.getenv(key)
            if value and value.strip():
                primary_value = value
                break
        
        # Check secondary keys if needed
        secondary_value = None
        if "secondary_keys" in config:
            for key in config["secondary_keys"]:
                value = os.getenv(key)
                if value and value.strip():
                    secondary_value = value
                    break
        
        # Determine status
        if config["name"] == "Amadeus Flight API":
            # Both primary and secondary needed
            if primary_value and secondary_value:
                status = "✅ CONFIGURED"
                total_configured += 1
            elif primary_value or secondary_value:
                status = "⚠️ PARTIAL (need both ID and SECRET)"
            else:
                status = "❌ MISSING"
        else:
            # Only primary needed
            if primary_value:
                status = "✅ CONFIGURED"
                total_configured += 1
            else:
                status = "❌ MISSING"
        
        print(f"\n{config['priority']} {config['name']}")
        print(f"   Status: {status}")
        print(f"   Purpose: {config['description']}")
        
        if status.startswith("❌") or status.startswith("⚠️"):
            if "get_url" in config:
                print(f"   Get key: {config['get_url']}")
    
    print("\n" + "=" * 50)
    print(f"📊 Configuration Summary: {total_configured}/{total_configs} properly configured")
    
    # Provide recommendations
    print("\n💡 Recommendations:")
    
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key or not openai_key.strip():
        print("🔴 URGENT: Add your OpenAI API key - chatbot won't work without it")
        print("   Get one at: https://platform.openai.com/api-keys")
    
    amadeus_id = os.getenv("AMADEUS_CLIENT_ID") or os.getenv("AMADEUS_API_KEY")
    amadeus_secret = os.getenv("AMADEUS_CLIENT_SECRET") or os.getenv("AMADEUS_API_SECRET")
    
    if not (amadeus_id and amadeus_secret):
        print("🟡 For real flight data: Add Amadeus API credentials")
        print("   Get them at: https://developers.amadeus.com/")
    
    rapid_key = os.getenv("RAPID_API_KEY") or os.getenv("RAPIDAPI_KEY")
    if not rapid_key or not rapid_key.strip():
        print("🟡 For real hotel data: Add RapidAPI key")
        print("   Get one at: https://rapidapi.com/")
    
    # Test with current config
    print(f"\n🧪 Testing with current configuration...")
    
    if openai_key and openai_key.strip():
        print("✅ Can provide AI-powered responses")
    else:
        print("❌ Cannot provide AI responses without OpenAI key")
    
    if amadeus_id and amadeus_secret:
        print("✅ Can search real flights")
    else:
        print("⚠️ Will show demo flight data (no real API)")
    
    if rapid_key and rapid_key.strip():
        print("✅ Can search real hotels") 
    else:
        print("⚠️ Will show demo hotel data (no real API)")
    
    print("✅ Can always provide real booking links")
    print("✅ Can handle reschedule/cancellation requests")
    
    print(f"\n🚀 Next Steps:")
    if total_configured == 0:
        print("1. Add at least your OpenAI API key to test basic functionality")
        print("2. Start server: uvicorn main:app --reload --port 8000")
        print("3. Add other API keys gradually for full functionality")
    elif total_configured >= 2:
        print("1. Your chatbot should work well with current configuration!")
        print("2. Start server: uvicorn main:app --reload --port 8000") 
        print("3. Test with: python test_chatbot.py")
    else:
        print("1. Add your OpenAI API key if missing")
        print("2. Start server: uvicorn main:app --reload --port 8000")
        print("3. Add other API keys for full real-time data")
    
    # Run detailed API tests if keys are present
    print("\n" + "=" * 50)
    print("🧪 Detailed API Testing")
    print("=" * 50)
    
    amadeus_works = test_amadeus_auth()
    rapidapi_works = test_rapidapi_setup()
    
    print(f"\n📋 API Test Results:")
    print(f"✅ Amadeus API: {'Working' if amadeus_works else 'Failed'}")
    print(f"✅ RapidAPI: {'Working' if rapidapi_works else 'Failed'}")
    
    if not amadeus_works and (os.getenv("AMADEUS_CLIENT_ID") or os.getenv("AMADEUS_API_KEY")):
        print("\n⚠️ Amadeus API Issue Detected:")
        print("   Your credentials might be incorrect or you may need to:")
        print("   • Verify your app is created in Amadeus Developer Portal")
        print("   • Check that you're using the right CLIENT_ID and CLIENT_SECRET")
        print("   • Ensure your app has Flight Search API access")
        
    if not rapidapi_works and (os.getenv("RAPID_API_KEY") or os.getenv("RAPIDAPI_KEY")):
        print("\n⚠️ RapidAPI Issue Detected:")
        print("   • Check your RapidAPI key is correct")
        print("   • Verify you've subscribed to Booking.com API")
        print("   • Make sure you haven't exceeded your free tier limits")

if __name__ == "__main__":
    check_config()