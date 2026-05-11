"""Check why the service fails"""
import paramiko

LOG = r"C:\Users\yuany\Documents\Person\smart-home\error_log.txt"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("8.137.21.211", 22, "root", "YuanYe0129", timeout=10, look_for_keys=False, allow_agent=False)

with open(LOG, "w") as f:
    # Journalctl logs
    stdin, stdout, stderr = ssh.exec_command("journalctl -u smart-home-backend --no-pager -n 50", timeout=10)
    f.write("=== JOURNALCTL ===\n")
    f.write(stdout.read().decode())
    
    # Python check
    stdin, stdout, stderr = ssh.exec_command("which python3 && python3 --version", timeout=10)
    f.write("\n=== PYTHON ===\n")
    f.write(stdout.read().decode())
    f.write(stderr.read().decode())
    
    # Check pip packages
    stdin, stdout, stderr = ssh.exec_command("pip3 list 2>/dev/null", timeout=10)
    f.write("\n=== PIP LIST ===\n")
    f.write(stdout.read().decode())
    
    # Try running python directly
    stdin, stdout, stderr = ssh.exec_command("cd /root/smart-home/backend && python3 -c \"print('hello')\" 2>&1", timeout=10)
    f.write("\n=== PYTHON TEST ===\n")
    f.write(stdout.read().decode())
    f.write(stderr.read().decode())

ssh.close()
print("Done! Check error_log.txt")
