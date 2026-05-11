"""Check network connection and test paramiko"""
LOG = r"C:\Users\yuany\Documents\Person\smart-home\conn_log.txt"
import os, sys, traceback
os.chdir(r"C:\Users\yuany\Documents\Person\smart-home")

def log(msg):
    with open(LOG, "a") as f:
        f.write(str(msg) + "\n")

log("=== Connection Test ===")
log(f"Python: {sys.version}")
log(f"CWD: {os.getcwd()}")

# 1. Check network
import socket
log("\n[1] DNS lookup...")
try:
    ip = socket.gethostbyname("8.137.21.211")
    log(f"  IP: {ip}")
except Exception as e:
    log(f"  FAIL: {e}")

log("\n[2] Port 8000...")
try:
    s = socket.socket()
    s.settimeout(5)
    s.connect(("8.137.21.211", 8000))
    s.send(b"GET / HTTP/1.0\r\nHost: 8.137.21.211\r\n\r\n")
    data = s.recv(1024)
    log(f"  Response: {data[:200]}")
    s.close()
except Exception as e:
    log(f"  FAIL: {e}")

log("\n[3] Port 22...")
try:
    s = socket.socket()
    s.settimeout(5)
    s.connect(("8.137.21.211", 22))
    data = s.recv(1024)
    log(f"  SSH banner: {data[:100]}")
    s.close()
except Exception as e:
    log(f"  FAIL: {e}")

log("\n[4] Paramiko...")
try:
    import paramiko
    log(f"  Version: {paramiko.__version__}")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    log("  Connecting with password...")
    ssh.connect("8.137.21.211", 22, "root", "YuanYe0129", timeout=10, look_for_keys=False, allow_agent=False)
    log("  Connected!")
    
    stdin, stdout, stderr = ssh.exec_command("echo OK", timeout=5)
    ec = stdout.channel.recv_exit_status()
    out = stdout.read().decode()
    log(f"  CMD: {out.strip()}, exit: {ec}")
    ssh.close()
    log("  Paramiko OK!")
except Exception as e:
    log(f"  FAIL: {e}")
    log(traceback.format_exc())

log("\nDone!")
