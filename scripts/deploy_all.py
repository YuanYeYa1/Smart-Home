#!/usr/bin/env python3
"""
ESP32 Smart Home - 一键部署到云服务器
使用密码登录，安装SSH密钥，然后部署所有文件
"""
import paramiko
import os
import time

SERVER = "8.137.21.211"
PORT = 22
USER = "root"
PASSWORD = "YuanYe0129"

BACKEND_DIR = r"C:\Users\yuany\Documents\Person\smart-home\backend"
REMOTE_DIR = "/root/smart-home/backend"

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def ssh_exec(ssh, cmd, timeout=30, print_output=True):
    """Execute command via SSH and return output"""
    log(f"执行: {cmd[:80]}{'...' if len(cmd) > 80 else ''}")
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=timeout)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if print_output and out:
        for line in out.split('\n')[:20]:
            log(f"  {line}")
    if print_output and err and exit_code != 0:
        for line in err.split('\n')[:5]:
            log(f"  [ERR] {line}")
    return out, err, exit_code

def main():
    log("=" * 60)
    log("🚀 ESP32 Smart Home - 一键部署到云服务器")
    log(f"   服务器: {USER}@{SERVER}:{PORT}")
    log("=" * 60)

    # 第一步：SSH连接（使用密码）
    log("\n🔑 [1/9] 连接服务器...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(SERVER, PORT, USER, PASSWORD, timeout=15)
        log("✅ 连接成功！")
    except Exception as e:
        log(f"❌ 连接失败: {e}")
        return

    try:
        # 第二步：安装SSH公钥
        log("\n🔐 [2/9] 安装SSH公钥...")
        pubkey_path = os.path.expanduser(r"~\.ssh\id_rsa.pub")
        if os.path.exists(pubkey_path):
            with open(pubkey_path, 'r') as f:
                pubkey = f.read().strip()
            
            out, err, rc = ssh_exec(ssh, f'mkdir -p ~/.ssh && echo "{pubkey}" >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && echo SSH_KEY_INSTALLED')
            if "SSH_KEY_INSTALLED" in out:
                log("✅ SSH公钥安装成功！以后无需密码")
        else:
            log(f"⚠️  公钥文件未找到: {pubkey_path}")

        # 第三步：创建远程目录
        log("\n📁 [3/9] 创建远程目录...")
        ssh_exec(ssh, f"mkdir -p {REMOTE_DIR}/static")

        # 第四步：上传文件（使用SFTP）
        log("\n📤 [4/9] 上传文件...")
        sftp = ssh.open_sftp()
        files_to_upload = [
            ("main.py", ""),
            ("requirements.txt", ""),
            ("smart-home-backend.service", ""),
            (r"static\index.html", "static/"),
        ]
        for local_name, remote_subdir in files_to_upload:
            local_path = os.path.join(BACKEND_DIR, local_name)
            remote_path = f"{REMOTE_DIR}/{remote_subdir}{os.path.basename(local_name)}"
            if os.path.exists(local_path):
                sftp.put(local_path, remote_path)
                log(f"  ✅ {local_name} -> {remote_path}")
            else:
                log(f"  ⚠️  本地文件不存在: {local_path}")
        sftp.close()

        # 第五步：安装Python依赖
        log("\n📦 [5/9] 安装Python依赖...")
        ssh_exec(ssh, f"pip3 install -r {REMOTE_DIR}/requirements.txt", timeout=120)

        # 第六步：设置systemd服务
        log("\n⚙️  [6/9] 设置systemd服务...")
        ssh_exec(ssh, f"cp {REMOTE_DIR}/smart-home-backend.service /etc/systemd/system/ && systemctl daemon-reload && systemctl enable smart-home-backend")

        # 第七步：启动服务
        log("\n🚀 [7/9] 启动服务...")
        ssh_exec(ssh, "systemctl restart smart-home-backend")
        time.sleep(3)

        # 第八步：检查状态
        log("\n🔍 [8/9] 检查服务状态...")
        out, _, _ = ssh_exec(ssh, "systemctl status smart-home-backend --no-pager -l | head -25")
        
        if "Active: active (running)" in out:
            log("✅ 服务运行正常！")
        elif "Active:" in out:
            for line in out.split('\n'):
                if "Active:" in line:
                    log(f"  状态: {line.strip()}")
        else:
            log("⚠️  请检查服务状态")

        # 第九步：配置防火墙并测试
        log("\n🛡️  [9/9] 配置防火墙...")
        ssh_exec(ssh, "ufw allow 8000/tcp 2>/dev/null; ufw reload 2>/dev/null; echo firewall_done")
        
        # 本地测试
        log("\n🔗 本地测试...")
        out, _, _ = ssh_exec(ssh, "curl -s -w 'HTTP_%{http_code}' http://localhost:8000/ 2>/dev/null || echo '服务未响应'")
        if "HTTP_" in out:
            log(f"✅ 服务响应: {out}")

        log("\n" + "=" * 60)
        log("✅ 部署完成！")
        log(f"🌐 访问地址: http://{SERVER}:8000")
        log("=" * 60)

    except Exception as e:
        log(f"❌ 部署出错: {e}")
        import traceback
        log(traceback.format_exc())
    finally:
        ssh.close()

if __name__ == "__main__":
    main()
    input("\n按回车键退出...")
