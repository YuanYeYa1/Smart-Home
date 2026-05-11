"""Check backend MQTT logs"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("8.137.21.211", 22, "root", "YuanYe0129", timeout=10, look_for_keys=False, allow_agent=False)

with open(r"C:\Users\yuany\Documents\Person\smart-home\mqtt_log.txt", "w") as f:
    # Check journalctl for backend logs
    stdin, out, _ = ssh.exec_command("journalctl -u smart-home-backend --since '5 min ago' --no-pager 2>&1 | tail -40", timeout=10)
    logs = out.read().decode()
    f.write(logs)
    print(logs)

ssh.close()
