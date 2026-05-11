"""Upload fixed main.py and restart service"""
import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("8.137.21.211", 22, "root", "YuanYe0129", timeout=10, look_for_keys=False, allow_agent=False)

# Read local file
with open(r"C:\Users\yuany\Documents\Person\smart-home\backend\main.py", "rb") as f:
    content = f.read()

# Upload via SFTP
sftp = ssh.open_sftp()
# Backup first
ssh.exec_command("cp /root/smart-home/backend/main.py /root/smart-home/backend/main.py.bak", timeout=10)
# Upload
with sftp.open("/root/smart-home/backend/main.py", "wb") as f:
    f.write(content)
sftp.close()

# Restart
ssh.exec_command("systemctl restart smart-home-backend", timeout=10)
time.sleep(3)

# Check status
stdin, out, _ = ssh.exec_command("systemctl status smart-home-backend --no-pager -l | head -10", timeout=10)
print(out.read().decode())

# Test
stdin, out, _ = ssh.exec_command("curl -s http://127.0.0.1:8000/api/status", timeout=10)
print("API status:", out.read().decode()[:200])

ssh.close()
print("Done!")
