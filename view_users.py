#!/usr/bin/env python3
"""
Script to view all user data stored in the travel chatbot database
"""

import sqlite3
import json
from datetime import datetime

def view_all_users():
    """Display all user data from the database"""
    conn = sqlite3.connect('backend/travel_chatbot.db')
    cursor = conn.cursor()
    
    print("🔐 REGISTERED USERS")
    print("=" * 50)
    
    # Get all registered users (not demo users)
    cursor.execute("""
        SELECT id, email, first_name, last_name, nationality, 
               created_at, last_login, is_active
        FROM users 
        WHERE is_demo_user = 0 AND email NOT LIKE '%anon_%'
        ORDER BY created_at DESC
    """)
    
    users = cursor.fetchall()
    
    if not users:
        print("📝 No registered users yet. Register at: http://localhost:5173")
        print("\n🤖 ANONYMOUS USERS")
        print("=" * 30)
        
        # Show anonymous users
        cursor.execute("""
            SELECT id, email, first_name, created_at
            FROM users 
            WHERE email LIKE '%anon_%'
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        anon_users = cursor.fetchall()
        for user in anon_users:
            print(f"ID: {user[0][:8]}... | Email: {user[1]} | Created: {user[3]}")
    else:
        for user in users:
            print(f"\n👤 USER: {user[2]} {user[3]}")
            print(f"   📧 Email: {user[1]}")
            print(f"   🌍 Nationality: {user[4] or 'Not specified'}")
            print(f"   📅 Registered: {user[5]}")
            print(f"   🔑 Last Login: {user[6] or 'Never'}")
            print(f"   ✅ Active: {user[7]}")
            
            # Get user interactions
            cursor.execute("""
                SELECT COUNT(*), interaction_type
                FROM user_interactions 
                WHERE user_id = ?
                GROUP BY interaction_type
            """, (user[0],))
            
            interactions = cursor.fetchall()
            if interactions:
                print(f"   💬 Interactions:")
                for count, int_type in interactions:
                    print(f"      - {int_type}: {count}")
            
            # Get learning data
            cursor.execute("""
                SELECT COUNT(*)
                FROM user_learning_data 
                WHERE user_id = ?
            """, (user[0],))
            
            learning_count = cursor.fetchone()[0]
            print(f"   🧠 AI Learned Preferences: {learning_count}")
            
            # Get conversations
            cursor.execute("""
                SELECT COUNT(*)
                FROM conversations 
                WHERE user_id = ?
            """, (user[0],))
            
            conv_count = cursor.fetchone()[0]
            print(f"   💭 Conversations: {conv_count}")
    
    print(f"\n📊 SYSTEM STATISTICS")
    print("=" * 30)
    
    # Total stats
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_demo_user = 0 AND email NOT LIKE '%anon_%'")
    real_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE email LIKE '%anon_%'")
    anon_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM user_interactions")
    total_interactions = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM conversations")
    total_conversations = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM user_learning_data")
    total_learning = cursor.fetchone()[0]
    
    print(f"👥 Registered Users: {real_users}")
    print(f"🤖 Anonymous Users: {anon_users}")
    print(f"💬 Total Interactions: {total_interactions}")
    print(f"💭 Total Conversations: {total_conversations}")
    print(f"🧠 AI Learning Records: {total_learning}")
    
    conn.close()

def view_user_detail(email):
    """View detailed info for a specific user"""
    conn = sqlite3.connect('backend/travel_chatbot.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    
    if not user:
        print(f"❌ User with email {email} not found")
        return
    
    print(f"\n🔍 DETAILED USER INFO: {email}")
    print("=" * 50)
    
    # User details
    columns = ['id', 'first_name', 'last_name', 'email', 'phone', 'date_of_birth', 
              'nationality', 'passport_number', 'frequent_flyer_number', 'loyalty_tier', 
              'created_at', 'password_hash', 'is_demo_user', 'last_login', 'is_active']
    
    for i, col in enumerate(columns):
        if col != 'password_hash':  # Don't show password hash
            print(f"{col}: {user[i] if user[i] is not None else 'Not set'}")
    
    # User interactions
    print(f"\n💬 RECENT INTERACTIONS:")
    cursor.execute("""
        SELECT interaction_type, interaction_data, timestamp
        FROM user_interactions 
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT 10
    """, (user[0],))
    
    interactions = cursor.fetchall()
    for interaction in interactions:
        print(f"  {interaction[2]}: {interaction[0]} - {interaction[1][:100]}...")
    
    # Learning data
    print(f"\n🧠 AI LEARNED PREFERENCES:")
    cursor.execute("""
        SELECT data_type, data_key, data_value, confidence_score, updated_at
        FROM user_learning_data 
        WHERE user_id = ?
        ORDER BY confidence_score DESC
    """, (user[0],))
    
    learning = cursor.fetchall()
    for learn in learning:
        print(f"  {learn[1]}: {learn[2]} (confidence: {learn[3]:.2f}) - {learn[4]}")
    
    conn.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        view_user_detail(sys.argv[1])
    else:
        view_all_users()
        print(f"\n💡 Usage: python view_users.py <email> for detailed user info")
        print(f"🌐 Web Interface: http://localhost:5173")
        print(f"📊 Analytics API: http://localhost:8000/analytics/dashboard") 