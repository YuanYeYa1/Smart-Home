#!/usr/bin/env python3
"""Quick deploy to cloud server using paramiko with password"""
import paramiko, os, time, traceback

def main():
    print("=" * 60)
    print("ESP32 Smart Home - Deploy to Cloud Server")
    print("=" * 60)
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print("\n[1/8] Connecting to 8.137.21.211...")
        ssh.connect("8.137.21.211", 22, "root", "YuanYe0129", timeout=15, look_for_keys=False, allow_agent=False)
        print("      Connected!")
        
        # Install SSH key for future passwordless access
        print("\n[2/8] Installing SSH key...")
        pubkey_path = os.path.expanduser(r"~\.ssh\id_rsa.pub")
        with open(pubkey_path) as f:
            pubkey = f.read().strip()
        stdin, stdout, stderr = ssh.exec_command(
            f'mkdir -p ~/.ssh && echo "{pubkey}" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo OK'
        )
        stdout.channel.recv_exit_status()
        print("      SSH key installed!")
        
        # Create directories
        print("\n[3/8] Creating directories...")
        sftp = ssh.open_sftp()
        for d in ["/root/smart-home", "/root/smart-home/backend", "/root/smart-home/backend/static"]:
            try:
                sftp.stat(d)
            except:
                sftp.mkdir(d)
        
        # Upload files
        print("\n[4/8] Uploading files...")
        backend = r"C:\Users\yuany\Documents\Person\smart-home\backend"
        files = [
            ("main.py", "/root/smart-home/backend/main.py"),
            ("requirements.txt", "/root/smart-home/backend/requirements.txt"),
            ("smart-home-backend.service", "/root/smart-home/backend/smart-home-backend.service"),
            (r"static\index.html", "/root/smart-home/backend/static/index.html"),
        ]
        for local_name, remote_path in files:
            local_path = os.path.join(backend, local_name)
            if os.path.exists(local_path):
                sftp.put(local_path, remote_path)
                print(f"      OK: {local_name}")
        sftp.close()
        
        # Install dependencies
        print("\n[5/8] Installing Python packages...")
        stdin, stdout, stderr = ssh.exec_command(
            "pip3 install -r /root/smart-home/backend/requirements.txt", timeout=120
        )
        stdout.channel.recv_exit_status()
        print("      Packages installed!")
        
        # Setup systemd
        print("\n[6/8] Setting up systemd...")
        cmds = [
            "cp /root/smart-home/backend/smart-home-backend.service /etc/systemd/system/",
            "systemctl daemon-reload",
            "systemctl enable smart-home-backend",
            "systemctl restart smart-home-backend",
        ]
        for cmd in cmds:
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
            stdout.channel.recv_exit_status()
        print("      Service configured!")
        
        time.sleep(3)
        
        # Check status
        print("\n[7/8] Checking service...")
        stdin, stdout, stderr = ssh.exec_command(
            "systemctl status smart-home-backend --no-pager -l | head -15", timeout=10
        )
        out = stdout.read().decode()
        for line in out.split("\n"):
            line = line.strip()
            if "Active:" in line or "Loaded:" in line:
                print(f"      {line}")
        
        # Firewall
        ssh.exec_command("ufw allow 8000/tcp 2>/dev/null; ufw reload 2>/dev/null", timeout=10)
        
        # Test
        print("\n[8/8] Testing...")
        stdin, stdout, stderr = ssh.exec_command(
            "curl -s -w 'HTTP_CODE:%{http_code}' http://localhost:8000/", timeout=10
        )
        out = stdout.read().decode()
        print(f"      Result: {out[:100]}")
        
        ssh.close()
        
        print("\n" + "=" * 60)
        print("DONE! Visit: http://8.137.21.211:8000")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        traceback.print_exc()

main()
