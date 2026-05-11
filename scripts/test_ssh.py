"""Test SSH connection"""
import paramiko, traceback, os

try:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print("Connecting to 8.137.21.211...")
    ssh.connect("8.137.21.211", 22, "root", "YuanYe0129", timeout=15, look_for_keys=False, allow_agent=False)
    print("Connected!")
    
    # Run a simple command
    stdin, stdout, stderr = ssh.exec_command("echo HELLO_WORLD && hostname && date", timeout=10)
    out = stdout.read().decode()
    err = stderr.read().decode()
    ec = stdout.channel.recv_exit_status()
    print(f"Exit code: {ec}")
    print(f"Stdout: {out}")
    if err: print(f"Stderr: {err}")
    
    ssh.close()
    print("Done!")
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()

input("Press Enter...")
