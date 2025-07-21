from langchain.tools import tool
from typing import Dict, Any
import random
import json

# ---- Enhanced Travel Tools with Natural Language Responses ----

@tool
def search_flights(origin: str, destination: str, date: str) -> str:
    """Search for flights. Returns flight options with pricing and schedules."""
    airlines = ["Delta", "United", "American", "Southwest", "JetBlue", "Alaska"]
    flight_options = []
    
    for i in range(3):
        airline = random.choice(airlines)
        flight_num = f"{airline[:2].upper()}{random.randint(100, 999)}"
        departure_time = f"{random.randint(6, 23):02d}:{random.choice(['00', '15', '30', '45'])}"
        arrival_time = f"{random.randint(6, 23):02d}:{random.choice(['00', '15', '30', '45'])}"
        price = random.randint(200, 800)
        duration = f"{random.randint(2, 8)}h {random.randint(0, 55)}m"
        aircraft = random.choice(['Boeing 737', 'Boeing 757', 'Boeing 777', 'Airbus A320'])
        
        flight_options.append(
            f"Option {i+1}: {airline} flight {flight_num} departing {departure_time}, arriving {arrival_time} ({duration}). Price: ${price}. Aircraft: {aircraft}, seats available."
        )
    
    return (
        f"I found {len(flight_options)} flights from {origin} to {destination} on {date}:\n\n" +
        "\n\n".join(flight_options) +
        "\n\nBased on your travel history, I'd recommend booking soon for the best prices. Would you like me to help you book one of these options?"
    )

@tool
def book_hotel(location: str, check_in: str, check_out: str, guests: str = "2") -> str:
    """Book a hotel. Returns confirmation details and options."""
    hotel_chains = ["Marriott", "Hilton", "Hyatt", "IHG", "Accor", "Westin"]
    hotel_types = ["Grand Hotel", "Resort & Spa", "Boutique Inn", "Business Hotel", "Downtown Hotel"]
    
    hotel_name = f"{random.choice(hotel_chains)} {random.choice(hotel_types)}"
    confirmation = f"HTL{random.randint(100000, 999999)}"
    room_type = random.choice(["Standard King Room", "Deluxe Queen Room", "Executive Suite", "Ocean View Room"])
    rate = random.randint(120, 400)
    
    amenities = random.sample([
        "complimentary WiFi", "swimming pool", "fitness center", "spa services", "restaurant", 
        "room service", "business center", "airport shuttle"
    ], 4)
    
    return (
        f"Great! I've successfully booked your hotel reservation.\n\n"
        f"Hotel: {hotel_name}\n"
        f"Location: {location}\n"
        f"Check-in: {check_in}\n"
        f"Check-out: {check_out}\n"
        f"Guests: {guests}\n"
        f"Room: {room_type}\n"
        f"Rate: ${rate} per night\n"
        f"Confirmation number: {confirmation}\n\n"
        f"Your hotel includes {', '.join(amenities)}. "
        f"A confirmation email has been sent to your registered email address. "
        f"Is there anything else you need help with for your trip?"
    )

@tool
def check_booking_status(confirmation_code: str) -> str:
    """Check the status of a booking using confirmation code."""
    booking_types = ["flight", "hotel", "car rental", "vacation package"]
    statuses = ["confirmed", "pending", "cancelled", "completed"]
    
    booking_type = random.choice(booking_types)
    status = random.choice(statuses)
    
    if status == "confirmed":
        return (
            f"I found your booking! Your {booking_type} reservation {confirmation_code} is confirmed and all set. "
            f"Check-in opens 24 hours before your travel date. You can download our mobile app for easy access to your booking details. "
            f"Do you need any changes to this reservation?"
        )
    elif status == "pending":
        return (
            f"Your {booking_type} booking {confirmation_code} is currently being processed. "
            f"You should receive confirmation within 24 hours. "
            f"If you don't hear back by then, please let me know and I can contact customer service for you."
        )
    else:
        return (
            f"I see that your {booking_type} reservation {confirmation_code} has been {status}. "
            f"If you need to make new arrangements, I'd be happy to help you find alternatives."
        )

@tool
def get_travel_recommendations(destination: str, travel_style: str = "leisure") -> str:
    """Get personalized travel recommendations for a destination."""
    attractions = {
        "Paris": ["Eiffel Tower", "Louvre Museum", "Notre-Dame Cathedral", "Champs-Élysées", "Montmartre district"],
        "Tokyo": ["Tokyo Tower", "Senso-ji Temple", "Shibuya Crossing", "day trip to Mount Fuji", "Tsukiji Fish Market"],
        "New York": ["Statue of Liberty", "Central Park", "Times Square", "9/11 Memorial", "Brooklyn Bridge"],
        "London": ["Big Ben", "London Eye", "British Museum", "Tower Bridge", "Buckingham Palace"]
    }
    
    restaurants = {
        "Paris": ["Le Jules Verne", "L'Ambroisie", "Bistrot Paul Bert"],
        "Tokyo": ["Sukiyabashi Jiro", "Narisawa", "Tsuta Ramen"],
        "New York": ["Le Bernardin", "Eleven Madison Park", "Joe's Pizza"],
        "London": ["The Ledbury", "Dishoom", "Borough Market"]
    }
    
    dest_attractions = attractions.get(destination, ["the historic downtown area", "local museums", "city parks"])
    dest_restaurants = restaurants.get(destination, ["highly-rated local restaurants", "traditional cafes"])
    
    selected_attractions = random.sample(dest_attractions, min(3, len(dest_attractions)))
    selected_restaurants = random.sample(dest_restaurants, min(2, len(dest_restaurants)))
    
    return (
        f"For your trip to {destination}, I'd recommend visiting {', '.join(selected_attractions)}. "
        f"For dining, definitely try {' and '.join(selected_restaurants)}. "
        f"Based on your {travel_style} travel style, I'd suggest planning 3-4 days to really enjoy everything the city has to offer. "
        f"Would you like me to help you plan a detailed itinerary?"
    )

@tool
def cancel_or_modify_booking(confirmation_code: str, action: str) -> str:
    """Cancel or modify a booking. Actions: 'cancel', 'modify_dates', 'modify_passengers'."""
    
    if action == "cancel":
        refund_amount = round(random.uniform(150, 500), 2)
        return (
            f"I've processed the cancellation for booking {confirmation_code}. "
            f"A refund of ${refund_amount} will be credited to your original payment method within 5-7 business days. "
            f"You'll receive a cancellation confirmation email shortly. "
            f"If you need help finding alternative travel options, I'm here to assist!"
        )
    elif action == "modify_dates":
        change_fee = random.randint(25, 75)
        return (
            f"I've submitted your date change request for booking {confirmation_code}. "
            f"There's a ${change_fee} change fee for this modification. "
            f"Our travel specialist will contact you within 2 hours to confirm the new dates and process payment. "
            f"Flexible date options sometimes have lower fees, so they'll discuss all available options with you."
        )
    else:
        return (
            f"Your modification request for booking {confirmation_code} has been received. "
            f"A customer service representative will call you within 1 hour to discuss the changes you need. "
            f"Please note that some modifications may include additional fees depending on the specific changes."
        )

@tool  
def get_weather_forecast(destination: str, date: str) -> str:
    """Get weather forecast for a destination on a specific date."""
    conditions = ["sunny", "partly cloudy", "cloudy", "light rain", "rainy", "clear"]
    temp_ranges = [(65, 75), (70, 80), (50, 65), (45, 60), (75, 85)]
    
    condition = random.choice(conditions)
    temp_min, temp_max = random.choice(temp_ranges)
    humidity = random.randint(40, 80)
    wind_speed = random.randint(5, 15)
    
    clothing_advice = {
        "sunny": "Pack light clothing, sunglasses, and sunscreen",
        "partly cloudy": "Bring comfortable layers and a light jacket",
        "cloudy": "A light jacket or sweater would be good",
        "light rain": "Don't forget an umbrella and light rain jacket",
        "rainy": "Pack a waterproof jacket and umbrella",
        "clear": "Perfect weather for outdoor activities"
    }
    
    return (
        f"The weather forecast for {destination} on {date} shows {condition} conditions "
        f"with temperatures between {temp_min}°F and {temp_max}°F. "
        f"Humidity will be around {humidity}% with winds at {wind_speed} mph. "
        f"{clothing_advice.get(condition, 'Check the weather again closer to your travel date')}. "
        f"I'd recommend checking the forecast again closer to your departure for the most up-to-date information."
    )

@tool
def search_car_rentals(location: str, pickup_date: str, return_date: str, car_type: str = "economy") -> str:
    """Search for car rental options. Car types: economy, compact, midsize, fullsize, luxury, suv."""
    rental_companies = ["Hertz", "Enterprise", "Avis", "Budget", "Alamo", "National"]
    car_models = {
        "economy": ["Nissan Versa", "Chevrolet Spark", "Mitsubishi Mirage"],
        "compact": ["Nissan Sentra", "Chevrolet Cruze", "Honda Civic"],
        "midsize": ["Toyota Camry", "Nissan Altima", "Chevrolet Malibu"],
        "fullsize": ["Chevrolet Impala", "Toyota Avalon", "Chrysler 300"],
        "luxury": ["BMW 3 Series", "Mercedes C-Class", "Audi A4"],
        "suv": ["Chevrolet Tahoe", "Ford Explorer", "Jeep Grand Cherokee"]
    }
    
    options = []
    for i in range(3):
        company = random.choice(rental_companies)
        model = random.choice(car_models.get(car_type, car_models["economy"]))
        daily_rate = random.randint(25, 120)
        
        features = random.sample([
            "unlimited mileage", "GPS included", "free cancellation", "roadside assistance", 
            "additional driver included", "fuel-efficient", "automatic transmission"
        ], 3)
        
        options.append(
            f"{company}: {model} at ${daily_rate}/day with {', '.join(features)}"
        )
    
    return (
        f"I found {len(options)} car rental options in {location} from {pickup_date} to {return_date}:\n\n" +
        "\n\n".join(options) +
        f"\n\nAll vehicles include basic insurance coverage. Would you like me to proceed with booking one of these options?"
    )

@tool
def book_activities(destination: str, activity_type: str, date: str, guests: str = "2") -> str:
    """Book tours, attractions, or restaurant reservations. Activity types: tours, attractions, restaurants, shows."""
    
    if activity_type == "restaurants":
        restaurants = ["Le Bernardin", "Eleven Madison Park", "Per Se", "Daniel", "Jean-Georges"]
        restaurant = random.choice(restaurants)
        time_slot = random.choice(["6:00 PM", "7:30 PM", "8:00 PM", "8:30 PM"])
        confirmation = f"RST{random.randint(100000, 999999)}"
        
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
    
    elif activity_type == "tours":
        tours = [
            "City Walking Tour", "Food & Culture Tour", "Historical Landmarks Tour", 
            "Photography Walking Tour", "Local Markets Tour", "Architecture Tour"
        ]
        tour = random.choice(tours)
        duration = random.choice(["2 hours", "3 hours", "4 hours", "Half day"])
        price = random.randint(45, 150)
        confirmation = f"TOR{random.randint(100000, 999999)}"
        
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
    
    elif activity_type == "attractions":
        attractions = [
            "Museum of Modern Art", "Historical Palace Tour", "Observatory Deck", 
            "Botanical Gardens", "Science Museum", "Art Gallery Exhibition"
        ]
        attraction = random.choice(attractions)
        time_slot = random.choice(["10:00 AM", "12:00 PM", "2:00 PM", "4:00 PM"])
        price = random.randint(15, 65)
        confirmation = f"ATT{random.randint(100000, 999999)}"
        
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
    
    else:  # shows
        shows = ["Broadway Musical", "Concert Hall Performance", "Opera", "Comedy Show", "Jazz Club"]
        show = random.choice(shows)
        time_slot = random.choice(["7:00 PM", "7:30 PM", "8:00 PM", "8:30 PM"])
        price = random.randint(75, 250)
        confirmation = f"SHW{random.randint(100000, 999999)}"
        
        return (
            f"Wonderful! Your show tickets are booked.\n\n"
            f"Show: {show}\n"
            f"Date: {date}\n"
            f"Time: {time_slot}\n"
            f"Tickets: {guests}\n"
            f"Price: ${price} per ticket\n"
            f"Confirmation: {confirmation}\n\n"
            f"Please arrive 30 minutes early. No photography during performance."
        )

@tool
def get_travel_insurance(trip_cost: str, destination: str, travelers: str = "1", trip_duration: str = "7") -> str:
    """Get travel insurance quotes and coverage options."""
    
    trip_cost_num = float(trip_cost.replace('$', '').replace(',', ''))
    duration_num = int(trip_duration.split()[0]) if 'day' in trip_duration else int(trip_duration)
    travelers_num = int(travelers)
    
    base_premium = trip_cost_num * 0.05  # 5% of trip cost
    duration_factor = max(1, duration_num / 7)  # Weekly basis
    traveler_factor = travelers_num
    
    basic_premium = round(base_premium * duration_factor * traveler_factor * 0.8, 2)
    comprehensive_premium = round(base_premium * duration_factor * traveler_factor * 1.2, 2)
    premium_premium = round(base_premium * duration_factor * traveler_factor * 1.6, 2)
    
    return (
        f"Here are travel insurance options for your {duration_num}-day trip to {destination}:\n\n"
        f"Basic Coverage (${basic_premium}):\n"
        f"Trip cancellation up to ${trip_cost}, medical emergency ${50000}, baggage loss ${1500}\n\n"
        f"Comprehensive Coverage (${comprehensive_premium}):\n"
        f"Trip cancellation up to ${trip_cost}, medical emergency ${100000}, baggage loss ${2500}, trip interruption coverage\n\n"
        f"Premium Coverage (${premium_premium}):\n"
        f"Trip cancellation up to ${trip_cost}, medical emergency ${250000}, baggage loss ${5000}, adventure sports coverage, rental car protection\n\n"
        f"All plans include 24/7 emergency assistance and COVID-19 coverage. "
        f"Would you like me to proceed with purchasing one of these policies?"
    )

@tool
def check_visa_requirements(destination_country: str, passport_country: str, trip_purpose: str = "tourism") -> str:
    """Check visa requirements and provide application assistance."""
    
    # Simulate common visa scenarios
    visa_free_countries = ["Canada", "UK", "France", "Germany", "Japan", "Australia", "South Korea"]
    visa_on_arrival = ["Egypt", "Jordan", "Nepal", "Cambodia", "Laos", "Madagascar"]
    visa_required = ["China", "Russia", "India", "Brazil", "Vietnam", "Myanmar"]
    
    if destination_country in visa_free_countries:
        stay_duration = random.choice(["90 days", "180 days", "6 months"])
        return (
            f"Good news! Citizens of {passport_country} can enter {destination_country} visa-free for {trip_purpose} purposes. "
            f"You can stay up to {stay_duration} without a visa. "
            f"Just ensure your passport is valid for at least 6 months from your travel date. "
            f"No additional documentation required for short-term visits."
        )
    
    elif destination_country in visa_on_arrival:
        fee = random.randint(25, 75)
        validity = random.choice(["30 days", "60 days", "90 days"])
        return (
            f"Citizens of {passport_country} can obtain a visa on arrival for {destination_country}. "
            f"Fee: ${fee} (cash or card accepted). "
            f"Validity: {validity}. "
            f"Required documents: valid passport, return ticket, hotel booking confirmation, and passport photos. "
            f"Processing time is typically 15-30 minutes at the airport."
        )
    
    else:  # visa required
        processing_time = random.choice(["5-10 business days", "10-15 business days", "2-3 weeks"])
        fee = random.randint(60, 180)
        return (
            f"A visa is required for citizens of {passport_country} traveling to {destination_country} for {trip_purpose}. "
            f"Application fee: ${fee}. "
            f"Processing time: {processing_time}. "
            f"Required documents: completed application, passport photos, bank statements, travel itinerary, and hotel bookings. "
            f"I recommend applying at least 3-4 weeks before your travel date. "
            f"Would you like assistance finding the nearest embassy or consulate?"
        )

@tool
def convert_currency(amount: str, from_currency: str, to_currency: str) -> str:
    """Convert currency with current exchange rates."""
    
    # Mock exchange rates (in a real app, these would come from a live API)
    exchange_rates = {
        "USD": {"EUR": 0.85, "GBP": 0.73, "JPY": 110.0, "CAD": 1.25, "AUD": 1.35, "CHF": 0.92},
        "EUR": {"USD": 1.18, "GBP": 0.86, "JPY": 129.0, "CAD": 1.47, "AUD": 1.59, "CHF": 1.08},
        "GBP": {"USD": 1.37, "EUR": 1.16, "JPY": 150.0, "CAD": 1.71, "AUD": 1.85, "CHF": 1.26},
        "JPY": {"USD": 0.0091, "EUR": 0.0078, "GBP": 0.0067, "CAD": 0.011, "AUD": 0.012, "CHF": 0.0084},
    }
    
    amount_num = float(amount.replace(',', ''))
    
    if from_currency == to_currency:
        return f"{amount} {from_currency} equals {amount} {to_currency} (same currency)"
    
    # Get exchange rate
    rate = exchange_rates.get(from_currency, {}).get(to_currency, 1.0)
    if rate == 1.0 and from_currency != to_currency:
        # If we don't have the rate, simulate one
        rate = random.uniform(0.5, 2.0)
    
    converted_amount = round(amount_num * rate, 2)
    
    return (
        f"{amount} {from_currency} equals {converted_amount:,.2f} {to_currency}\n"
        f"Exchange rate: 1 {from_currency} = {rate:.4f} {to_currency}\n\n"
        f"Exchange rates fluctuate daily. For large transactions, I recommend checking rates closer to your exchange date. "
        f"Most banks and exchange services charge a 2-4% fee on top of the market rate."
    )

@tool
def get_travel_alerts(destination: str) -> str:
    """Get current travel alerts, warnings, and health advisories for a destination."""
    
    alert_types = ["health advisory", "weather warning", "security notice", "transportation disruption", "all clear"]
    alert_levels = ["low", "moderate", "high"]
    
    alert_type = random.choice(alert_types)
    alert_level = random.choice(alert_levels)
    
    if alert_type == "all clear":
        return (
            f"Current status for {destination}: All clear! "
            f"No significant travel advisories at this time. "
            f"Standard precautions recommended: keep copies of important documents, "
            f"register with your embassy if staying long-term, and follow local laws and customs. "
            f"Check back before departure for any updates."
        )
    
    elif alert_type == "health advisory":
        if alert_level == "low":
            return (
                f"Health Advisory for {destination} (Low Risk): "
                f"Routine vaccinations recommended (measles, DPT, flu). "
                f"No specific health risks reported. "
                f"Standard travel health precautions advised: drink bottled water, "
                f"avoid street food if you have a sensitive stomach, and bring basic medications."
            )
        elif alert_level == "moderate":
            return (
                f"Health Advisory for {destination} (Moderate Risk): "
                f"Additional vaccinations may be recommended (Hepatitis A/B, Typhoid). "
                f"Seasonal flu outbreak reported in some regions. "
                f"Take precautions with food and water. Consider travel health insurance. "
                f"Consult your doctor 4-6 weeks before travel."
            )
        else:
            return (
                f"Health Advisory for {destination} (High Risk): "
                f"Multiple health concerns reported. Specialized vaccinations required. "
                f"Consult a travel medicine specialist immediately. "
                f"Consider postponing non-essential travel. "
                f"If travel is necessary, take maximum precautions and ensure comprehensive health insurance."
            )
    
    elif alert_type == "security notice":
        return (
            f"Security Notice for {destination} ({alert_level.title()} Risk): "
            f"Elevated security concerns in certain areas. "
            f"Avoid large gatherings and demonstrations. "
            f"Stay alert in tourist areas and use reputable transportation. "
            f"Register with your embassy upon arrival. "
            f"Keep emergency contacts readily available."
        )
    
    elif alert_type == "weather warning":
        weather_event = random.choice(["hurricane season", "monsoon rains", "extreme heat", "winter storms"])
        return (
            f"Weather Warning for {destination}: "
            f"Active {weather_event} affecting the region. "
            f"Monitor weather forecasts closely and be prepared for travel disruptions. "
            f"Pack appropriate clothing and consider flexible booking options. "
            f"Check with airlines and hotels for any schedule changes."
        )
    
    else:  # transportation disruption
        return (
            f"Transportation Notice for {destination}: "
            f"Temporary disruptions reported in local transportation networks. "
            f"Expect delays in public transit and increased traffic. "
            f"Allow extra time for airport transfers and local travel. "
            f"Consider alternative transportation options and download local transport apps."
        )

ALL_TOOLS: Dict[str, Any] = {
    "search_flights": search_flights,
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