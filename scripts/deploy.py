#!/usr/bin/env python3
"""Automated deployment script using subprocess"""
import subprocess
import sys
import os
import time

SERVER = "root@8.137.21.211"
REMOTE_DIR = "/root/smart-home/backend"
LOCAL_DIR = r"C:\Users\yuany\Documents\Person\smart-home\backend"

def run(cmd, timeout=60):
    """Run a command and return output"""
    print(f"\n>>> {cmd}")
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout
    )
    if result.stdout:
        for line in result.stdout.strip().split("\n"):
            print(f"  {line}")
    if result.stderr:
        for line in result.stderr.strip().split("\n"):
            if "Warning" not in line and "Permanently" not in line:
                print(f"  [ERR] {line}")
    print(f"  [RETURN CODE: {result.returncode}]")
    return result

def main():
    print("=" * 60)
    print("🚀 ESP32 Smart Home - Deploy to Cloud Server")
    print(f"   Server: {SERVER}")
    print("=" * 60)

    # Step 1: Copy SSH public key to server (requires password)
    pubkey_path = os.path.expanduser(r"~\.ssh\id_rsa.pub")
    with open(pubkey_path, "r") as f:
        pubkey = f.read().strip()
    
    print("\n🔑 Setting up SSH key authentication (will prompt for password)...")
    cmd = f'ssh {SERVER} "mkdir -p ~/.ssh && echo \\"{pubkey}\\" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"'
    result = run(cmd, timeout=15)
    
    if result.returncode != 0:
        print("⚠️  SSH key setup may have failed. Trying with password input...")
    
    # Step 2: Create remote directories
    print("\n📁 Creating remote directories...")
    run(f'ssh {SERVER} "mkdir -p {REMOTE_DIR}/static"', timeout=10)
    
    # Step 3: Copy files
    print("\n📤 Copying files to server...")
    files = [
        ("main.py", ""),
        ("requirements.txt", ""),
        ("smart-home-backend.service", ""),
        ("deploy.sh", ""),
        ("static\\index.html", "static/"),
    ]
    
    for local_file, remote_subdir in files:
        local_path = os.path.join(LOCAL_DIR, local_file)
        remote_path = f"{REMOTE_DIR}/{remote_subdir}{os.path.basename(local_file)}"
        if os.path.exists(local_path):
            run(f'scp {local_path} {SERVER}:{remote_path}', timeout=30)
        else:
            print(f"  ⚠️  File not found: {local_path}")
    
    # Step 4: Install dependencies
    print("\n📦 Installing Python dependencies...")
    run(f'ssh {SERVER} "pip3 install -r {REMOTE_DIR}/requirements.txt"', timeout=120)
    
    # Step 5: Setup systemd service
    print("\n⚙️  Setting up systemd service...")
    cmds = [
        f'cp {REMOTE_DIR}/smart-home-backend.service /etc/systemd/system/',
        "systemctl daemon-reload",
        "systemctl enable smart-home-backend",
    ]
    for c in cmds:
        run(f'ssh {SERVER} "{c}"', timeout=15)
    
    # Step 6: Start the service
    print("\n🚀 Starting backend service...")
    run(f'ssh {SERVER} "systemctl restart smart-home-backend"', timeout=15)
    time.sleep(3)
    
    # Step 7: Check status
    print("\n🔍 Checking service status...")
    run(f'ssh {SERVER} "systemctl status smart-home-backend --no-pager -l"', timeout=15)
    
    # Step 8: Configure firewall
    print("\n🛡️  Configuring firewall...")
    run(f'ssh {SERVER} "ufw allow 8000/tcp 2>/dev/null; ufw reload 2>/dev/null; echo done"', timeout=15)
    
    # Step 9: Verify access
    print("\n🔗 Verifying local access...")
    run(f'ssh {SERVER} "curl -s -w \'HTTP %{{http_code}}\' http://localhost:8000/ 2>/dev/null || echo not ready"', timeout=10)
    
    print("\n" + "=" * 60)
    print("✅ Deployment complete!")
    print(f"🌐 Visit: http://8.137.21.211:8000")
    print("=" * 60)

if __name__ == "__main__":
    main()
