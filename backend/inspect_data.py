import sqlite3
import json

def inspect_database():
    """Inspect the travel chatbot database and display user data"""
    
    conn = sqlite3.connect('travel_chatbot.db')
    cursor = conn.cursor()
    
    print("=" * 60)
    print("TRAVEL CHATBOT DATABASE INSPECTION")
    print("=" * 60)
    
    # Get database stats
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM user_preferences")
    pref_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM travel_history")
    history_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM bookings")
    booking_count = cursor.fetchone()[0]
    
    print(f"📊 Database Statistics:")
    print(f"   • Users: {user_count}")
    print(f"   • User Preferences: {pref_count}")
    print(f"   • Travel History Records: {history_count}")
    print(f"   • Bookings: {booking_count}")
    print()
    
    # Show sample users
    print("👥 Sample Users:")
    cursor.execute("""
        SELECT first_name, last_name, email, nationality, loyalty_tier 
        FROM users LIMIT 3
    """)
    for i, (first, last, email, nationality, loyalty) in enumerate(cursor.fetchall(), 1):
        print(f"   {i}. {first} {last}")
        print(f"      Email: {email}")
        print(f"      Nationality: {nationality}")
        print(f"      Loyalty: {loyalty or 'None'}")
        print()
    
    # Show detailed view of one user
    cursor.execute("SELECT * FROM users LIMIT 1")
    user_row = cursor.fetchone()
    if user_row:
        user_id = user_row[0]
        first_name = user_row[1]
        last_name = user_row[2]
        
        print(f"🔍 Detailed View: {first_name} {last_name}")
        print("-" * 40)
        
        # Get their preferences
        cursor.execute("""
            SELECT preference_type, preference_value 
            FROM user_preferences WHERE user_id = ?
        """, (user_id,))
        prefs = cursor.fetchall()
        
        print("   Preferences:")
        for pref_type, pref_value in prefs:
            print(f"   • {pref_type.replace('_', ' ').title()}: {pref_value}")
        
        # Get their travel history
        cursor.execute("""
            SELECT destination, country, trip_date, trip_purpose, rating 
            FROM travel_history WHERE user_id = ? 
            ORDER BY trip_date DESC LIMIT 3
        """, (user_id,))
        history = cursor.fetchall()
        
        print("\n   Recent Travel History:")
        for dest, country, date, purpose, rating in history:
            print(f"   • {dest}, {country} ({date}) - {purpose}, rated {rating}/5")
        
        # Get their bookings
        cursor.execute("""
            SELECT booking_type, confirmation_number, status, travel_date_start, details 
            FROM bookings WHERE user_id = ? 
            ORDER BY travel_date_start LIMIT 2
        """, (user_id,))
        bookings = cursor.fetchall()
        
        print("\n   Active Bookings:")
        for booking_type, conf_num, status, travel_date, details in bookings:
            print(f"   • {booking_type.title()}: {conf_num} ({status}) - {travel_date}")
            if details:
                details_obj = json.loads(details)
                if booking_type == 'flight':
                    print(f"     {details_obj.get('from', '')} → {details_obj.get('to', '')} on {details_obj.get('airline', '')}")
                elif booking_type == 'hotel':
                    print(f"     {details_obj.get('hotel_name', '')} in {details_obj.get('location', '')}")
    
    print("\n" + "=" * 60)
    print("Database file location: backend/travel_chatbot.db")
    print("=" * 60)
    
    conn.close()

if __name__ == "__main__":
    inspect_database() 