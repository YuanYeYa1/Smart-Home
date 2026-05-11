import traceback, os, sys
LOG = r"C:\Users\yuany\Documents\Person\smart-home\test_result.txt"
try:
    with open(LOG, "w") as f:
        f.write("Python version: " + sys.version + "\n")
        f.write("CWD: " + os.getcwd() + "\n")
        
        import paramiko
        f.write("paramiko imported: " + paramiko.__version__ + "\n")
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        f.write("Connecting to 8.137.21.211...\n")
        ssh.connect("8.137.21.211", 22, "root", "YuanYe0129", timeout=15, look_for_keys=False, allow_agent=False)
        f.write("Connected!\n")
        
        stdin, stdout, stderr = ssh.exec_command("echo HELLO", timeout=10)
        ec = stdout.channel.recv_exit_status()
        out = stdout.read().decode().strip()
        f.write(f"CMD result: {out}, exit_code: {ec}\n")
        
        ssh.close()
        f.write("All OK!\n")
except Exception as e:
    with open(LOG, "a") as f:
        f.write(f"ERROR: {e}\n")
        f.write(traceback.format_exc())
