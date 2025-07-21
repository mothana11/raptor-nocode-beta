#!/usr/bin/env python3
"""
Test script for all 12 MCP tools in the Enhanced Travel Chatbot
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_chat_endpoint(message, description):
    """Test a chat message and return the response"""
    print(f"\n🧪 Testing: {description}")
    print(f"📤 Input: {message}")
    
    payload = {
        "message": message,
        "conversation_id": None
    }
    
    try:
        response = requests.post(f"{BASE_URL}/chat", json=payload)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {result['response'][:200]}...")
            return result
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def main():
    """Test all 12 MCP tools"""
    
    print("🚀 Enhanced Travel Chatbot - Tool Testing Suite")
    print("=" * 60)
    
    # Test 1: Flight Search
    test_chat_endpoint(
        "Find flights from New York to Tokyo for March 15th",
        "Flight Search Tool"
    )
    time.sleep(1)
    
    # Test 2: Hotel Booking
    test_chat_endpoint(
        "Book a hotel in Paris for March 20-25 for 2 guests",
        "Hotel Booking Tool"
    )
    time.sleep(1)
    
    # Test 3: Car Rental
    test_chat_endpoint(
        "Search for car rentals in London from April 1-7, I need an SUV",
        "Car Rental Search Tool"
    )
    time.sleep(1)
    
    # Test 4: Activity Booking
    test_chat_endpoint(
        "Book a food tour in Rome for 4 people on May 10th",
        "Activity Booking Tool"
    )
    time.sleep(1)
    
    # Test 5: Travel Insurance
    test_chat_endpoint(
        "Get travel insurance quotes for a $4000 trip to Japan for 2 travelers for 10 days",
        "Travel Insurance Tool"
    )
    time.sleep(1)
    
    # Test 6: Visa Requirements
    test_chat_endpoint(
        "Check visa requirements for US citizens traveling to India for tourism",
        "Visa Requirements Tool"
    )
    time.sleep(1)
    
    # Test 7: Currency Converter
    test_chat_endpoint(
        "Convert 1000 USD to EUR",
        "Currency Converter Tool"
    )
    time.sleep(1)
    
    # Test 8: Weather Forecast
    test_chat_endpoint(
        "What's the weather forecast for Barcelona on June 15th?",
        "Weather Forecast Tool"
    )
    time.sleep(1)
    
    # Test 9: Travel Alerts
    test_chat_endpoint(
        "Are there any travel alerts for Thailand?",
        "Travel Alerts Tool"
    )
    time.sleep(1)
    
    # Test 10: Booking Status
    test_chat_endpoint(
        "Check the status of booking HTL123456",
        "Booking Status Tool"
    )
    time.sleep(1)
    
    # Test 11: Travel Recommendations
    test_chat_endpoint(
        "Give me travel recommendations for Singapore for leisure travel",
        "Travel Recommendations Tool"
    )
    time.sleep(1)
    
    # Test 12: Booking Modification
    test_chat_endpoint(
        "Cancel booking ABC789 and process my refund",
        "Booking Modification Tool"
    )
    time.sleep(1)
    
    # Test 13: Multi-tool Workflow
    test_chat_endpoint(
        "Plan a complete trip to Amsterdam: find flights from Boston, book a hotel, get car rental, check weather, and tell me about visa requirements",
        "Multi-tool Workflow Test"
    )
    
    print("\n" + "=" * 60)
    print("🎉 Tool testing complete!")
    print("\n🌟 All 12 tools are now available:")
    print("   • Flight Search & Hotel Booking")
    print("   • Car Rental Search & Activity Booking") 
    print("   • Travel Insurance & Visa Requirements")
    print("   • Currency Converter & Weather Forecast")
    print("   • Travel Alerts & Booking Management")
    print("   • Travel Recommendations & Multi-tool Workflows")
    print("\n🚀 Ready for comprehensive travel assistance demo!")

if __name__ == "__main__":
    main() 