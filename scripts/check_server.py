"""Check server - no prompts"""
import urllib.request, sys

url = "http://8.137.21.211:8000/"
print(f"Testing {url}...")
sys.stdout.flush()
try:
    r = urllib.request.urlopen(url, timeout=10)
    data = r.read()
    print(f"Status: {r.status}")
    print(f"Length: {len(data)} bytes")
    print(f"Content preview: {data[:200]}")
except Exception as e:
    print(f"ERROR: {e}")
