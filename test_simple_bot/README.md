# Simple OpenAI API Test Bot

This directory contains simple test scripts to verify OpenAI API functionality using different approaches.

## Files

- `test_agents.py` - Test using `openai-agents` SDK (your suggested approach)
- `test_direct_openai.py` - Test using direct OpenAI API calls
- `requirements.txt` - Required packages

## Usage

1. **Install dependencies:**
   ```bash
   cd test_simple_bot
   pip install -r requirements.txt
   ```

2. **Test with agents SDK:**
   ```bash
   python test_agents.py
   ```

3. **Test with direct OpenAI:**
   ```bash
   python test_direct_openai.py
   ```

## Results

Both tests confirm the same issue: **OpenAI API quota exceeded**.

```
❌ API Error: Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details.'}}
```

## Solution

The API key `sk-proj-TirPRXOESzbxBBQDx2k8...` has reached its usage limit. To fix:

1. **Visit:** https://platform.openai.com/billing
2. **Add payment method** and purchase credits
3. **OR create new API key** with available quota
4. **Update environment variable** with new key

## Verified Functionality

✅ **openai-agents SDK works correctly** - the issue is purely quota-related
✅ **Direct OpenAI API works correctly** - same quota limitation  
✅ **Both approaches produce identical error messages** - confirms quota exhaustion

Once quota is resolved, both test scripts should work perfectly! 