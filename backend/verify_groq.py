#!/usr/bin/env python3
"""Verify Groq API model availability and test chat completion."""
import os
import sys
from groq import Groq

def verify_groq_models():
    """List available Groq models without exposing the API key."""
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        print("ERROR: GROQ_API_KEY environment variable not set")
        return False, []
    
    # Mask the API key for logging
    key_preview = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "(too short)"
    print(f"API Key detected: {key_preview}")
    
    try:
        client = Groq(api_key=api_key)
        
        # List available models
        print("\nFetching available models from Groq API...")
        models_response = client.models.list()
        
        available_models = []
        for model in models_response.data:
            model_id = model.id
            available_models.append(model_id)
            print(f"  - {model_id}")
        
        return True, available_models
        
    except Exception as e:
        print(f"ERROR: Failed to fetch models: {type(e).__name__}: {e}")
        return False, []

def test_chat_completion(model_name: str):
    """Test a minimal chat completion with the specified model."""
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        print("ERROR: GROQ_API_KEY environment variable not set")
        return False, None
    
    try:
        client = Groq(api_key=api_key)
        
        print(f"\nTesting chat completion with model: {model_name}")
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "Reply with only: 'Connection successful'"}],
            temperature=0.1,
            max_tokens=20
        )
        
        content = response.choices[0].message.content.strip()
        print(f"Response: {content}")
        
        return True, content
        
    except Exception as e:
        print(f"ERROR: Chat completion failed: {type(e).__name__}: {e}")
        return False, str(e)

def test_strategy_parsing(model_name: str):
    """Test natural language strategy parsing."""
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        print("ERROR: GROQ_API_KEY environment variable not set")
        return False, None
    
    try:
        client = Groq(api_key=api_key)
        
        print(f"\nTesting strategy parsing with model: {model_name}")
        
        prompt = """Convert this stock screening strategy into structured conditions:

"Find stocks with price above 50-day moving average and RSI below 70"

Available fields: price, sma_20, sma_50, sma_200, rsi_14, macd, volume, market_cap, pe_ratio
Available operators: >, <, >=, <=, =

Return JSON with format:
{
  "name": "strategy name",
  "description": "brief description",
  "conditions": [
    {"field": "field_name", "operator": ">", "value": number}
  ]
}"""

        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=500
        )
        
        content = response.choices[0].message.content.strip()
        print(f"Raw response:\n{content[:500]}...")
        
        # Try to parse JSON
        import json
        if content.startswith('```'):
            content = content.split('```')[1]
            if content.startswith('json'):
                content = content[4:]
            content = content.strip()
        
        result = json.loads(content)
        print(f"\nParsed strategy: {result.get('name', 'N/A')}")
        print(f"Conditions: {len(result.get('conditions', []))}")
        
        return True, result
        
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse JSON response: {e}")
        return False, None
    except Exception as e:
        print(f"ERROR: Strategy parsing failed: {type(e).__name__}: {e}")
        return False, None

if __name__ == "__main__":
    # Load .env file if it exists
    from pathlib import Path
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        print(f"Loading environment from: {env_file}")
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    
    print("=" * 60)
    print("GROQ API VERIFICATION")
    print("=" * 60)
    
    # Verify models
    success, models = verify_groq_models()
    
    if not success:
        print("\nFailed to verify Groq models")
        sys.exit(1)
    
    # Check if configured model is available
    from config import settings
    configured_model = settings.groq_model
    
    print(f"\nConfigured model in settings: {configured_model}")
    
    if configured_model in models:
        print(f"✓ Configured model is available")
    else:
        print(f"✗ Configured model NOT in available models list")
        print(f"  Available models: {models}")
    
    # Test chat completion
    print("\n" + "=" * 60)
    print("TESTING CHAT COMPLETION")
    print("=" * 60)
    
    success, result = test_chat_completion(configured_model)
    
    if not success:
        print(f"\nChat completion test FAILED")
        sys.exit(1)
    
    # Test strategy parsing
    print("\n" + "=" * 60)
    print("TESTING STRATEGY PARSING")
    print("=" * 60)
    
    success, result = test_strategy_parsing(configured_model)
    
    if success:
        print("\n✓ All tests passed!")
        sys.exit(0)
    else:
        print("\n✗ Strategy parsing test failed")
        sys.exit(1)
