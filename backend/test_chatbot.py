#!/usr/bin/env python3
"""
Test script for Travel Chatbot
Run this to verify everything is working correctly
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_imports():
    """Test if all modules can be imported"""
    print("🧪 Testing imports...")
    try:
        from workflow import build_travel_workflow, process_travel_request, determine_intent
        from mcp_tools import ALL_TOOLS, amadeus_api, booking_api
        from auth import init_auth_tables
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_api_keys():
    """Test if API keys are configured"""
    print("\n🔑 Testing API key configuration...")
    
    keys = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY"),
        "AMADEUS_CLIENT_ID": os.getenv("AMADEUS_CLIENT_ID"),
        "AMADEUS_CLIENT_SECRET": os.getenv("AMADEUS_CLIENT_SECRET"),
        "RAPID_API_KEY": os.getenv("RAPID_API_KEY")
    }
    
    all_configured = True
    for key_name, key_value in keys.items():
        if key_value:
            print(f"✅ {key_name}: Configured")
        else:
            print(f"⚠️ {key_name}: Not configured")
            all_configured = False
    
    return all_configured

def test_workflow():
    """Test the workflow creation"""
    print("\n🔧 Testing workflow creation...")
    try:
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            print("⚠️ OPENAI_API_KEY not configured, using dummy key for test")
            openai_key = "sk-dummy"
        
        from workflow import build_travel_workflow
        workflow = build_travel_workflow(openai_key)
        print("✅ Workflow created successfully")
        return True
    except Exception as e:
        print(f"❌ Workflow creation failed: {e}")
        return False

def test_travel_request():
    """Test a sample travel request"""
    print("\n🎯 Testing travel request processing...")
    try:
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            print("⚠️ Using dummy OpenAI key - response may be limited")
            openai_key = "sk-dummy"
        
        from workflow import process_travel_request
        
        test_message = "Find flights from New York to Los Angeles on March 15"
        response = process_travel_request(test_message, openai_key, [])
        
        if response and len(response) > 10:
            print("✅ Travel request processed successfully")
            print(f"📝 Sample response: {response[:100]}...")
            return True
        else:
            print(f"⚠️ Got response but it's short: {response}")
            return False
            
    except Exception as e:
        print(f"❌ Travel request processing failed: {e}")
        return False

def test_database():
    """Test database initialization"""
    print("\n💾 Testing database...")
    try:
        from main import init_db
        init_db()
        print("✅ Database initialized successfully")
        
        # Test if we can connect to the database
        import sqlite3
        conn = sqlite3.connect('travel_chatbot.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()
        
        print(f"📊 Found {len(tables)} database tables")
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_api_endpoints():
    """Test if APIs would work (without actually calling them)"""
    print("\n🌐 Testing API connectivity...")
    try:
        from mcp_tools import amadeus_api, booking_api
        
        # Test Amadeus token (if credentials are available)
        if os.getenv("AMADEUS_CLIENT_ID") and os.getenv("AMADEUS_CLIENT_SECRET"):
            token = amadeus_api.get_token()
            if token:
                print("✅ Amadeus API: Authentication successful")
            else:
                print("⚠️ Amadeus API: Authentication failed")
        else:
            print("⚠️ Amadeus API: Credentials not configured")
        
        # Test RapidAPI (basic check)
        if os.getenv("RAPID_API_KEY"):
            print("✅ RapidAPI: Key configured")
        else:
            print("⚠️ RapidAPI: Key not configured")
        
        return True
    except Exception as e:
        print(f"❌ API connectivity test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Travel Chatbot Test Suite")
    print("=" * 50)
    
    tests = [
        ("Module Imports", test_imports),
        ("API Key Configuration", test_api_keys),
        ("Workflow Creation", test_workflow),
        ("Travel Request Processing", test_travel_request),
        ("Database Initialization", test_database),
        ("API Connectivity", test_api_endpoints)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📋 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your chatbot is ready to use.")
    elif passed >= total - 2:
        print("⚠️ Most tests passed. The chatbot should work with some limitations.")
    else:
        print("🔧 Several tests failed. Please check your configuration.")
    
    print("\n💡 Next steps:")
    if not os.getenv("OPENAI_API_KEY"):
        print("- Configure OPENAI_API_KEY in your .env file")
    if not os.getenv("AMADEUS_CLIENT_ID"):
        print("- Configure Amadeus API credentials for real flight data")
    if not os.getenv("RAPID_API_KEY"):
        print("- Configure RapidAPI key for real hotel data")
    
    print("- Start the server with: uvicorn main:app --reload --port 8000")

if __name__ == "__main__":
    main()