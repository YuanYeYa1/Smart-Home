"""Install pip packages on server"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("8.137.21.211", 22, "root", "YuanYe0129", timeout=10, look_for_keys=False, allow_agent=False)

# Install all needed packages
stdin, stdout, stderr = ssh.exec_command(
    "pip3 install --break-system-packages paho-mqtt fastapi uvicorn sqlalchemy websockets 2>&1",
    timeout=120
)
out = stdout.read().decode()
with open(r"C:\Users\yuany\Documents\Person\smart-home\pip_out.txt", "w") as f:
    f.write(out)
print(out[-500:])

ssh.close()
