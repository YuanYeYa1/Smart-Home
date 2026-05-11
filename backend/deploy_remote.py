#!/usr/bin/env python3
"""
ESP32 智能家居 - 远程部署脚本
通过 SSH 将后端代码部署到云服务器
"""

import os
import sys
import paramiko
import time

# ========== 配置 ==========
SERVER_IP = "8.137.21.211"
SERVER_USER = "root"
SERVER_PASSWORD = "YuanYe0129"
REMOTE_DIR = "/root/smart-home/backend"
LOCAL_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))

# 需要上传的文件和目录
FILES_TO_UPLOAD = [
    "main.py",
    "requirements.txt",
    "deploy.sh",
    "smart-home-backend.service",
]
DIRS_TO_UPLOAD = [
    "static",
]

def run_ssh_command(ssh, command, timeout=30):
    """执行 SSH 命令并打印输出"""
    print(f"  $ {command}")
    stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
    exit_status = stdout.channel.recv_exit_status()
    output = stdout.read().decode("utf-8", errors="replace").strip()
    error = stderr.read().decode("utf-8", errors="replace").strip()
    if output:
        for line in output.split("\n"):
            print(f"    {line}")
    if error and exit_status != 0:
        for line in error.split("\n"):
            print(f"    [ERROR] {line}")
    return exit_status, output

def upload_file(sftp, local_path, remote_path):
    """上传单个文件"""
    print(f"  📤 {os.path.basename(local_path)} -> {remote_path}")
    sftp.put(local_path, remote_path)

def main():
    print("=" * 60)
    print("🚀 ESP32 智能家居 - 远程部署到云服务器")
    print(f"  服务器: {SERVER_IP}")
    print("=" * 60)
    
    # 连接 SSH
    print("\n🔌 连接服务器...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(
            SERVER_IP,
            username=SERVER_USER,
            password=SERVER_PASSWORD,
            look_for_keys=False,
            timeout=15
        )
        print("✅ SSH 连接成功!")
    except Exception as e:
        print(f"❌ SSH 连接失败: {e}")
        sys.exit(1)
    
    # 创建远程目录
    print("\n📁 创建远程目录...")
    run_ssh_command(ssh, f"mkdir -p {REMOTE_DIR}/static")
    
    # 上传文件
    print("\n📤 上传文件...")
    sftp = ssh.open_sftp()
    
    for filename in FILES_TO_UPLOAD:
        local_path = os.path.join(LOCAL_BACKEND_DIR, filename)
        remote_path = os.path.join(REMOTE_DIR, filename)
        if os.path.exists(local_path):
            upload_file(sftp, local_path, remote_path)
        else:
            print(f"  ⚠️  本地文件不存在: {local_path}")
    
    for dirname in DIRS_TO_UPLOAD:
        local_dir = os.path.join(LOCAL_BACKEND_DIR, dirname)
        remote_dir = os.path.join(REMOTE_DIR, dirname)
        if os.path.exists(local_dir):
            for f in os.listdir(local_dir):
                local_path = os.path.join(local_dir, f)
                remote_path = os.path.join(remote_dir, f)
                if os.path.isfile(local_path):
                    upload_file(sftp, local_path, remote_path)
    
    sftp.close()
    print("✅ 文件上传完成!")
    
    # 设置可执行权限
    print("\n🔧 设置文件权限...")
    run_ssh_command(ssh, f"chmod +x {REMOTE_DIR}/deploy.sh")
    
    # 安装依赖
    print("\n📦 安装 Python 依赖...")
    run_ssh_command(ssh, f"pip3 install -r {REMOTE_DIR}/requirements.txt")
    
    # 安装 systemd 服务
    print("\n⚙️  配置 systemd 服务（开机自启）...")
    run_ssh_command(ssh, f"cp {REMOTE_DIR}/smart-home-backend.service /etc/systemd/system/")
    run_ssh_command(ssh, "systemctl daemon-reload")
    run_ssh_command(ssh, "systemctl enable smart-home-backend")
    
    # 启动服务
    print("\n🚀 启动后端服务...")
    run_ssh_command(ssh, "systemctl restart smart-home-backend")
    time.sleep(2)
    
    # 检查服务状态
    print("\n🔍 检查服务状态...")
    exit_code, status = run_ssh_command(ssh, "systemctl status smart-home-backend --no-pager -l")
    
    # 配置防火墙
    print("\n🛡️  配置防火墙放行 8000 端口...")
    run_ssh_command(ssh, "ufw allow 8000/tcp 2>/dev/null || firewall-cmd --add-port=8000/tcp --permanent 2>/dev/null || echo '防火墙已配置'")
    
    # 检查服务是否在运行
    print("\n🔍 验证服务运行状态...")
    exit_code, check = run_ssh_command(ssh, "curl -s -o /dev/null -w '%{http_code}' http://localhost:8000/")
    
    ssh.close()
    
    print("\n" + "=" * 60)
    if "200" in check:
        print("✅ 部署成功！🎉")
        print(f"🌐 访问地址: http://{SERVER_IP}:8000")
        print(f"📖 API 文档: http://{SERVER_IP}:8000/docs")
        print(f"🔌 WebSocket: ws://{SERVER_IP}:8000/ws")
    else:
        print("⚠️  服务可能还在启动中，请稍后检查...")
        print(f"   systemctl status smart-home-backend")
    print("=" * 60)

if __name__ == "__main__":
    main()
