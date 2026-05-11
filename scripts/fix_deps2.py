"""Fix deps with --break-system-packages"""
import paramiko, time

LOG = r"C:\Users\yuany\Documents\Person\smart-home\fix2_log.txt"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("8.137.21.211", 22, "root", "YuanYe0129", timeout=10, look_for_keys=False, allow_agent=False)

with open(LOG, "w") as f:
    f.write("Installing packages with --break-system-packages...\n")
    
    # Install all at once
    stdin, stdout, stderr = ssh.exec_command(
        "pip3 install --break-system-packages paho-mqtt fastapi uvicorn sqlalchemy websockets 2>&1 | tail -20",
        timeout=120
    )
    out = stdout.read().decode()
    f.write(out + "\n")
    
    # Verify
    f.write("\nVerifying...\n")
    stdin, stdout, stderr = ssh.exec_command("pip3 list 2>/dev/null | grep -iE 'paho|fast|uvicorn|sqlalchemy|websocket'", timeout=10)
    f.write(stdout.read().decode() + "\n")
    
    # Restart
    ssh.exec_command("systemctl restart smart-home-backend", timeout=10)
    time.sleep(3)
    
    # Status
    f.write("\nStatus:\n")
    stdin, stdout, stderr = ssh.exec_command("systemctl status smart-home-backend --no-pager -l | head -15", timeout=10)
    f.write(stdout.read().decode() + "\n")
    
    # Test
    f.write("\nTest:\n")
    stdin, stdout, stderr = ssh.exec_command("curl -s -w 'HTTP:%{http_code}' http://localhost:8000/", timeout=10)
    f.write(stdout.read().decode() + "\n")

ssh.close()
print("Done!")
