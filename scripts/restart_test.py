"""Restart service and test"""
import paramiko, time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("8.137.21.211", 22, "root", "YuanYe0129", timeout=10, look_for_keys=False, allow_agent=False)

with open(r"C:\Users\yuany\Documents\Person\smart-home\restart_log.txt", "w") as f:
    f.write("Restarting service...\n")
    ssh.exec_command("systemctl stop smart-home-backend", timeout=10)
    time.sleep(1)
    ssh.exec_command("systemctl restart smart-home-backend", timeout=10)
    time.sleep(3)
    
    f.write("Status:\n")
    stdin, stdout, stderr = ssh.exec_command("systemctl status smart-home-backend --no-pager -l | head -20", timeout=10)
    f.write(stdout.read().decode())
    
    f.write("\nCurl test:\n")
    stdin, stdout, stderr = ssh.exec_command("curl -s -w 'HTTP:%{http_code}' http://localhost:8000/", timeout=10)
    f.write(stdout.read().decode()[:200])

ssh.close()
print("Done!")
