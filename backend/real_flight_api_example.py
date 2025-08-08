"""
REAL FLIGHT API INTEGRATION EXAMPLE
Replace the demo MCP tools with these REAL API calls for production use.
"""

import requests
import os
from datetime import datetime

class RealFlightAPI:
    """Real flight API integration for production use"""
    
    def __init__(self):
        # Get real API credentials from environment
        self.amadeus_token = os.getenv('AMADEUS_API_TOKEN')
        self.amadeus_key = os.getenv('AMADEUS_API_KEY')
        self.amadeus_secret = os.getenv('AMADEUS_API_SECRET')
        
    def get_amadeus_access_token(self):
        """Get access token from Amadeus API"""
        url = "https://api.amadeus.com/v1/security/oauth2/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "client_id": self.amadeus_key,
            "client_secret": self.amadeus_secret
        }
        response = requests.post(url, headers=headers, data=data)
        return response.json()["access_token"]
    
    def search_real_flights(self, origin: str, destination: str, departure_date: str):
        """Get REAL flight data from Amadeus API"""
        
        # Get access token
        token = self.get_amadeus_access_token()
        
        # Search for real flights
        url = "https://api.amadeus.com/v2/shopping/flight-offers"
        headers = {"Authorization": f"Bearer {token}"}
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": 1,
            "max": 4  # Return top 4 flights
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            return self.format_real_flight_data(response.json())
        else:
            return f"Error fetching real flight data: {response.text}"
    
    def format_real_flight_data(self, amadeus_response):
        """Format real Amadeus API response for customers"""
        
        flights = amadeus_response.get('data', [])
        
        if not flights:
            return "No flights found for this route and date."
        
        result = f"✈️ REAL FLIGHTS AVAILABLE NOW:\n\n"
        
        for i, flight in enumerate(flights[:4], 1):
            # Extract real flight details
            segments = flight['itineraries'][0]['segments'][0]
            price = flight['price']['total']
            currency = flight['price']['currency']
            
            departure = segments['departure']
            arrival = segments['arrival']
            carrier = segments['carrierCode']
            flight_number = segments['number']
            
            result += f"{i}. {carrier} Flight {carrier}{flight_number}\n"
            result += f"   Departure: {departure['at']} from {departure['iataCode']}\n"
            result += f"   Arrival: {arrival['at']} at {arrival['iataCode']}\n"
            result += f"   Price: {currency} {price}\n"
            result += f"   Book: https://www.amadeus.com/booking\n\n"
        
        result += "These are LIVE flights you can book RIGHT NOW!\n"
        result += f"Data updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}"
        
        return result

# INTEGRATION INSTRUCTIONS:

# 1. Sign up for Amadeus API (FREE tier):
#    https://developers.amadeus.com/register

# 2. Get your API credentials:
#    - API Key
#    - API Secret

# 3. Add to your .env file:
#    AMADEUS_API_KEY=your_api_key_here
#    AMADEUS_API_SECRET=your_api_secret_here

# 4. Replace the _get_real_flight_data function in mcp_tools.py:
def get_real_flight_data_production(origin: str, destination: str, departure_date: str) -> str:
    """Production function with REAL flight data"""
    api = RealFlightAPI()
    return api.search_real_flights(origin, destination, departure_date)

# 5. Update search_flights tool to use this function

print("🔧 REAL FLIGHT API INTEGRATION EXAMPLE READY")
print("📋 Follow the integration steps above for production use")
print("🌐 No more fake data - only real bookable flights!")