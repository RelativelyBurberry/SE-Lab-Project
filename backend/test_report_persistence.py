#!/usr/bin/env python3
"""Test research report generation and persistence end-to-end."""
import os
import sys
from pathlib import Path
from datetime import datetime
import json

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
print("RESEARCH REPORT GENERATION AND PERSISTENCE TEST")
print("=" * 80)

# Test 1: Check database state before generation
print("\n1. DATABASE STATE BEFORE GENERATION")
from sqlalchemy import create_engine, text
from config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
with engine.connect() as conn:
    count_result = conn.execute(text("SELECT COUNT(*) FROM research_reports"))
    count_before = count_result.scalar()
    print(f"   Reports before: {count_before}")

# Test 2: Generate a report via the API endpoint
print("\n2. GENERATING REPORT VIA API")
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# First, check health
print("\n   Checking API health...")
health_response = client.get("/health")
print(f"   Health status: {health_response.status_code}")
health_data = health_response.json()
print(f"   Database available: {health_data['services'][2]['available']}")
print(f"   Database details: {health_data['services'][2]['details']}")

# Generate report for a known ticker
ticker = "AAPL"
print(f"\n   Generating report for {ticker}...")
print(f"   This may take 30-60 seconds...")

start_time = datetime.now()
response = client.post(f"/api/research/{ticker}")
end_time = datetime.now()
duration = (end_time - start_time).total_seconds()

print(f"\n   Response status: {response.status_code}")
print(f"   Duration: {duration:.1f} seconds")

if response.status_code == 200:
    data = response.json()
    print(f"\n   Report generated successfully!")
    print(f"   Report ID: {data.get('id')}")
    print(f"   Saved: {data.get('saved')}")
    print(f"   Company: {data.get('report', {}).get('company_name')}")
    print(f"   Ticker: {data.get('report', {}).get('ticker')}")
    
    if not data.get('saved'):
        print(f"\n   WARNING: Report was NOT saved to database!")
    elif not data.get('id'):
        print(f"\n   WARNING: Report saved but no ID returned!")
else:
    print(f"\n   ERROR: Generation failed")
    print(f"   Response: {response.text[:500]}")

# Test 3: Check database state after generation
print("\n3. DATABASE STATE AFTER GENERATION")
with engine.connect() as conn:
    count_result = conn.execute(text("SELECT COUNT(*) FROM research_reports"))
    count_after = count_result.scalar()
    print(f"   Reports after: {count_after}")
    print(f"   Change: {count_after - count_before}")
    
    if count_after > count_before:
        # Show the new report
        print(f"\n   New report details:")
        result = conn.execute(text("""
            SELECT id, ticker, company_name, generated_at
            FROM research_reports
            ORDER BY generated_at DESC
            LIMIT 1
        """))
        row = result.fetchone()
        if row:
            print(f"   - ID: {row[0]}")
            print(f"   - Ticker: {row[1]}")
            print(f"   - Company: {row[2]}")
            print(f"   - Generated at: {row[3]}")

# Test 4: Fetch report history via API
print("\n4. FETCHING REPORT HISTORY VIA API")
history_response = client.get("/api/research/history")
print(f"   History status: {history_response.status_code}")

if history_response.status_code == 200:
    history_data = history_response.json()
    print(f"   Reports in history: {len(history_data)}")
    
    if len(history_data) > 0:
        print(f"\n   Sample report from history:")
        sample = history_data[0]
        print(f"   - ID: {sample.get('id')}")
        print(f"   - Ticker: {sample.get('report', {}).get('ticker')}")
        print(f"   - Company: {sample.get('report', {}).get('company_name')}")
else:
    print(f"   ERROR: Failed to fetch history")
    print(f"   Response: {history_response.text[:500]}")

# Test 5: Fetch individual report
if count_after > 0:
    print("\n5. FETCHING INDIVIDUAL REPORT VIA API")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id FROM research_reports ORDER BY generated_at DESC LIMIT 1"))
        report_id = result.scalar()
    
    if report_id:
        detail_response = client.get(f"/api/research/{report_id}")
        print(f"   Detail status: {detail_response.status_code}")
        
        if detail_response.status_code == 200:
            detail_data = detail_response.json()
            print(f"   Report fetched successfully!")
            print(f"   - ID: {detail_data.get('id')}")
            print(f"   - Saved: {detail_data.get('saved')}")
        else:
            print(f"   ERROR: Failed to fetch report")
            print(f"   Response: {detail_response.text[:500]}")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
