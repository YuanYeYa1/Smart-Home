#!/usr/bin/env python3
"""Final deploy - clean version, writes to file, no prompts"""
import paramiko, os, time, traceback, urllib.request

LOG = r"C:\Users\yuany\Documents\Person\smart-home\final_log.txt"
SERVER = "8.137.21.211"
BACKEND = r"C:\Users\yuany\Documents\Person\smart-home\backend"

def w(msg):
    with open(LOG, "a") as f: f.write(str(msg) + "\n")

def main():
    # First check if server is already running
    try:
        r = urllib.request.urlopen(f"http://{SERVER}:8000/", timeout=5)
        w("Server already running! Status: " + str(r.status))
        return
    except Exception:
        w("Server not reachable, deploying...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        w("Connecting...")
        ssh.connect(SERVER, 22, "root", "YuanYe0129", timeout=15, look_for_keys=False, allow_agent=False)
        w("Connected!")
        
        # Install SSH key
        with open(os.path.expanduser(r"~\.ssh\id_rsa.pub")) as f:
            pubkey = f.read().strip()
        stdin, stdout, stderr = ssh.exec_command(f'mkdir -p ~/.ssh && echo "{pubkey}" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo OK')
        out = stdout.read().decode().strip()
        w("Key: " + out)
        
        # Upload files via SFTP
        sftp = ssh.open_sftp()
        for d in ["/root/smart-home", "/root/smart-home/backend", "/root/smart-home/backend/static"]:
            try: sftp.stat(d)
            except: sftp.mkdir(d)
        
        for fname in ["main.py", "requirements.txt", "smart-home-backend.service", "static\\index.html"]:
            local = os.path.join(BACKEND, fname)
            rname = fname.replace("static\\", "static/")
            remote = f"/root/smart-home/backend/{rname}"
            if os.path.exists(local):
                sftp.put(local, remote)
                w(f"Uploaded: {fname}")
        sftp.close()
        
        # Install deps
        w("Installing packages...")
        ssh.exec_command("pip3 install -r /root/smart-home/backend/requirements.txt", timeout=120)
        w("Packages done!")
        
        # Setup systemd
        for cmd in [
            "cp /root/smart-home/backend/smart-home-backend.service /etc/systemd/system/",
            "systemctl daemon-reload",
            "systemctl enable smart-home-backend",
            "systemctl restart smart-home-backend"
        ]:
            ssh.exec_command(cmd, timeout=15)
        w("Service configured!")
        
        time.sleep(3)
        
        # Check status
        stdin, stdout, stderr = ssh.exec_command("systemctl status smart-home-backend --no-pager -l | head -20", timeout=10)
        out = stdout.read().decode()
        w("Status:\n" + out)
        
        # Firewall
        ssh.exec_command("ufw allow 8000/tcp 2>/dev/null; ufw reload 2>/dev/null", timeout=10)
        w("Firewall done!")
        
        # Test
        stdin, stdout, stderr = ssh.exec_command("curl -s -w 'HTTP:%{http_code}' http://localhost:8000/", timeout=10)
        out = stdout.read().decode()
        w("Test: " + out[:100])
        
        ssh.close()
        w(f"\nDONE! Visit: http://{SERVER}:8000")
        
    except Exception as e:
        w(f"ERROR: {e}\n{traceback.format_exc()}")

main()
