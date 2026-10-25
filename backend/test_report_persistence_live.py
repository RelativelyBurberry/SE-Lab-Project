#!/usr/bin/env python3
"""Test research report generation and persistence end-to-end with live API."""
import os
import sys
from pathlib import Path
from datetime import datetime
import json
import requests

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
print("RESEARCH REPORT PERSISTENCE TEST - LIVE API")
print("=" * 80)

API_BASE = "http://localhost:8000"

# Test 1: Check database state before generation
print("\n1. DATABASE STATE BEFORE GENERATION")
from sqlalchemy import create_engine, text
from config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
with engine.connect() as conn:
    count_result = conn.execute(text("SELECT COUNT(*) FROM research_reports"))
    count_before = count_result.scalar()
    print(f"   Reports before: {count_before}")

# Test 2: Check API health
print("\n2. API HEALTH CHECK")
try:
    response = requests.get(f"{API_BASE}/health", timeout=5)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        db_service = next((s for s in data['services'] if s['name'] == 'Database'), None)
        if db_service:
            print(f"   Database available: {db_service['available']}")
            print(f"   Database details: {db_service['details']}")
except requests.exceptions.ConnectionError:
    print("   ERROR: Backend server not running. Start with: python main.py")
    sys.exit(1)

# Test 3: Generate report
print("\n3. GENERATING REPORT")
ticker = "MSFT"
print(f"   Ticker: {ticker}")
print(f"   This may take 30-60 seconds...")

start_time = datetime.now()
try:
    response = requests.post(f"{API_BASE}/api/research/{ticker}", timeout=120)
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"   Status: {response.status_code}")
    print(f"   Duration: {duration:.1f} seconds")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n   Report generated successfully!")
        print(f"   Report ID: {data.get('id')}")
        print(f"   Saved: {data.get('saved')}")
        print(f"   Company: {data.get('report', {}).get('company_name')}")
        print(f"   Ticker: {data.get('report', {}).get('ticker')}")
        
        if not data.get('saved'):
            print(f"\n   ERROR: Report was NOT saved to database!")
        elif not data.get('id'):
            print(f"\n   ERROR: Report saved but no ID returned!")
        else:
            print(f"\n   SUCCESS: Report saved with ID {data.get('id')}")
    else:
        print(f"\n   ERROR: Generation failed")
        print(f"   Response: {response.text[:500]}")
        
except requests.exceptions.Timeout:
    print("   ERROR: Request timed out")
    sys.exit(1)
except Exception as e:
    print(f"   ERROR: {type(e).__name__}: {e}")
    sys.exit(1)

# Test 4: Check database state after generation
print("\n4. DATABASE STATE AFTER GENERATION")
with engine.connect() as conn:
    count_result = conn.execute(text("SELECT COUNT(*) FROM research_reports"))
    count_after = count_result.scalar()
    print(f"   Reports after: {count_after}")
    print(f"   Change: {count_after - count_before}")
    
    if count_after > count_before:
        # Show the new report
        print(f"\n   New report in database:")
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
            
            # Verify JSON data
            json_result = conn.execute(text("""
                SELECT report_data
                FROM research_reports
                WHERE id = :id
            """), {"id": row[0]})
            json_row = json_result.fetchone()
            if json_row:
                report_data = json_row[0]
                print(f"   - JSON keys: {list(report_data.keys())[:10]}...")
                print(f"   - Has executive_summary: {'executive_summary' in report_data}")
                print(f"   - Has generated_at: {'generated_at' in report_data}")
                print(f"   - generated_at type: {type(report_data.get('generated_at'))}")
    else:
        print("   ERROR: No new report found in database!")

# Test 5: Fetch report history via API
print("\n5. FETCHING REPORT HISTORY VIA API")
history_response = requests.get(f"{API_BASE}/api/research/history", timeout=10)
print(f"   Status: {history_response.status_code}")

if history_response.status_code == 200:
    history_data = history_response.json()
    print(f"   Reports in history: {len(history_data)}")
    
    if len(history_data) > 0:
        print(f"\n   Sample report from history:")
        sample = history_data[0]
        print(f"   - ID: {sample.get('id')}")
        print(f"   - Ticker: {sample.get('report', {}).get('ticker')}")
        print(f"   - Company: {sample.get('report', {}).get('company_name')}")
        print(f"   - Saved: {sample.get('saved')}")
    else:
        print("   ERROR: No reports returned from history endpoint!")
else:
    print(f"   ERROR: Failed to fetch history")
    print(f"   Response: {history_response.text[:500]}")

# Test 6: Fetch individual report
if count_after > 0:
    print("\n6. FETCHING INDIVIDUAL REPORT VIA API")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT id FROM research_reports ORDER BY generated_at DESC LIMIT 1"))
        report_id = result.scalar()
    
    if report_id:
        detail_response = requests.get(f"{API_BASE}/api/research/{report_id}", timeout=10)
        print(f"   Status: {detail_response.status_code}")
        
        if detail_response.status_code == 200:
            detail_data = detail_response.json()
            print(f"   Report fetched successfully!")
            print(f"   - ID: {detail_data.get('id')}")
            print(f"   - Ticker: {detail_data.get('report', {}).get('ticker')}")
            print(f"   - Saved: {detail_data.get('saved')}")
        else:
            print(f"   ERROR: Failed to fetch report")
            print(f"   Response: {detail_response.text[:500]}")

print("\n" + "=" * 80)
if count_after > count_before:
    print("TEST RESULT: SUCCESS - Report persisted and retrievable")
else:
    print("TEST RESULT: FAILED - Report not persisted")
print("=" * 80)
