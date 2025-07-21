from langchain.tools import tool
from typing import Dict, Any
import random
import json
from datetime import datetime, timedelta

# Global state to maintain consistency across ALL tool calls
_flight_cache = {}
_hotel_cache = {}
_car_rental_cache = {}
_activity_cache = {}
_insurance_cache = {}
_booking_registry = {}  # Track all bookings made

def _generate_consistent_seed(params: str) -> int:
    """Generate consistent seed for deterministic 'random' data"""
    return abs(hash(params)) % (2**31)

def _generate_consistent_flights(origin: str, destination: str, date: str, cache_key: str):
    """Generate consistent flight options for the same search parameters"""
    if cache_key in _flight_cache:
        return _flight_cache[cache_key]
    
    # Use deterministic seed based on search parameters
    random.seed(_generate_consistent_seed(f"{origin}{destination}{date}"))
    
    airlines = ["Delta", "United", "American", "Southwest", "JetBlue", "Alaska"]
    flight_options = []
    
    for i in range(3):
        airline = random.choice(airlines)
        flight_num = f"{airline[:2].upper()}{random.randint(100, 999)}"
        
        # Generate realistic departure and arrival times
        departure_hour = random.randint(6, 22)
        departure_minute = random.choice([0, 15, 30, 45])
        departure_time = f"{departure_hour:02d}:{departure_minute:02d}"
        
        # Calculate realistic arrival time (considering time zones and flight duration)
        flight_duration_hours = random.randint(2, 8)
        flight_duration_minutes = random.randint(0, 55)
        arrival_hour = (departure_hour + flight_duration_hours) % 24
        arrival_minute = (departure_minute + flight_duration_minutes) % 60
        if departure_minute + flight_duration_minutes >= 60:
            arrival_hour = (arrival_hour + 1) % 24
        arrival_time = f"{arrival_hour:02d}:{arrival_minute:02d}"
        
        price = random.randint(200, 800)
        duration = f"{flight_duration_hours}h {flight_duration_minutes}m"
        aircraft = random.choice(['Boeing 737', 'Boeing 757', 'Boeing 777', 'Airbus A320'])
        
        flight_options.append({
            "option": i + 1,
            "airline": airline,
            "flight_number": flight_num,
            "departure_time": departure_time,
            "arrival_time": arrival_time,
            "duration": duration,
            "price": price,
            "aircraft": aircraft
        })
    
    _flight_cache[cache_key] = flight_options
    return flight_options

def _generate_consistent_hotels(location: str, check_in: str, check_out: str, guests: str, cache_key: str):
    """Generate consistent hotel options"""
    if cache_key in _hotel_cache:
        return _hotel_cache[cache_key]
    
    random.seed(_generate_consistent_seed(f"{location}{check_in}{check_out}{guests}"))
    
    hotel_chains = ["Marriott", "Hilton", "Hyatt", "IHG", "Accor", "Westin"]
    hotel_types = ["Grand Hotel", "Resort & Spa", "Boutique Inn", "Business Hotel", "Downtown Hotel"]
    
    hotel_options = []
    for i in range(3):
        hotel_name = f"{random.choice(hotel_chains)} {random.choice(hotel_types)}"
        room_type = random.choice(["Standard King Room", "Deluxe Queen Room", "Executive Suite", "Ocean View Room"])
        rate = random.randint(120, 400)
        
        amenities = random.sample([
            "complimentary WiFi", "swimming pool", "fitness center", "spa services", "restaurant", 
            "room service", "business center", "airport shuttle"
        ], 4)
        
        hotel_options.append({
            "option": i + 1,
            "name": hotel_name,
            "room_type": room_type,
            "rate": rate,
            "amenities": amenities
        })
    
    _hotel_cache[cache_key] = hotel_options
    return hotel_options

@tool
def search_flights(origin: str, destination: str, date: str) -> str:
    """Search for flights. Returns consistent flight options with pricing and schedules."""
    cache_key = f"{origin}_{destination}_{date}"
    flight_options = _generate_consistent_flights(origin, destination, date, cache_key)
    
    response_lines = [f"I found {len(flight_options)} flights from {origin} to {destination} on {date}:"]
    
    for flight in flight_options:
        response_lines.append(
            f"\n{flight['option']}. {flight['airline']} Flight {flight['flight_number']} "
            f"departing at {flight['departure_time']}, arriving at {flight['arrival_time']} "
            f"({flight['duration']}) - Price: ${flight['price']}"
        )
    
    response_lines.append(f"\n\nWhich option would you like to book? Please specify the option number (1, 2, or 3).")
    
    return "\n".join(response_lines)

@tool
def book_flight(origin: str, destination: str, date: str, option_number: str, passengers: str = "1") -> str:
    """Book a specific flight option. Requires the option number from search results."""
    try:
        option_num = int(option_number)
        if option_num < 1 or option_num > 3:
            return "Invalid option number. Please choose 1, 2, or 3."
    except ValueError:
        return "Please provide a valid option number (1, 2, or 3)."
    
    cache_key = f"{origin}_{destination}_{date}"
    flight_options = _generate_consistent_flights(origin, destination, date, cache_key)
    
    if option_num > len(flight_options):
        return f"Option {option_num} is not available. Please choose from options 1-{len(flight_options)}."
    
    selected_flight = flight_options[option_num - 1]
    confirmation = f"FLT{abs(hash(f'{origin}{destination}{date}{option_num}')) % 900000 + 100000}"
    
    # Store booking in registry
    _booking_registry[confirmation] = {
        "type": "flight",
        "details": selected_flight,
        "passengers": passengers,
        "origin": origin,
        "destination": destination,
        "date": date,
        "status": "confirmed"
    }
    
    return (
        f"Perfect! I've successfully booked your flight.\n\n"
        f"Flight Details:\n"
        f"• Airline: {selected_flight['airline']}\n"
        f"• Flight Number: {selected_flight['flight_number']}\n"
        f"• Route: {origin} → {destination}\n"
        f"• Date: {date}\n"
        f"• Departure: {selected_flight['departure_time']}\n"
        f"• Arrival: {selected_flight['arrival_time']}\n"
        f"• Duration: {selected_flight['duration']}\n"
        f"• Passengers: {passengers}\n"
        f"• Price: ${selected_flight['price']} per person\n"
        f"• Confirmation: {confirmation}\n\n"
        f"Your booking is confirmed! A confirmation email has been sent to your registered email address. "
        f"Would you like me to help you with hotel accommodations or any other travel arrangements?"
    )

@tool
def search_hotels(location: str, check_in: str, check_out: str, guests: str = "2") -> str:
    """Search for hotels. Returns consistent hotel options with pricing."""
    cache_key = f"{location}_{check_in}_{check_out}_{guests}"
    hotel_options = _generate_consistent_hotels(location, check_in, check_out, guests, cache_key)
    
    response_lines = [f"I found {len(hotel_options)} hotels in {location} for {guests} guests:"]
    
    for hotel in hotel_options:
        amenities_str = ", ".join(hotel['amenities'])
        response_lines.append(
            f"\n{hotel['option']}. {hotel['name']}\n"
            f"   Room: {hotel['room_type']}\n"
            f"   Rate: ${hotel['rate']} per night\n"
            f"   Amenities: {amenities_str}"
        )
    
    response_lines.append(f"\n\nWhich hotel would you like to book? Please specify the option number (1, 2, or 3).")
    
    return "\n".join(response_lines)

@tool
def book_hotel(location: str, check_in: str, check_out: str, guests: str = "2", option_number: str = "1") -> str:
    """Book a specific hotel option. If no option specified, books option 1."""
    try:
        option_num = int(option_number)
        if option_num < 1 or option_num > 3:
            option_num = 1  # Default to first option
    except ValueError:
        option_num = 1
    
    cache_key = f"{location}_{check_in}_{check_out}_{guests}"
    hotel_options = _generate_consistent_hotels(location, check_in, check_out, guests, cache_key)
    
    selected_hotel = hotel_options[option_num - 1]
    confirmation = f"HTL{abs(hash(f'{location}{check_in}{check_out}{option_num}')) % 900000 + 100000}"
    
    # Store booking in registry
    _booking_registry[confirmation] = {
        "type": "hotel",
        "details": selected_hotel,
        "location": location,
        "check_in": check_in,
        "check_out": check_out,
        "guests": guests,
        "status": "confirmed"
    }
    
    return (
        f"Great! I've successfully booked your hotel reservation.\n\n"
        f"Hotel: {selected_hotel['name']}\n"
        f"Location: {location}\n"
        f"Check-in: {check_in}\n"
        f"Check-out: {check_out}\n"
        f"Guests: {guests}\n"
        f"Room: {selected_hotel['room_type']}\n"
        f"Rate: ${selected_hotel['rate']} per night\n"
        f"Confirmation number: {confirmation}\n\n"
        f"Your hotel includes {', '.join(selected_hotel['amenities'])}. "
        f"A confirmation email has been sent to your registered email address. "
        f"Is there anything else you need help with for your trip?"
    )

@tool
def check_booking_status(confirmation_code: str) -> str:
    """Check the status of a booking using confirmation code - uses real booking data."""
    if confirmation_code in _booking_registry:
        booking = _booking_registry[confirmation_code]
        booking_type = booking["type"]
        status = booking["status"]
        
        if booking_type == "flight":
            details = booking["details"]
            return (
                f"I found your booking! Your flight reservation {confirmation_code} is {status}.\n\n"
                f"Flight Details:\n"
                f"• {details['airline']} Flight {details['flight_number']}\n"
                f"• Route: {booking['origin']} → {booking['destination']}\n"
                f"• Date: {booking['date']}\n"
                f"• Departure: {details['departure_time']}\n"
                f"• Passengers: {booking['passengers']}\n\n"
                f"Check-in opens 24 hours before departure. Do you need any changes to this reservation?"
            )
        
        elif booking_type == "hotel":
            details = booking["details"]
            return (
                f"I found your booking! Your hotel reservation {confirmation_code} is {status}.\n\n"
                f"Hotel Details:\n"
                f"• {details['name']}\n"
                f"• Location: {booking['location']}\n"
                f"• Check-in: {booking['check_in']}\n"
                f"• Check-out: {booking['check_out']}\n"
                f"• Guests: {booking['guests']}\n"
                f"• Room: {details['room_type']}\n\n"
                f"Your reservation is all set. Do you need any modifications?"
            )
        
        else:
            return (
                f"I found your {booking_type} reservation {confirmation_code}. Status: {status}. "
                f"All details are confirmed. Let me know if you need any assistance."
            )
    
    else:
        # For demo purposes, return a helpful message for unknown codes
        return (
            f"I couldn't find a booking with confirmation code {confirmation_code}. "
            f"Please double-check the code or contact customer service if you need assistance. "
            f"Would you like me to help you with a new booking instead?"
        )

@tool
def get_travel_recommendations(destination: str, travel_style: str = "leisure") -> str:
    """Get personalized travel recommendations for a destination - consistent suggestions."""
    # Use deterministic seed for consistent recommendations
    random.seed(_generate_consistent_seed(f"{destination}{travel_style}"))
    
    attractions = {
        "Paris": ["Eiffel Tower", "Louvre Museum", "Notre-Dame Cathedral", "Champs-Élysées", "Montmartre district"],
        "Tokyo": ["Tokyo Tower", "Senso-ji Temple", "Shibuya Crossing", "Mount Fuji day trip", "Tsukiji Fish Market"],
        "Kyoto": ["Fushimi Inari Shrine", "Kinkaku-ji Temple", "Arashiyama Bamboo Grove", "Gion District", "Philosopher's Path"],
        "New York": ["Statue of Liberty", "Central Park", "Times Square", "9/11 Memorial", "Brooklyn Bridge"],
        "London": ["Big Ben", "London Eye", "British Museum", "Tower Bridge", "Buckingham Palace"],
        "Detroit": ["Detroit Institute of Arts", "Henry Ford Museum", "Eastern Market", "Belle Isle Park", "Motown Museum"]
    }
    
    restaurants = {
        "Paris": ["Le Jules Verne", "L'Ambroisie", "Bistrot Paul Bert"],
        "Tokyo": ["Sukiyabashi Jiro", "Narisawa", "Tsuta Ramen"],
        "Kyoto": ["Kikunoi", "Yoshikawa", "Ganko Sushi"],
        "New York": ["Le Bernardin", "Eleven Madison Park", "Joe's Pizza"],
        "London": ["The Ledbury", "Dishoom", "Borough Market"],
        "Detroit": ["Grey Ghost Detroit", "Selden Standard", "Lafayette Coney Island"]
    }
    
    dest_attractions = attractions.get(destination, ["the historic downtown area", "local museums", "city parks"])
    dest_restaurants = restaurants.get(destination, ["highly-rated local restaurants", "traditional cafes"])
    
    # Consistently select same attractions for same destination
    selected_attractions = dest_attractions[:3]
    selected_restaurants = dest_restaurants[:2]
    
    return (
        f"For your {travel_style} trip to {destination}, I recommend visiting {', '.join(selected_attractions)}. "
        f"For dining, definitely try {' and '.join(selected_restaurants)}. "
        f"Based on your travel style, I'd suggest planning 3-4 days to really enjoy everything the city has to offer. "
        f"Would you like me to help you plan a detailed itinerary or book any specific activities?"
    )

@tool
def cancel_or_modify_booking(confirmation_code: str, action: str, new_details: str = "") -> str:
    """Cancel or modify a booking - works with real booking data."""
    if confirmation_code not in _booking_registry:
        return (
            f"I couldn't find a booking with confirmation code {confirmation_code}. "
            f"Please check the code and try again."
        )
    
    booking = _booking_registry[confirmation_code]
    booking_type = booking["type"]
    
    if action.lower() == "cancel":
        booking["status"] = "cancelled"
        return (
            f"I've successfully cancelled your {booking_type} reservation {confirmation_code}. "
            f"You should receive a cancellation confirmation email shortly. "
            f"Depending on the booking terms, you may be eligible for a refund. "
            f"Is there anything else I can help you with?"
        )
    
    elif action.lower() == "modify":
        booking["status"] = "modified"
        return (
            f"I've noted your request to modify {booking_type} reservation {confirmation_code}. "
            f"Changes requested: {new_details}. "
            f"I'm processing this modification and you'll receive an updated confirmation shortly. "
            f"Please note that changes may be subject to availability and additional fees."
        )
    
    else:
        return (
            f"I can help you cancel or modify your booking {confirmation_code}. "
            f"Please specify whether you'd like to 'cancel' or 'modify' this reservation."
        )

@tool  
def get_weather_forecast(destination: str, date: str) -> str:
    """Get weather forecast for destination - consistent weather based on location and season."""
    # Use deterministic seed for consistent weather
    random.seed(_generate_consistent_seed(f"{destination}{date}"))
    
    # Define climate patterns for different destinations
    weather_patterns = {
        "Tokyo": {"summer": [75, 85, "humid"], "winter": [35, 45, "dry"], "spring": [55, 70, "mild"], "fall": [60, 75, "pleasant"]},
        "Kyoto": {"summer": [78, 88, "humid"], "winter": [32, 42, "cool"], "spring": [58, 72, "comfortable"], "fall": [62, 77, "crisp"]},
        "Paris": {"summer": [68, 78, "mild"], "winter": [38, 48, "cool"], "spring": [52, 65, "variable"], "fall": [55, 68, "wet"]},
        "London": {"summer": [60, 70, "variable"], "winter": [40, 50, "damp"], "spring": [48, 60, "unpredictable"], "fall": [50, 62, "rainy"]},
        "New York": {"summer": [75, 85, "hot"], "winter": [30, 45, "cold"], "spring": [55, 70, "variable"], "fall": [60, 75, "comfortable"]},
        "Detroit": {"summer": [70, 80, "warm"], "winter": [20, 35, "cold"], "spring": [50, 65, "cool"], "fall": [55, 70, "mild"]}
    }
    
    # Determine season from date (simplified)
    month = date.split('-')[1] if '-' in date else date.split('/')[0] if '/' in date else "07"
    month_num = int(month)
    
    if month_num in [6, 7, 8]:
        season = "summer"
    elif month_num in [12, 1, 2]:
        season = "winter"
    elif month_num in [3, 4, 5]:
        season = "spring"
    else:
        season = "fall"
    
    pattern = weather_patterns.get(destination, {"summer": [70, 80, "pleasant"], "winter": [40, 50, "cool"], "spring": [55, 70, "mild"], "fall": [60, 75, "comfortable"]})
    season_weather = pattern.get(season, [65, 75, "moderate"])
    
    temp_low, temp_high, condition = season_weather
    temp = random.randint(temp_low, temp_high)
    
    conditions = ["sunny", "partly cloudy", "cloudy", "light rain", "clear"]
    weather_condition = random.choice(conditions)
    
    return (
        f"Weather forecast for {destination} on {date}:\n"
        f"Temperature: {temp}°F\n"
        f"Conditions: {weather_condition.title()}\n"
        f"General climate: {condition}\n\n"
        f"Perfect weather for sightseeing! Pack layers and comfortable walking shoes. "
        f"Check the forecast again closer to your travel date for any updates."
    )

@tool
def search_car_rentals(location: str, pickup_date: str, return_date: str) -> str:
    """Search for car rentals - consistent options based on location."""
    # Use deterministic seed for consistent car options
    random.seed(_generate_consistent_seed(f"{location}{pickup_date}{return_date}"))
    
    car_companies = ["Hertz", "Enterprise", "Avis", "Budget", "National"]
    car_types = [
        {"name": "Economy", "example": "Nissan Versa", "price_base": 25},
        {"name": "Compact", "example": "Toyota Corolla", "price_base": 35},
        {"name": "Mid-size", "example": "Honda Accord", "price_base": 45},
        {"name": "Full-size", "example": "Chevrolet Malibu", "price_base": 55},
        {"name": "SUV", "example": "Ford Explorer", "price_base": 75}
    ]
    
    response_lines = [f"Car rental options in {location} from {pickup_date} to {return_date}:"]
    
    for i, car_type in enumerate(car_types[:3]):  # Show 3 consistent options
        company = car_companies[i % len(car_companies)]
        daily_rate = car_type["price_base"] + random.randint(-5, 15)
        
        response_lines.append(
            f"\n{i+1}. {car_type['name']} - {car_type['example']}\n"
            f"   Company: {company}\n"
            f"   Rate: ${daily_rate}/day\n"
            f"   Features: Air conditioning, automatic transmission"
        )
    
    response_lines.append(f"\n\nWhich car would you like to reserve? Please specify the option number.")
    
    return "\n".join(response_lines)

@tool
def book_activities(location: str, activity_type: str, date: str, guests: str = "2") -> str:
    """Book activities like tours, restaurants, attractions, shows - consistent options."""
    # Use deterministic seed for consistent activity booking
    random.seed(_generate_consistent_seed(f"{location}{activity_type}{date}{guests}"))
    
    confirmation = f"{activity_type[:3].upper()}{abs(hash(f'{location}{activity_type}{date}')) % 900000 + 100000}"
    
    if activity_type.lower() == "restaurant":
        restaurants = {
            "Tokyo": ["Sukiyabashi Jiro", "Narisawa", "Tsuta Ramen"],
            "Kyoto": ["Kikunoi", "Yoshikawa", "Ganko Sushi"],
            "Paris": ["Le Jules Verne", "L'Ambroisie", "Bistrot Paul Bert"],
            "New York": ["Le Bernardin", "Eleven Madison Park", "Joe's Pizza"],
            "Detroit": ["Grey Ghost Detroit", "Selden Standard", "Lafayette Coney Island"]
        }
        
        location_restaurants = restaurants.get(location, ["Local Fine Dining", "Traditional Restaurant", "Popular Bistro"])
        restaurant = location_restaurants[0]  # Consistently pick first option
        time_slot = "7:30 PM"  # Consistent time
        
        return (
            f"Perfect! I've secured your restaurant reservation.\n\n"
            f"Restaurant: {restaurant}\n"
            f"Date: {date}\n"
            f"Time: {time_slot}\n"
            f"Party size: {guests} guests\n"
            f"Confirmation: {confirmation}\n\n"
            f"The restaurant will hold your table for 15 minutes past your reservation time. "
            f"Please call if you're running late. Dress code is smart casual."
        )
    
    elif activity_type.lower() == "tour":
        tours = {
            "Tokyo": "Traditional Culture & Temples Tour",
            "Kyoto": "Ancient Temples & Bamboo Forest Tour", 
            "Paris": "Historic Landmarks & Art Tour",
            "New York": "Manhattan Highlights Walking Tour",
            "Detroit": "Automotive Heritage & Arts Tour"
        }
        
        tour = tours.get(location, "City Highlights Tour")
        duration = "4 hours"
        price = 85
        
        return (
            f"Excellent! Your tour is booked.\n\n"
            f"Tour: {tour}\n"
            f"Date: {date}\n"
            f"Duration: {duration}\n"
            f"Participants: {guests}\n"
            f"Price: ${price} per person\n"
            f"Confirmation: {confirmation}\n\n"
            f"Meet your guide at the main entrance 15 minutes before start time. "
            f"Comfortable walking shoes recommended."
        )
    
    else:  # attractions or shows
        attractions = {
            "Tokyo": "Tokyo Tower Observatory",
            "Kyoto": "Fushimi Inari Shrine Experience",
            "Paris": "Louvre Museum Skip-the-Line",
            "New York": "Statue of Liberty & Ellis Island",
            "Detroit": "Henry Ford Museum"
        }
        
        attraction = attractions.get(location, "Local Main Attraction")
        time_slot = "10:00 AM"
        price = 35
        
        return (
            f"Great! Your attraction tickets are confirmed.\n\n"
            f"Attraction: {attraction}\n"
            f"Date: {date}\n"
            f"Time: {time_slot}\n"
            f"Tickets: {guests}\n"
            f"Price: ${price} per ticket\n"
            f"Confirmation: {confirmation}\n\n"
            f"Tickets are valid for the entire day. Audio guides available in multiple languages."
        )

@tool
def get_travel_insurance(trip_cost: str, destination: str, travelers: str = "1", trip_duration: str = "7") -> str:
    """Get travel insurance quotes - consistent pricing based on trip details."""
    # Use deterministic calculation for consistent quotes
    trip_cost_num = float(trip_cost.replace('$', '').replace(',', ''))
    duration_num = int(trip_duration.split()[0]) if 'day' in trip_duration else int(trip_duration)
    travelers_num = int(travelers)
    
    # Consistent pricing formula
    base_premium = trip_cost_num * 0.05  # 5% of trip cost
    duration_factor = max(1, duration_num / 7)  # Weekly basis
    traveler_factor = travelers_num
    
    basic_premium = round(base_premium * duration_factor * traveler_factor * 0.8, 2)
    comprehensive_premium = round(base_premium * duration_factor * traveler_factor * 1.2, 2)
    premium_premium = round(base_premium * duration_factor * traveler_factor * 1.6, 2)
    
    return (
        f"Travel insurance options for your {duration_num}-day trip to {destination} ({travelers_num} travelers):\n\n"
        f"1. Basic Coverage (${basic_premium}):\n"
        f"   Trip cancellation up to ${trip_cost_num:,.0f}, medical emergency $50,000, baggage loss $1,500\n\n"
        f"2. Comprehensive Coverage (${comprehensive_premium}):\n"
        f"   Trip cancellation up to ${trip_cost_num:,.0f}, medical emergency $100,000, baggage loss $2,500, trip interruption\n\n"
        f"3. Premium Coverage (${premium_premium}):\n"
        f"   Trip cancellation up to ${trip_cost_num:,.0f}, medical emergency $250,000, baggage loss $5,000, adventure sports, rental car protection\n\n"
        f"All plans include 24/7 emergency assistance and COVID-19 coverage. Which option interests you?"
    )

@tool
def check_visa_requirements(destination: str, nationality: str = "US") -> str:
    """Check visa requirements - consistent information based on destination and nationality."""
    # Visa requirements database (simplified but consistent)
    visa_info = {
        "Japan": {
            "US": "90-day tourist visa waiver available",
            "requirements": "Valid passport, return ticket, sufficient funds"
        },
        "UK": {
            "US": "6-month tourist visa waiver available", 
            "requirements": "Valid passport, return ticket, accommodation proof"
        },
        "France": {
            "US": "90-day Schengen tourist visa waiver",
            "requirements": "Valid passport, return ticket within 90 days"
        },
        "China": {
            "US": "Tourist visa required in advance",
            "requirements": "Valid passport, visa application, invitation letter or tour booking"
        }
    }
    
    country_info = visa_info.get(destination, {
        "US": "Please check with embassy for current requirements",
        "requirements": "Valid passport required, check embassy website for visa needs"
    })
    
    visa_status = country_info.get(nationality, country_info.get("US", "Check embassy requirements"))
    requirements = country_info.get("requirements", "Standard travel documents required")
    
    return (
        f"Visa requirements for {nationality} citizens traveling to {destination}:\n\n"
        f"Status: {visa_status}\n"
        f"Requirements: {requirements}\n\n"
        f"I recommend checking with the embassy or consulate for the most current information, "
        f"especially for any recent policy changes. Processing times can vary, so apply early if a visa is needed."
    )

@tool
def convert_currency(amount: str, from_currency: str, to_currency: str) -> str:
    """Convert currency - consistent exchange rates for demo purposes."""
    # Use deterministic exchange rates for consistency
    exchange_rates = {
        "USD_EUR": 0.85, "EUR_USD": 1.18,
        "USD_JPY": 110.0, "JPY_USD": 0.009,
        "USD_GBP": 0.73, "GBP_USD": 1.37,
        "EUR_JPY": 129.0, "JPY_EUR": 0.0077,
        "GBP_JPY": 150.0, "JPY_GBP": 0.0067
    }
    
    amount_num = float(amount.replace(',', ''))
    rate_key = f"{from_currency}_{to_currency}"
    
    if rate_key in exchange_rates:
        rate = exchange_rates[rate_key]
    else:
        # Default rate for demo
        rate = 1.0
    
    converted_amount = round(amount_num * rate, 2)
    
    return (
        f"{amount} {from_currency} equals {converted_amount:,.2f} {to_currency}\n"
        f"Exchange rate: 1 {from_currency} = {rate:.4f} {to_currency}\n\n"
        f"Exchange rates are for reference only. Actual rates may vary by provider. "
        f"Most banks and exchange services charge a 2-4% fee on top of the market rate."
    )

@tool
def get_travel_alerts(destination: str) -> str:
    """Get travel alerts - consistent safety information based on destination."""
    # Consistent alert levels for destinations
    alert_levels = {
        "Japan": "all clear",
        "UK": "all clear", 
        "France": "low",
        "Germany": "all clear",
        "Italy": "low",
        "Spain": "low",
        "China": "moderate",
        "Thailand": "low",
        "Mexico": "moderate"
    }
    
    alert_level = alert_levels.get(destination, "low")
    
    if alert_level == "all clear":
        return (
            f"Current status for {destination}: All clear! "
            f"No significant travel advisories at this time. "
            f"Standard precautions recommended: keep copies of important documents, "
            f"register with your embassy if staying long-term, and follow local laws and customs. "
            f"Safe travels!"
        )
    elif alert_level == "low":
        return (
            f"Travel Advisory for {destination} (Low Risk): "
            f"Generally safe for travelers with standard precautions. "
            f"Stay aware of your surroundings, avoid isolated areas at night, "
            f"and keep important documents secure. "
            f"Monitor local news for any updates during your stay."
        )
    else:
        return (
            f"Travel Advisory for {destination} (Moderate Risk): "
            f"Exercise increased caution. Stay informed about local conditions, "
            f"avoid demonstrations and large gatherings, "
            f"and maintain a high level of security awareness. "
            f"Register with your embassy upon arrival."
        )

# Updated ALL_TOOLS dictionary with all fixed tools
ALL_TOOLS: Dict[str, Any] = {
    "search_flights": search_flights,
    "book_flight": book_flight,
    "search_hotels": search_hotels,
    "book_hotel": book_hotel,
    "check_booking_status": check_booking_status,
    "get_travel_recommendations": get_travel_recommendations,
    "cancel_or_modify_booking": cancel_or_modify_booking,
    "get_weather_forecast": get_weather_forecast,
    "search_car_rentals": search_car_rentals,
    "book_activities": book_activities,
    "get_travel_insurance": get_travel_insurance,
    "check_visa_requirements": check_visa_requirements,
    "convert_currency": convert_currency,
    "get_travel_alerts": get_travel_alerts,
} 