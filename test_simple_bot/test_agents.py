#!/usr/bin/env python3
"""
Simple test bot using openai-agents to verify API key works
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openai_agents():
    """Test OpenAI API using the agents SDK"""
    print("🔍 Testing OpenAI API with agents SDK...")
    
    # Check if API key is loaded
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ No OPENAI_API_KEY found in environment")
        return False
    
    print(f"🔑 Using API Key: {api_key[:10]}...{api_key[-5:]}")
    
    try:
        from agents import Agent, Runner
        
        # Create a simple agent
        agent = Agent(
            name="Assistant", 
            instructions="You are a helpful assistant",
            model="gpt-4o-mini"
        )
        
        print("✅ Agent created successfully")
        
        # Test with a simple request
        print("📤 Sending test request...")
        result = Runner.run_sync(agent, "Write a haiku about recursion in programming.")
        
        print("✅ OpenAI API call successful!")
        print(f"📝 Response: {result.final_output}")
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 Try: pip install openai-agents")
        return False
    except Exception as e:
        error_str = str(e)
        print(f"❌ API Error: {error_str}")
        
        if "429" in error_str or "quota" in error_str.lower():
            print("\n🚨 QUOTA EXCEEDED:")
            print("1. Your OpenAI API key has reached its usage limit")
            print("2. Visit: https://platform.openai.com/billing")
            print("3. Add payment method and purchase credits")
            print("4. Or create a new API key with available quota")
        elif "401" in error_str:
            print("\n🔑 INVALID API KEY:")
            print("1. Check your API key is correct")
            print("2. Visit: https://platform.openai.com/api-keys")
            
        return False

if __name__ == "__main__":
    test_openai_agents() 