"""Test external access to the cloud server"""
import urllib.request, socket

LOG = r"C:\Users\yuany\Documents\Person\smart-home\external_test.txt"

with open(LOG, "w") as f:
    f.write("=== External Access Test ===\n\n")
    
    # Test 1: HTTP access to port 8000
    f.write("[1] HTTP http://8.137.21.211:8000/\n")
    try:
        r = urllib.request.urlopen("http://8.137.21.211:8000/", timeout=10)
        data = r.read()
        f.write(f"  OK! Status={r.status}, Size={len(data)} bytes\n")
        f.write(f"  HTML starts: {data[:100]}\n")
    except Exception as e:
        f.write(f"  FAILED: {e}\n")
    
    # Test 2: API endpoint
    f.write("\n[2] API /api/status\n")
    try:
        r = urllib.request.urlopen("http://8.137.21.211:8000/api/status", timeout=10)
        data = r.read()
        f.write(f"  OK! Status={r.status}, Data={data[:200]}\n")
    except Exception as e:
        f.write(f"  FAILED: {e}\n")
    
    # Test 3: API docs
    f.write("\n[3] API /docs\n")
    try:
        r = urllib.request.urlopen("http://8.137.21.211:8000/docs", timeout=10)
        data = r.read()
        f.write(f"  OK! Status={r.status}, Size={len(data)} bytes\n")
    except Exception as e:
        f.write(f"  FAILED: {e}\n")
    
    f.write("\n=== Test Complete ===\n")

print("Done! Check external_test.txt")
