#!/bin/bash
# ==========================================
# ESP32 智能家居 - 云服务器部署脚本
# 使用方法: bash deploy.sh
# ==========================================

set -e

echo "========================================"
echo "🚀 ESP32 智能家居 - 后端部署脚本"
echo "========================================"

# 项目目录
PROJECT_DIR="/root/smart-home/backend"

# 1. 创建项目目录
echo "📁 创建项目目录..."
mkdir -p $PROJECT_DIR/static

# 2. 安装 Python 依赖
echo "📦 安装 Python 依赖..."
cd $PROJECT_DIR
pip3 install -r requirements.txt

# 3. 检查 systemd 服务是否已存在
SERVICE_FILE="/etc/systemd/system/smart-home-backend.service"
if [ -f "$SERVICE_FILE" ]; then
    echo "✅ systemd 服务已存在，重启服务..."
    systemctl restart smart-home-backend
else
    echo "⚠️  systemd 服务文件未找到，请手动安装:"
    echo "   cp smart-home-backend.service /etc/systemd/system/"
    echo "   systemctl daemon-reload"
    echo "   systemctl enable smart-home-backend"
    echo "   systemctl start smart-home-backend"
fi

# 4. 检查服务状态
echo "🔍 检查服务状态..."
systemctl status smart-home-backend --no-pager || true

echo ""
echo "========================================"
echo "✅ 部署完成！"
echo "🌐 访问地址: http://8.137.21.211:8000"
echo "📖 API 文档: http://8.137.21.211:8000/docs"
echo "========================================"
