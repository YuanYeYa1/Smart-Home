#!/usr/bin/env python3
"""Deploy to cloud server - no input prompts"""
import paramiko, os, sys, time, traceback

LOG = r"C:\Users\yuany\Documents\Person\smart-home\deploy_v2_log.txt"
SERVER = "8.137.21.211"
PASSWORD = "YuanYe0129"

def log(msg):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")

def main():
    try:
        log("=" * 60)
        log("DEPLOY STARTING")
        log("=" * 60)
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        log("Connecting to " + SERVER)
        ssh.connect(SERVER, 22, "root", PASSWORD, timeout=15, look_for_keys=False, allow_agent=False)
        log("Connected!")
        
        # Install SSH key
        log("Installing SSH key...")
        pubkey_path = os.path.expanduser(r"~\.ssh\id_rsa.pub")
        with open(pubkey_path) as f:
            pubkey = f.read().strip()
        stdin, stdout, stderr = ssh.exec_command(f'mkdir -p ~/.ssh && echo "{pubkey}" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo KEY_OK')
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode().strip()
        log(f"Key install: rc={exit_code}, out={out}")
        
        # Create dirs via SFTP
        log("Creating dirs...")
        sftp = ssh.open_sftp()
        try: sftp.stat('/root/smart-home')
        except: sftp.mkdir('/root/smart-home')
        try: sftp.stat('/root/smart-home/backend')
        except: sftp.mkdir('/root/smart-home/backend')
        try: sftp.stat('/root/smart-home/backend/static')
        except: sftp.mkdir('/root/smart-home/backend/static')
        
        # Upload files
        log("Uploading files...")
        backend = r"C:\Users\yuany\Documents\Person\smart-home\backend"
        for fname, subdir in [("main.py",""), ("requirements.txt",""), ("smart-home-backend.service",""), (r"static\index.html","static/")]:
            local = os.path.join(backend, fname)
            remote = f"/root/smart-home/backend/{subdir}{os.path.basename(fname)}"
            if os.path.exists(local):
                sftp.put(local, remote)
                log(f"  OK: {fname}")
            else:
                log(f"  MISSING: {local}")
        sftp.close()
        
        # Install pip deps
        log("Installing pip packages...")
        stdin, stdout, stderr = ssh.exec_command("pip3 install -r /root/smart-home/backend/requirements.txt", timeout=120)
        exit_code = stdout.channel.recv_exit_status()
        log(f"Pip done: rc={exit_code}")
        
        # Setup systemd
        log("Setting up systemd...")
        cmds = [
            "cp /root/smart-home/backend/smart-home-backend.service /etc/systemd/system/",
            "systemctl daemon-reload",
            "systemctl enable smart-home-backend",
            "systemctl restart smart-home-backend"
        ]
        for cmd in cmds:
            stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
            ec = stdout.channel.recv_exit_status()
            log(f"  {cmd[:40]}: rc={ec}")
        
        time.sleep(3)
        
        # Check status
        log("Checking status...")
        stdin, stdout, stderr = ssh.exec_command("systemctl status smart-home-backend --no-pager -l | head -20", timeout=10)
        ec = stdout.channel.recv_exit_status()
        out = stdout.read().decode()
        for line in out.split('\n')[:15]:
            if line.strip(): log(f"  {line.strip()}")
        
        # Firewall
        log("Configuring firewall...")
        ssh.exec_command("ufw allow 8000/tcp 2>/dev/null; ufw reload 2>/dev/null", timeout=10)
        
        # Test
        log("Testing...")
        stdin, stdout, stderr = ssh.exec_command("curl -s -w 'HTTP_CODE:%{http_code}' http://localhost:8000/ 2>/dev/null || echo NO_RESPONSE", timeout=10)
        ec = stdout.channel.recv_exit_status()
        out = stdout.read().decode()
        log(f"Curl: {out[:100]}")
        
        ssh.close()
        log("DONE!")
        
    except Exception as e:
        log(f"ERROR: {e}")
        log(traceback.format_exc())

main()
