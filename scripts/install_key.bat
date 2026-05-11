@echo off
chcp 65001 >nul
echo 正在安装 SSH 公钥到服务器 (密码: YuanYe0129)
echo.
echo 请在弹出的窗口中输入密码 (不会显示): YuanYe0129
echo.
echo 方法1: 使用密码登录并安装密钥...
echo.
:: 复制公钥内容
type "%USERPROFILE%\.ssh\id_rsa.pub" > "%TEMP%\smart_home_pubkey.txt"

:: SCP 公钥到服务器
scp -o StrictHostKeyChecking=no "%TEMP%\smart_home_pubkey.txt" root@8.137.21.211:/root/

:: SSH 登录并将公钥加入 authorized_keys
ssh -o StrictHostKeyChecking=no root@8.137.21.211 "mkdir -p ~/.ssh && cat ~/smart_home_pubkey.txt >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys && rm ~/smart_home_pubkey.txt && echo 密钥安装成功！"

pause
