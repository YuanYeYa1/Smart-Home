#!/usr/bin/env python3
"""Redirect all output to a log file"""
import subprocess
import sys
import os

log_path = r"C:\Users\yuany\Documents\Person\smart-home\deploy_result.txt"

with open(log_path, "w", encoding="utf-8") as log:
    log.write("Starting deployment...\n")
    
    # Check if SSH key auth works
    try:
        r = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", 
             "root@8.137.21.211", "echo 'SSH OK'"],
            capture_output=True, text=True, timeout=10
        )
        log.write(f"SSH test: stdout={r.stdout}, stderr={r.stderr}, rc={r.returncode}\n")
    except Exception as e:
        log.write(f"SSH test failed: {e}\n")
    
    # Create remote dir
    try:
        r = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no",
             "root@8.137.21.211", "mkdir -p /root/smart-home/backend/static"],
            capture_output=True, text=True, timeout=10
        )
        log.write(f"mkdir: rc={r.returncode}, err={r.stderr}\n")
    except Exception as e:
        log.write(f"mkdir failed: {e}\n")
    
    # Copy files
    backend_dir = r"C:\Users\yuany\Documents\Person\smart-home\backend"
    files_to_copy = [
        ("main.py", ""),
        ("requirements.txt", ""),
        ("smart-home-backend.service", ""),
        (r"static\index.html", "static/"),
    ]
    
    for fname, dest_sub in files_to_copy:
        src = os.path.join(backend_dir, fname)
        dest = f"root@8.137.21.211:/root/smart-home/backend/{dest_sub}{os.path.basename(fname)}"
        try:
            r = subprocess.run(
                ["scp", "-o", "StrictHostKeyChecking=no", src, dest],
                capture_output=True, text=True, timeout=30
            )
            log.write(f"scp {fname}: rc={r.returncode}\n")
        except Exception as e:
            log.write(f"scp {fname} failed: {e}\n")
    
    # Install deps
    try:
        r = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "root@8.137.21.211",
             "pip3 install -r /root/smart-home/backend/requirements.txt 2>&1 | tail -5"],
            capture_output=True, text=True, timeout=120
        )
        log.write(f"pip install: rc={r.returncode}\n{r.stdout}\n")
    except Exception as e:
        log.write(f"pip install failed: {e}\n")
    
    # Setup systemd
    cmds = [
        "cp /root/smart-home/backend/smart-home-backend.service /etc/systemd/system/",
        "systemctl daemon-reload",
        "systemctl enable smart-home-backend",
        "systemctl restart smart-home-backend",
    ]
    for cmd in cmds:
        try:
            r = subprocess.run(
                ["ssh", "-o", "BatchMode=yes", "root@8.137.21.211", cmd],
                capture_output=True, text=True, timeout=15
            )
            log.write(f"systemd {cmd[:40]}: rc={r.returncode}\n")
        except Exception as e:
            log.write(f"systemd cmd failed: {e}\n")
    
    # Wait and check
    import time
    time.sleep(3)
    
    try:
        r = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "root@8.137.21.211",
             "systemctl status smart-home-backend --no-pager -l 2>&1 | head -20"],
            capture_output=True, text=True, timeout=15
        )
        log.write(f"Status:\n{r.stdout}\n")
    except Exception as e:
        log.write(f"status failed: {e}\n")
    
    # Firewall
    try:
        r = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "root@8.137.21.211",
             "ufw allow 8000/tcp 2>&1; ufw reload 2>&1; echo 'done'"],
            capture_output=True, text=True, timeout=15
        )
        log.write(f"firewall: {r.stdout}\n")
    except Exception as e:
        log.write(f"firewall failed: {e}\n")
    
    # Curl test
    try:
        r = subprocess.run(
            ["ssh", "-o", "BatchMode=yes", "root@8.137.21.211",
             "curl -s -w '%{http_code}' http://localhost:8000/ 2>&1"],
            capture_output=True, text=True, timeout=10
        )
        log.write(f"curl localhost: {r.stdout}\n")
    except Exception as e:
        log.write(f"curl failed: {e}\n")
    
    log.write("\nDone!\n")

print(f"Log written to {log_path}")
