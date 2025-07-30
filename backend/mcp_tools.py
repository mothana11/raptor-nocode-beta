from langchain.tools import tool
from typing import Dict, Any
import json
from datetime import datetime, timedelta
import os
import time
import hashlib
from openai import OpenAI

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Simple cache and rate limiting
_tool_cache = {}
_last_api_call = 0
_min_call_interval = 5.0  # Minimum 5 seconds between API calls (increased)
_daily_call_count = 0
_last_reset_date = None
_max_daily_calls = 30  # Reduced to 30 calls per day

def _get_cache_key(tool_name: str, user_query: str, parameters: Dict[str, Any]) -> str:
    """Generate cache key for tool responses"""
    cache_data = f"{tool_name}:{user_query}:{json.dumps(parameters, sort_keys=True)}"
    return hashlib.md5(cache_data.encode()).hexdigest()

def _check_daily_limit() -> bool:
    """Check if we've hit the daily API call limit"""
    global _daily_call_count, _last_reset_date
    
    today = datetime.now().date()
    if _last_reset_date != today:
        _daily_call_count = 0
        _last_reset_date = today
    
    return _daily_call_count < _max_daily_calls

def _call_openai_for_tool(tool_name: str, user_query: str, parameters: Dict[str, Any]) -> str:
    """
    Use OpenAI to generate intelligent, contextual responses for travel tools
    with aggressive rate limiting to prevent quota issues
    """
    # Check cache first (increased cache time to 1 hour)
    cache_key = _get_cache_key(tool_name, user_query, parameters)
    if cache_key in _tool_cache:
        cached_result, cached_time = _tool_cache[cache_key]
        # Cache valid for 1 hour (increased from 30 minutes)
        if time.time() - cached_time < 3600:
            print(f"🔄 Using cached response for {tool_name}")
            return cached_result
    
    # Check daily limit
    if not _check_daily_limit():
        return json.dumps({
            "error": "Daily API limit reached",
            "message": "Our AI services are at capacity today. Please try again tomorrow or contact support for immediate assistance."
        })
    
    # Aggressive rate limiting (5 seconds between calls)
    global _last_api_call, _daily_call_count
    time_since_last_call = time.time() - _last_api_call
    if time_since_last_call < _min_call_interval:
        wait_time = _min_call_interval - time_since_last_call
        print(f"⏱️ Rate limiting: waiting {wait_time:.1f} seconds before API call...")
        time.sleep(wait_time)
    
    # Create a comprehensive prompt for the specific tool
    system_prompts = {
        "search_flights": f"""You are a professional flight search assistant. Generate realistic flight search results for the user's query.

User is searching for flights with these parameters: {json.dumps(parameters)}

Provide 3-4 realistic flight options with:
- Real airline names and flight numbers
- Realistic departure/arrival times
- Appropriate prices based on route and date
- Actual aircraft types
- Real airport codes
- Realistic flight durations

Format as JSON with this structure:
{{
  "flights": [
    {{
      "flight_number": "DL1234",
      "airline": "Delta",
      "departure_time": "08:30",
      "arrival_time": "11:45",
      "price": 456,
      "duration": "3h 15m",
      "aircraft": "Boeing 737",
      "stops": 0
    }}
  ],
  "search_summary": "Found X flights from {origin} to {destination}"
}}

Be helpful, professional, and realistic.""",

        "search_hotels": f"""You are a professional hotel booking assistant. Generate realistic hotel search results.

User is searching for hotels with these parameters: {json.dumps(parameters)}

Provide 3-4 realistic hotel options with:
- Real hotel chain names and properties
- Appropriate star ratings
- Realistic nightly rates
- Actual amenities
- Real locations/neighborhoods
- Genuine room types

Format as JSON with this structure:
{{
  "hotels": [
    {{
      "name": "Marriott Downtown",
      "star_rating": 4,
      "price_per_night": 189,
      "location": "Downtown District",
      "amenities": ["WiFi", "Pool", "Gym"],
      "room_type": "Standard King"
    }}
  ],
  "search_summary": "Found X hotels in {location}"
}}""",

        "book_flight": f"""You are a flight booking assistant. Process this flight booking request.

Booking parameters: {json.dumps(parameters)}

Generate a realistic booking confirmation with:
- Confirmation number
- Booking details
- Payment processing
- Next steps for the traveler

Format as JSON:
{{
  "booking_status": "confirmed",
  "confirmation_number": "ABC123",
  "booking_details": {{ flight details }},
  "total_cost": 456,
  "message": "Your flight has been successfully booked!"
}}""",

        "book_hotel": f"""You are a hotel booking assistant. Process this hotel booking request.

Booking parameters: {json.dumps(parameters)}

Generate a realistic booking confirmation with confirmation number, details, and next steps.

Format as JSON with booking_status, confirmation_number, booking_details, total_cost, and message.""",

        "reschedule_booking": f"""You are a booking modification assistant. Handle this reschedule request.

Reschedule parameters: {json.dumps(parameters)}

Process the change request realistically - check availability, calculate any fees, provide new options.

Format as JSON with status, options, fees, and helpful message.""",

        "cancel_booking": f"""You are a cancellation assistant. Process this cancellation/refund request.

Cancellation parameters: {json.dumps(parameters)}

Handle the cancellation realistically - check cancellation policy, calculate refund amount, provide timeline.

Format as JSON with cancellation_status, refund_amount, timeline, and policy details."""
    }

    # Get the appropriate system prompt or use a default
    system_prompt = system_prompts.get(tool_name, f"""You are a helpful travel assistant. 
    Help the user with their {tool_name} request: {user_query}
    
    Parameters: {json.dumps(parameters)}
    
    Provide a helpful, realistic response in JSON format.""")

    try:
        _last_api_call = time.time()
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Please help me with: {user_query}"}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        result = response.choices[0].message.content
        
        # Cache the result
        _tool_cache[cache_key] = (result, time.time())
        
        return result
    except Exception as e:
        # Fallback response if OpenAI call fails
        return json.dumps({
            "error": f"Service temporarily unavailable: {str(e)}",
            "message": "Please try again in a moment. Our travel services are currently being updated."
        })

@tool
def search_flights(origin: str, destination: str, departure_date: str, return_date: str = None, passengers: int = 1) -> str:
    """
    Search for available flights between two cities with AI-powered results.
    
    Args:
        origin: Departure city or airport code
        destination: Arrival city or airport code  
        departure_date: Departure date (YYYY-MM-DD)
        return_date: Return date for round trip (optional)
        passengers: Number of passengers (default 1)
    
    Returns:
        JSON string with realistic flight options and search summary
    """
    parameters = {
        "origin": origin,
        "destination": destination,
        "departure_date": departure_date,
        "return_date": return_date,
        "passengers": passengers
    }
    
    user_query = f"Find flights from {origin} to {destination} on {departure_date}"
    if return_date:
        user_query += f" returning {return_date}"
    if passengers > 1:
        user_query += f" for {passengers} passengers"
    
    return _call_openai_for_tool("search_flights", user_query, parameters)

@tool
def search_hotels(location: str, check_in: str, check_out: str, guests: int = 1, budget_range: str = "any") -> str:
    """
    Search for available hotels in a location with AI-powered results.
    
    Args:
        location: City or area to search for hotels
        check_in: Check-in date (YYYY-MM-DD)
        check_out: Check-out date (YYYY-MM-DD)
        guests: Number of guests
        budget_range: Budget preference (budget/mid-range/luxury/any)
    
    Returns:
        JSON string with realistic hotel options and search summary
    """
    parameters = {
        "location": location,
        "check_in": check_in,
        "check_out": check_out,
        "guests": guests,
        "budget_range": budget_range
    }
    
    user_query = f"Find hotels in {location} from {check_in} to {check_out} for {guests} guests"
    if budget_range != "any":
        user_query += f" in {budget_range} price range"
    
    return _call_openai_for_tool("search_hotels", user_query, parameters)

@tool
def book_flight(flight_details: str, passenger_info: str) -> str:
    """
    Book a selected flight with AI-powered booking process.
    
    Args:
        flight_details: JSON string with flight information to book
        passenger_info: JSON string with passenger details
    
    Returns:
        JSON string with booking confirmation and details
    """
    parameters = {
        "flight_details": flight_details,
        "passenger_info": passenger_info
    }
    
    user_query = f"Book the flight with details: {flight_details}"
    
    return _call_openai_for_tool("book_flight", user_query, parameters)

@tool
def book_hotel(hotel_details: str, guest_info: str) -> str:
    """
    Book a selected hotel with AI-powered booking process.
    
    Args:
        hotel_details: JSON string with hotel information to book
        guest_info: JSON string with guest details
    
    Returns:
        JSON string with booking confirmation and details
    """
    parameters = {
        "hotel_details": hotel_details,
        "guest_info": guest_info
    }
    
    user_query = f"Book the hotel with details: {hotel_details}"
    
    return _call_openai_for_tool("book_hotel", user_query, parameters)

@tool
def reschedule_booking(booking_reference: str, new_date: str, booking_type: str = "flight") -> str:
    """
    Reschedule an existing booking with AI-powered change management.
    
    Args:
        booking_reference: Booking confirmation number
        new_date: New date for the booking (YYYY-MM-DD)
        booking_type: Type of booking (flight/hotel/car)
    
    Returns:
        JSON string with reschedule options, fees, and confirmation
    """
    parameters = {
        "booking_reference": booking_reference,
        "new_date": new_date,
        "booking_type": booking_type
    }
    
    user_query = f"Reschedule {booking_type} booking {booking_reference} to {new_date}"
    
    return _call_openai_for_tool("reschedule_booking", user_query, parameters)

@tool
def cancel_booking(booking_reference: str, reason: str = "change of plans") -> str:
    """
    Cancel an existing booking and process refund with AI-powered cancellation handling.
    
    Args:
        booking_reference: Booking confirmation number
        reason: Reason for cancellation
    
    Returns:
        JSON string with cancellation status, refund details, and timeline
    """
    parameters = {
        "booking_reference": booking_reference,
        "reason": reason
    }
    
    user_query = f"Cancel booking {booking_reference} due to {reason}"
    
    return _call_openai_for_tool("cancel_booking", user_query, parameters)

@tool
def get_travel_weather(destination: str, travel_date: str) -> str:
    """
    Get weather forecast for travel destination with AI-powered weather insights.
    
    Args:
        destination: City or location
        travel_date: Date of travel (YYYY-MM-DD)
    
    Returns:
        JSON string with weather forecast and travel recommendations
    """
    parameters = {
        "destination": destination,
        "travel_date": travel_date
    }
    
    user_query = f"What's the weather forecast for {destination} on {travel_date}?"
    
    system_prompt = f"""You are a weather and travel advisor. Provide realistic weather information and travel tips.

For {destination} on {travel_date}, provide:
- Temperature forecast (high/low)
- Weather conditions
- Precipitation chance
- What to pack recommendations
- Activity suggestions based on weather

Format as JSON:
{{
  "destination": "{destination}",
  "date": "{travel_date}",
  "temperature": {{ "high": 75, "low": 60, "unit": "F" }},
  "conditions": "Partly cloudy",
  "precipitation_chance": 20,
  "recommendations": ["Pack light jacket", "Great for outdoor activities"],
  "summary": "Pleasant weather expected for your trip"
}}"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            temperature=0.7,
            max_tokens=400
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return json.dumps({
            "error": "Weather service temporarily unavailable",
            "message": "Please check a weather app for current conditions."
        })

@tool
def get_travel_tips(destination: str, trip_type: str = "leisure") -> str:
    """
    Get AI-powered travel tips and recommendations for a destination.
    
    Args:
        destination: City or country to visit
        trip_type: Type of trip (leisure/business/adventure/family)
    
    Returns:
        JSON string with personalized travel tips and recommendations
    """
    parameters = {
        "destination": destination,
        "trip_type": trip_type
    }
    
    user_query = f"Give me travel tips for {trip_type} trip to {destination}"
    
    system_prompt = f"""You are an expert travel advisor. Provide helpful, accurate travel tips for {destination}.

Include:
- Best time to visit
- Must-see attractions
- Local customs/etiquette
- Transportation tips
- Food recommendations
- Safety considerations
- Budget tips
- Packing suggestions specific to {trip_type} travel

Format as JSON:
{{
  "destination": "{destination}",
  "trip_type": "{trip_type}",
  "best_time_to_visit": "Season/months",
  "must_see": ["Attraction 1", "Attraction 2"],
  "local_tips": ["Tip 1", "Tip 2"],
  "transportation": "How to get around",
  "food": "Local cuisine recommendations",
  "safety": "Important safety info",
  "summary": "Overall travel advice"
}}"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            temperature=0.7,
            max_tokens=600
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return json.dumps({
            "error": "Travel tips service temporarily unavailable",
            "message": "Please consult a travel guide for destination information."
        })

# Export all tools for the workflow
ALL_TOOLS = [
    search_flights,
    search_hotels,
    book_flight,
    book_hotel,
    reschedule_booking,
    cancel_booking,
    get_travel_weather,
    get_travel_tips
] 