#!/usr/bin/env python3
"""Deploy with subprocess and pexpect-like stdin handling"""
import subprocess, os, sys, time

def run_cmd(cmd, timeout=30):
    print(f"\n>>> {cmd[:80]}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    if result.stdout: print(result.stdout[:500])
    if result.returncode != 0 and result.stderr:
        err = result.stderr[:300]
        if "password" not in err.lower(): print(f"[ERR] {err}")
    return result.returncode

def main():
    logfile = r"C:\Users\yuany\Documents\Person\smart-home\fw_deploy_log.txt"
    os.chdir(r"C:\Users\yuany\Documents\Person\smart-home")
    
    with open(logfile, "w") as log:
        log.write("Starting deployment...\n")
        
        # Copy public key using PowerShell with password
        log.write("\n=== Installing SSH key ===\n")
        pubkey_path = os.path.expanduser(r"~\.ssh\id_rsa.pub")
        with open(pubkey_path) as f:
            pubkey = f.read().strip()
        
        # Use PowerShell to run ssh with password
        ps_script = f'''
$secpasswd = ConvertTo-SecureString "YuanYe0129" -AsPlainText -Force
$cred = New-Object System.Management.Automation.PSCredential("root", $secpasswd)
$pubkey = "{pubkey}"
$cmd = "mkdir -p ~/.ssh && echo '$pubkey' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
ssh root@8.137.21.211 $cmd
'''
        # Actually, just try with subprocess directly, ssh will prompt for password
        # Use cmdkey /add approach
        
        log.write("1. Trying to install SSH key...\n")
        
        # Method: write a script that pipes password to ssh
        # We'll use plink-like approach with ssh command and here-string
        
    # Step 1: Try if server is already up
    print("Checking if server is already running...")
    try:
        import urllib.request
        r = urllib.request.urlopen("http://8.137.21.211:8000/", timeout=5)
        print(f"Server responded! Status: {r.status}")
        r.read()
        print("Server is already running! No need to deploy.")
        return
    except Exception as e:
        print(f"Server not reachable: {e}")
    
    # Let's try the simplest possible approach with pexpect
    print("\nAttempting password-based SSH login...")
    
    # Create a temporary batch file that will handle SSH
    bat_content = """@echo off
set PASSWORD=YuanYe0129
echo %PASSWORD% | ssh -o StrictHostKeyChecking=no root@8.137.21.211 "echo SSH_WORKS"
"""
    
    # Actually, Windows SSH doesn't support password via stdin
    # Let's use the simplest brute force approach
    
    print("\n=== Creating helper script ===")
    
    # Use sshpass via WSL or... 
    # Simpler: Try paramiko step by step to find the issue
    
    import paramiko
    
    print("Testing paramiko connection...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect("8.137.21.211", 22, "root", "YuanYe0129", timeout=10, 
                    look_for_keys=False, allow_agent=False, 
                    disabled_algorithms=dict(pubkeys=["rsa-sha2-256", "rsa-sha2-512"]))
        print("Connected!")
        
        # Test command
        stdin, stdout, stderr = ssh.exec_command("echo HELLO && hostname", timeout=10)
        out = stdout.read().decode()
        print(f"Output: {out.strip()}")
        
        # Install key
        with open(pubkey_path) as f:
            pubkey = f.read().strip()
        stdin, stdout, stderr = ssh.exec_command(
            f'mkdir -p ~/.ssh && echo "{pubkey}" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo KEY_DONE',
            timeout=10)
        out = stdout.read().decode()
        print(f"Key install: {out.strip()}")
        
        # Create dirs
        sftp = ssh.open_sftp()
        for d in ["/root/smart-home", "/root/smart-home/backend", "/root/smart-home/backend/static"]:
            try: sftp.stat(d)
            except: sftp.mkdir(d)
        
        # Upload
        backend = r"C:\Users\yuany\Documents\Person\smart-home\backend"
        for fname in ["main.py", "requirements.txt", "smart-home-backend.service", "static\\index.html"]:
            local = os.path.join(backend, fname)
            if "static" in fname:
                remote = f"/root/smart-home/backend/static/{os.path.basename(fname)}"
            else:
                remote = f"/root/smart-home/backend/{os.path.basename(fname)}"
            if os.path.exists(local):
                sftp.put(local, remote)
                print(f"  OK: {fname}")
        sftp.close()
        
        # Install deps
        print("Installing packages...")
        stdin, stdout, stderr = ssh.exec_command("pip3 install -r /root/smart-home/backend/requirements.txt", timeout=120)
        stdout.channel.recv_exit_status()
        print("Packages done!")
        
        # Systemd
        for cmd in [
            "cp /root/smart-home/backend/smart-home-backend.service /etc/systemd/system/",
            "systemctl daemon-reload",
            "systemctl enable smart-home-backend",
            "systemctl restart smart-home-backend"
        ]:
            ssh.exec_command(cmd, timeout=15)
        
        time.sleep(3)
        
        # Status
        stdin, stdout, stderr = ssh.exec_command(
            "systemctl status smart-home-backend --no-pager -l | head -15", timeout=10)
        out = stdout.read().decode()
        print(f"Status:\n{out}")
        
        # Firewall
        ssh.exec_command("ufw allow 8000/tcp 2>/dev/null; ufw reload 2>/dev/null", timeout=10)
        
        # Test
        stdin, stdout, stderr = ssh.exec_command(
            "curl -s -w '%{http_code}' http://localhost:8000/", timeout=10)
        out = stdout.read().decode()
        print(f"Curl: {out[:100]}")
        
        ssh.close()
        print("\nDONE! http://8.137.21.211:8000")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

main()
input("\nPress Enter...")
