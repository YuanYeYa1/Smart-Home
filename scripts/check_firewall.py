"""Check cloud firewall and ufw"""
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("8.137.21.211", 22, "root", "YuanYe0129", timeout=10, look_for_keys=False, allow_agent=False)

with open(r"C:\Users\yuany\Documents\Person\smart-home\firewall_check.txt", "w") as f:
    # Check if port 8000 is listening
    f.write("=== Listening ports ===\n")
    stdin, stdout, stderr = ssh.exec_command("ss -tlnp | grep 8000", timeout=10)
    f.write(stdout.read().decode() + "\n")
    
    # Check UFW status
    f.write("\n=== UFW Status ===\n")
    stdin, stdout, stderr = ssh.exec_command("ufw status verbose 2>&1", timeout=10)
    f.write(stdout.read().decode() + "\n")
    
    # Check iptables
    f.write("\n=== iptables ===\n")
    stdin, stdout, stderr = ssh.exec_command("iptables -L -n --line-numbers 2>/dev/null | head -30", timeout=10)
    f.write(stdout.read().decode() + "\n")
    
    # Test local curl
    f.write("\n=== Local curl test ===\n")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://localhost:8000/ | head -5", timeout=10)
    f.write(stdout.read().decode() + "\n")
    
    # Test public IP curl
    f.write("\n=== Public IP curl test ===\n")
    stdin, stdout, stderr = ssh.exec_command("curl -s http://8.137.21.211:8000/ 2>&1 | head -5", timeout=10)
    f.write(stdout.read().decode()[:200] + "\n")
    err = stderr.read().decode()
    if err: f.write(f"STDERR: {err[:200]}\n")
    
    # Check network interface
    f.write("\n=== Network interfaces ===\n")
    stdin, stdout, stderr = ssh.exec_command("ip addr show | grep inet", timeout=10)
    f.write(stdout.read().decode() + "\n")

ssh.close()
print("Done!")
