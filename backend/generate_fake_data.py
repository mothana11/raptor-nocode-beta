import sqlite3
import uuid
from faker import Faker
import random
from datetime import datetime, timedelta
import json

fake = Faker()

def generate_fake_travel_data():
    """Generate comprehensive fake travel data for demo purposes"""
    
    conn = sqlite3.connect('travel_chatbot.db')
    cursor = conn.cursor()
    
    # Clear existing data (optional - for fresh demo)
    print("Clearing existing demo data...")
    cursor.execute("DELETE FROM travel_history")
    cursor.execute("DELETE FROM bookings")
    cursor.execute("DELETE FROM user_preferences")
    cursor.execute("DELETE FROM users")
    
    # Generate 10 realistic users
    print("Generating users...")
    users = []
    for i in range(10):
        user_id = str(uuid.uuid4())
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = f"{first_name.lower()}.{last_name.lower()}@{fake.domain_name()}"
        
        user_data = {
            'id': user_id,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'phone': fake.phone_number(),
            'date_of_birth': fake.date_of_birth(minimum_age=18, maximum_age=80).strftime('%Y-%m-%d'),
            'nationality': fake.country(),
            'passport_number': fake.bothify(text='??#######'),
            'frequent_flyer_number': fake.bothify(text='??########') if random.choice([True, False]) else None,
            'loyalty_tier': random.choice(['Bronze', 'Silver', 'Gold', 'Platinum', None])
        }
        
        cursor.execute('''
            INSERT INTO users (id, first_name, last_name, email, phone, date_of_birth, 
                             nationality, passport_number, frequent_flyer_number, loyalty_tier)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_data['id'], user_data['first_name'], user_data['last_name'], 
              user_data['email'], user_data['phone'], user_data['date_of_birth'],
              user_data['nationality'], user_data['passport_number'], 
              user_data['frequent_flyer_number'], user_data['loyalty_tier']))
        
        users.append(user_data)
    
    # Generate user preferences
    print("Generating user preferences...")
    preference_types = [
        ('seat_preference', ['aisle', 'window', 'middle']),
        ('meal_preference', ['vegetarian', 'vegan', 'kosher', 'halal', 'gluten-free', 'no_preference']),
        ('accommodation_type', ['hotel', 'resort', 'apartment', 'hostel', 'boutique']),
        ('price_range', ['budget', 'mid-range', 'luxury']),
        ('travel_style', ['business', 'leisure', 'adventure', 'cultural', 'relaxation']),
        ('notification_preference', ['email', 'sms', 'app', 'none']),
        ('preferred_airlines', ['Delta', 'United', 'American', 'Southwest', 'JetBlue']),
        ('preferred_hotel_chains', ['Marriott', 'Hilton', 'Hyatt', 'IHG', 'Accor'])
    ]
    
    for user in users:
        # Each user gets 3-6 random preferences
        num_preferences = random.randint(3, 6)
        selected_prefs = random.sample(preference_types, num_preferences)
        
        for pref_type, possible_values in selected_prefs:
            value = random.choice(possible_values)
            cursor.execute('''
                INSERT INTO user_preferences (user_id, preference_type, preference_value)
                VALUES (?, ?, ?)
            ''', (user['id'], pref_type, value))
    
    # Generate travel history
    print("Generating travel history...")
    destinations = [
        ('New York', 'USA'), ('London', 'UK'), ('Paris', 'France'), ('Tokyo', 'Japan'),
        ('Sydney', 'Australia'), ('Dubai', 'UAE'), ('Singapore', 'Singapore'),
        ('Barcelona', 'Spain'), ('Rome', 'Italy'), ('Bangkok', 'Thailand'),
        ('Cairo', 'Egypt'), ('Mumbai', 'India'), ('Toronto', 'Canada'),
        ('Amsterdam', 'Netherlands'), ('Berlin', 'Germany'), ('Istanbul', 'Turkey'),
        ('San Francisco', 'USA'), ('Los Angeles', 'USA'), ('Miami', 'USA'),
        ('Zurich', 'Switzerland')
    ]
    
    trip_purposes = ['business', 'leisure', 'family_visit', 'conference', 'vacation', 'honeymoon']
    
    for user in users:
        # Each user has 2-8 past trips
        num_trips = random.randint(2, 8)
        for _ in range(num_trips):
            destination, country = random.choice(destinations)
            trip_date = fake.date_between(start_date='-2y', end_date='-1m')
            duration = random.randint(2, 14)
            
            cursor.execute('''
                INSERT INTO travel_history (user_id, destination, country, trip_purpose, 
                                          trip_date, duration_days, rating, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user['id'], destination, country, random.choice(trip_purposes),
                  trip_date, duration, random.randint(3, 5), 
                  fake.sentence() if random.choice([True, False]) else None))
    
    # Generate current/future bookings
    print("Generating bookings...")
    booking_types = ['flight', 'hotel', 'car_rental', 'package', 'cruise']
    booking_statuses = ['confirmed', 'pending', 'cancelled', 'completed']
    currencies = ['USD', 'EUR', 'GBP', 'JPY', 'AUD']
    
    for user in users:
        # Each user has 1-4 bookings
        num_bookings = random.randint(1, 4)
        for _ in range(num_bookings):
            booking_id = str(uuid.uuid4())
            booking_type = random.choice(booking_types)
            status = random.choice(booking_statuses)
            
            # Generate realistic booking details based on type
            if booking_type == 'flight':
                details = {
                    'from': fake.city(),
                    'to': fake.city(),
                    'airline': random.choice(['Delta', 'United', 'American', 'Southwest']),
                    'flight_number': fake.bothify(text='??####'),
                    'class': random.choice(['economy', 'business', 'first']),
                    'passengers': random.randint(1, 4)
                }
            elif booking_type == 'hotel':
                details = {
                    'hotel_name': f"{fake.company()} Hotel",
                    'location': fake.city(),
                    'room_type': random.choice(['standard', 'deluxe', 'suite']),
                    'guests': random.randint(1, 4),
                    'amenities': random.sample(['wifi', 'pool', 'gym', 'spa', 'restaurant'], 2)
                }
            elif booking_type == 'car_rental':
                details = {
                    'company': random.choice(['Hertz', 'Avis', 'Enterprise', 'Budget']),
                    'car_type': random.choice(['economy', 'compact', 'midsize', 'luxury', 'suv']),
                    'pickup_location': fake.address(),
                    'return_location': fake.address()
                }
            else:
                details = {'description': fake.sentence()}
            
            booking_date = fake.date_between(start_date='-3m', end_date='today')
            travel_start = fake.date_between(start_date='today', end_date='+6m')
            travel_end = travel_start + timedelta(days=random.randint(1, 14))
            
            cursor.execute('''
                INSERT INTO bookings (id, user_id, booking_type, status, confirmation_number,
                                    booking_date, travel_date_start, travel_date_end,
                                    total_amount, currency, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (booking_id, user['id'], booking_type, status, fake.bothify(text='??######'),
                  booking_date, travel_start, travel_end,
                  round(random.uniform(100, 5000), 2), random.choice(currencies),
                  json.dumps(details)))
    
    conn.commit()
    conn.close()
    
    print(f"Generated fake data for {len(users)} users!")
    print("Data includes:")
    print("- User profiles with personal details and loyalty information")
    print("- Travel preferences (seats, meals, accommodation, etc.)")
    print("- Travel history with past trips and ratings")
    print("- Current and future bookings across different travel services")
    
    # Display sample user for verification
    print(f"\nSample user: {users[0]['first_name']} {users[0]['last_name']}")
    print(f"Email: {users[0]['email']}")
    print(f"Loyalty tier: {users[0]['loyalty_tier']}")

if __name__ == "__main__":
    generate_fake_travel_data() 