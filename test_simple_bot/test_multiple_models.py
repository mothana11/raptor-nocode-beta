#!/usr/bin/env python3
"""
Test multiple OpenAI models to see which ones work with current quota
"""
import os
from openai import OpenAI

# Set API key directly
os.environ["OPENAI_API_KEY"] = "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"

def test_model(model_name: str, max_tokens: int = 10):
    """Test a specific OpenAI model"""
    print(f"\n🔍 Testing {model_name}...")
    
    client = OpenAI()
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "Say 'OK'"}],
            max_tokens=max_tokens
        )
        
        print(f"✅ {model_name} - WORKING!")
        print(f"📝 Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        error_str = str(e)
        print(f"❌ {model_name} - FAILED: {error_str}")
        
        if "429" in error_str or "quota" in error_str.lower():
            print(f"   🚨 Quota exceeded for {model_name}")
        elif "401" in error_str:
            print(f"   🔑 Invalid API key for {model_name}")
        elif "model" in error_str.lower():
            print(f"   🤖 Model not available: {model_name}")
        
        return False

def test_all_models():
    """Test multiple OpenAI models"""
    print("🧪 Testing Multiple OpenAI Models")
    print("=" * 50)
    
    # List of models to test (from cheapest to most expensive)
    models_to_test = [
        ("gpt-4o-mini", 10),      # Cheapest GPT-4 model
        ("gpt-3.5-turbo", 10),    # Cheapest overall
        ("gpt-4o", 10),           # Full GPT-4o
        ("gpt-4-turbo", 10),      # GPT-4 Turbo
        ("gpt-4", 10),            # Standard GPT-4
    ]
    
    working_models = []
    failed_models = []
    
    for model_name, max_tokens in models_to_test:
        if test_model(model_name, max_tokens):
            working_models.append(model_name)
        else:
            failed_models.append(model_name)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY:")
    print(f"✅ Working models: {working_models}")
    print(f"❌ Failed models: {failed_models}")
    
    if working_models:
        print(f"\n🎉 You can use: {', '.join(working_models)}")
        print("💡 Update your chatbot to use one of these models!")
    else:
        print("\n🚨 All models failed - quota issue affects all models")
        print("💡 You need to add credits to your OpenAI account")

if __name__ == "__main__":
    test_all_models() 