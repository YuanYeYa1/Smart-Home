"""Fix missing Python dependencies on server"""
import paramiko

LOG = r"C:\Users\yuany\Documents\Person\smart-home\fix_log.txt"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("8.137.21.211", 22, "root", "YuanYe0129", timeout=10, look_for_keys=False, allow_agent=False)

with open(LOG, "w") as f:
    # First stop the failing service
    f.write("Stopping service...\n")
    ssh.exec_command("systemctl stop smart-home-backend", timeout=10)
    
    # Install packages one by one with verbose output
    f.write("Installing paho-mqtt...\n")
    stdin, stdout, stderr = ssh.exec_command("pip3 install paho-mqtt 2>&1 | tail -5", timeout=60)
    f.write(stdout.read().decode() + "\n")
    
    f.write("Installing fastapi...\n")
    stdin, stdout, stderr = ssh.exec_command("pip3 install fastapi 2>&1 | tail -5", timeout=60)
    f.write(stdout.read().decode() + "\n")
    
    f.write("Installing uvicorn...\n")
    stdin, stdout, stderr = ssh.exec_command("pip3 install uvicorn 2>&1 | tail -5", timeout=60)
    f.write(stdout.read().decode() + "\n")
    
    f.write("Installing sqlalchemy...\n")
    stdin, stdout, stderr = ssh.exec_command("pip3 install sqlalchemy 2>&1 | tail -5", timeout=60)
    f.write(stdout.read().decode() + "\n")
    
    f.write("Installing websockets...\n")
    stdin, stdout, stderr = ssh.exec_command("pip3 install websockets 2>&1 | tail -5", timeout=60)
    f.write(stdout.read().decode() + "\n")
    
    # Verify installations
    f.write("\nVerifying...\n")
    stdin, stdout, stderr = ssh.exec_command("pip3 list 2>/dev/null | grep -iE 'paho|fast|uvicorn|sqlalchemy|websocket'", timeout=10)
    f.write(stdout.read().decode() + "\n")
    
    # Restart service
    f.write("Restarting service...\n")
    ssh.exec_command("systemctl restart smart-home-backend", timeout=10)
    
    import time
    time.sleep(3)
    
    # Check status
    f.write("\nService status:\n")
    stdin, stdout, stderr = ssh.exec_command("systemctl status smart-home-backend --no-pager -l | head -15", timeout=10)
    f.write(stdout.read().decode() + "\n")
    
    # Test
    f.write("\nCurl test:\n")
    stdin, stdout, stderr = ssh.exec_command("curl -s -w 'HTTP:%{http_code}' http://localhost:8000/", timeout=10)
    f.write(stdout.read().decode() + "\n")

ssh.close()
print("Done! Check fix_log.txt")
