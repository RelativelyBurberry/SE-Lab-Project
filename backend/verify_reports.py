#!/usr/bin/env python3
"""Verify report history still works after changes."""
import requests
import sys

API_BASE = "http://localhost:8000"

print("VERIFYING REPORT HISTORY AND DETAIL")
print("=" * 60)

# Test history endpoint
print("\n1. Report History")
try:
    r = requests.get(f"{API_BASE}/api/research/history", timeout=10)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"   Reports: {len(data)}")
        for d in data[:5]:
            report = d.get("report", {})
            print(f"   - ID={d.get('id')}, {report.get('ticker')} ({report.get('company_name')})")
    else:
        print(f"   Error: {r.text[:200]}")
except requests.exceptions.ConnectionError:
    print("   ERROR: Backend not running. Skipping live tests.")
    sys.exit(0)

# Test individual report
print("\n2. Individual Report")
if r.status_code == 200 and len(data) > 0:
    report_id = data[0].get("id")
    r2 = requests.get(f"{API_BASE}/api/research/{report_id}", timeout=10)
    print(f"   Status: {r2.status_code}")
    if r2.status_code == 200:
        detail = r2.json()
        report = detail.get("report", {})
        print(f"   Ticker: {report.get('ticker')}")
        print(f"   Company: {report.get('company_name')}")
        print(f"   Has executive_summary: {bool(report.get('executive_summary'))}")
        print(f"   Has technical_analysis: {bool(report.get('technical_analysis'))}")
        print(f"   Has fundamental_analysis: {bool(report.get('fundamental_analysis'))}")
        print(f"   Has news_analysis: {bool(report.get('news_analysis'))}")
        print(f"   Bullish factors: {len(report.get('bullish_factors', []))}")
        print(f"   Bearish factors: {len(report.get('bearish_factors', []))}")
        print(f"   Risk factors: {len(report.get('risk_factors', []))}")
    else:
        print(f"   Error: {r2.text[:200]}")

# Test health endpoint
print("\n3. Health Check")
r3 = requests.get(f"{API_BASE}/health", timeout=10)
print(f"   Status: {r3.status_code}")
if r3.status_code == 200:
    health = r3.json()
    for service in health.get("services", []):
        print(f"   - {service['name']}: {'OK' if service['available'] else 'UNAVAILABLE'}")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
