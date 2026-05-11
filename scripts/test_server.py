"""Simple server test"""
import urllib.request
import json

try:
    req = urllib.request.Request("http://8.137.21.211:8000/")
    with urllib.request.urlopen(req, timeout=10) as resp:
        print(f"Status: {resp.status}")
        data = resp.read().decode()
        print(f"Response ({len(data)} bytes): {data[:200]}")
except Exception as e:
    print(f"Error: {e}")
