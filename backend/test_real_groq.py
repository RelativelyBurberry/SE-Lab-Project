#!/usr/bin/env python3
"""Test real Groq API call for strategy parsing."""
import os
import sys
from pathlib import Path

# Load .env file
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    print(f"Loading environment from: {env_file}")
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value

from groq import Groq
import json

def test_groq_strategy_parsing():
    """Test real strategy parsing with Groq API."""
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("ERROR: GROQ_API_KEY not set")
        return False
    
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    print(f"Using model: {model}")
    
    try:
        client = Groq(api_key=api_key)
        
        natural_language = "Find stocks with price above 50-day moving average and RSI below 70"
        
        prompt = f"""Convert this stock screening strategy into structured conditions:

"{natural_language}"

Available fields: price, sma_20, sma_50, sma_200, rsi_14, macd, volume, market_cap, pe_ratio
Available operators: >, <, >=, <=, =

Return JSON with format:
{{
  "name": "strategy name",
  "description": "brief description",
  "conditions": [
    {{"field": "field_name", "operator": ">", "value": number}}
  ]
}}"""

        print(f"\nSending request to Groq API...")
        print(f"Prompt: {natural_language}")
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=500
        )
        
        if not response.choices:
            print("ERROR: Empty choices in response")
            return False
        
        content = response.choices[0].message.content
        
        if not content or not content.strip():
            print("ERROR: Empty content in response")
            return False
        
        # Safely print response (handle Unicode)
        try:
            print(f"\nRaw response:\n{content[:500]}...")
        except UnicodeEncodeError:
            print(f"\nRaw response: [contains special characters, length={len(content)}]")
            print(f"First 200 ASCII-safe: {content[:200].encode('ascii', 'replace').decode('ascii')}...")
        
        # Clean up markdown if present
        content = content.strip()
        if content.startswith('```'):
            parts = content.split('```')
            if len(parts) >= 2:
                content = parts[1]
                if content.startswith('json'):
                    content = content[4:]
                content = content.strip()
        
        # Parse JSON
        result = json.loads(content)
        
        print(f"\nParsed strategy:")
        print(f"  Name: {result.get('name', 'N/A').encode('ascii', 'replace').decode('ascii')}")
        print(f"  Description: {result.get('description', 'N/A').encode('ascii', 'replace').decode('ascii')}")
        print(f"  Conditions ({len(result.get('conditions', []))}):")
        
        for cond in result.get("conditions", []):
            print(f"    - {cond.get('field')} {cond.get('operator')} {cond.get('value')}")
        
        # Validate conditions
        allowed_fields = {'price', 'sma_20', 'sma_50', 'sma_200', 'rsi_14', 'macd', 'volume', 'market_cap', 'pe_ratio'}
        allowed_operators = {'>', '<', '>=', '<=', '='}
        
        valid_conditions = []
        for cond in result.get("conditions", []):
            field = cond.get("field")
            operator = cond.get("operator")
            value = cond.get("value")
            
            if field in allowed_fields and operator in allowed_operators and isinstance(value, (int, float)):
                valid_conditions.append(cond)
            else:
                print(f"  WARNING: Invalid condition: {cond}")
        
        if valid_conditions:
            print(f"\nValid conditions: {len(valid_conditions)}")
            print("\nSUCCESS: Strategy parsing completed successfully!")
            return True
        else:
            print("\nERROR: No valid conditions found")
            return False
            
    except json.JSONDecodeError as e:
        print(f"ERROR: JSON parsing failed: {e}")
        return False
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("REAL GROQ API TEST - STRATEGY PARSING")
    print("=" * 60)
    
    success = test_groq_strategy_parsing()
    
    sys.exit(0 if success else 1)
