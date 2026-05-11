"""ESP32 Smart Home - Deploy to Cloud Server"""
import subprocess, os, sys, time

LOG_FILE = r"C:\Users\yuany\Documents\Person\smart-home\deploy_details.txt"
BACKEND = r"C:\Users\yuany\Documents\Person\smart-home\backend"

def log(msg):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)

def run(cmd, timeout=30):
    log(f"\nCMD: {cmd}")
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        log(f"RC: {r.returncode}")
        if r.stdout.strip(): log(f"OUT: {r.stdout.strip()[:500]}")
        if r.stderr.strip(): log(f"ERR: {r.stderr.strip()[:500]}")
        return r
    except Exception as e:
        log(f"EXCEPTION: {e}")
        return None

def main():
    # Clear log
    open(LOG_FILE, "w").close()
    log("="*60)
    log("ESP32 SMART HOME - DEPLOY TO CLOUD")
    log("="*60)
    
    # 1. Create remote dirs
    log("\n[1] Creating remote directories...")
    run(f'ssh -o StrictHostKeyChecking=no root@8.137.21.211 "mkdir -p /root/smart-home/backend/static"', 10)
    
    # 2. Copy files
    log("\n[2] Uploading files...")
    files = [
        ("main.py", ""),
        ("requirements.txt", ""),
        ("smart-home-backend.service", ""),
        (r"static\index.html", "static/"),
    ]
    for fname, subdir in files:
        src = os.path.join(BACKEND, fname)
        dst = f"root@8.137.21.211:/root/smart-home/backend/{subdir}{os.path.basename(fname)}"
        run(f'scp -o StrictHostKeyChecking=no "{src}" {dst}', 15)
    
    # 3. Install Python deps
    log("\n[3] Installing Python dependencies...")
    run(f'ssh root@8.137.21.211 "pip3 install -r /root/smart-home/backend/requirements.txt"', 120)
    
    # 4. Setup systemd
    log("\n[4] Setting up systemd service...")
    run(f'ssh root@8.137.21.211 "cp /root/smart-home/backend/smart-home-backend.service /etc/systemd/system/ && systemctl daemon-reload && systemctl enable smart-home-backend"', 15)
    
    # 5. Start service
    log("\n[5] Starting service...")
    run(f'ssh root@8.137.21.211 "systemctl restart smart-home-backend"', 15)
    time.sleep(3)
    
    # 6. Check status
    log("\n[6] Checking service status...")
    run(f'ssh root@8.137.21.211 "systemctl status smart-home-backend --no-pager -l | head -30"', 10)
    
    # 7. Firewall
    log("\n[7] Configuring firewall...")
    run(f'ssh root@8.137.21.211 "ufw allow 8000/tcp; ufw reload; ufw status"', 10)
    
    # 8. Test local
    log("\n[8] Testing local access...")
    run(f'ssh root@8.137.21.211 "curl -s -w \\"%{{http_code}}\\" http://localhost:8000/ || echo FAILED"', 10)
    
    log("\n" + "="*60)
    log("Deployment complete!")
    log(f"Visit: http://8.137.21.211:8000")
    log("="*60)
    
    # Also try from local
    log("\nTrying local HTTP test...")
    try:
        req = urllib.request.Request("http://8.137.21.211:8000/")
        with urllib.request.urlopen(req, timeout=10) as resp:
            log(f"Local test HTTP {resp.status}: got {len(resp.read())} bytes")
    except Exception as e:
        log(f"Local test failed: {e}")

import urllib.request
main()
