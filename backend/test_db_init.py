#!/usr/bin/env python3
"""Test database initialization to identify the failure."""
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

print("=" * 80)
print("DATABASE INITIALIZATION TEST")
print("=" * 80)

# Test 1: Check settings
print("\n1. SETTINGS CHECK")
from config import settings
print(f"   has_database: {settings.has_database}")
print(f"   database_url type: {type(settings.database_url)}")
print(f"   database_url length: {len(settings.database_url) if settings.database_url else 0}")

# Mask credentials for logging
if settings.database_url:
    url = settings.database_url
    if '@' in url:
        parts = url.split('@')
        masked = parts[0].rsplit(':', 1)[0] + ':***@' + parts[1]
        print(f"   database_url: {masked[:80]}...")

# Test 2: Initialize database
print("\n2. DATABASE INITIALIZATION")
from database import init_db, is_database_available, engine, SessionLocal

print(f"   Calling init_db()...")
result = init_db()
print(f"   init_db() returned: {result}")
print(f"   engine: {engine}")
print(f"   SessionLocal: {SessionLocal}")
print(f"   is_database_available(): {is_database_available()}")

# Test 3: Test raw connection
print("\n3. RAW CONNECTION TEST")
if settings.database_url:
    from sqlalchemy import create_engine, text
    
    try:
        test_engine = create_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args={"connect_timeout": 10}
        )
        
        with test_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print(f"   Raw connection: SUCCESS")
    except Exception as e:
        print(f"   Raw connection: FAILED")
        print(f"   Error: {type(e).__name__}: {e}")
else:
    print(f"   SKIPPED: No database URL")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
