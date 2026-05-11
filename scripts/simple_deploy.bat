@echo off
chcp 65001 >nul
set LOG=C:\Users\yuany\Documents\Person\smart-home\simple_log.txt
echo Starting deploy... > %LOG%
echo ======================== >> %LOG%

:: Step 1: Test SSH key
echo [1] Testing SSH... >> %LOG%
ssh -o BatchMode=yes -o StrictHostKeyChecking=no root@8.137.21.211 "echo SSH_OK" >> %LOG% 2>&1
if %ERRORLEVEL% neq 0 (
    echo SSH key auth FAILED - you need to enter password once >> %LOG%
    echo Please manually run: ssh-copy-id root@8.137.21.211 >> %LOG%
    echo OR manually enter the password below: >> %LOG%
    ssh root@8.137.21.211 "mkdir -p ~/.ssh && echo done" >> %LOG% 2>&1
)

:: Step 2: Create remote directories
echo [2] Creating remote directories... >> %LOG%
ssh -o BatchMode=yes root@8.137.21.211 "mkdir -p /root/smart-home/backend/static" >> %LOG% 2>&1

:: Step 3: Copy files
echo [3] Copying files... >> %LOG%
scp -o StrictHostKeyChecking=no C:\Users\yuany\Documents\Person\smart-home\backend\main.py root@8.137.21.211:/root/smart-home/backend/ >> %LOG% 2>&1
scp -o StrictHostKeyChecking=no C:\Users\yuany\Documents\Person\smart-home\backend\requirements.txt root@8.137.21.211:/root/smart-home/backend/ >> %LOG% 2>&1
scp -o StrictHostKeyChecking=no C:\Users\yuany\Documents\Person\smart-home\backend\smart-home-backend.service root@8.137.21.211:/root/smart-home/backend/ >> %LOG% 2>&1
scp -o StrictHostKeyChecking=no C:\Users\yuany\Documents\Person\smart-home\backend\static\index.html root@8.137.21.211:/root/smart-home/backend/static/ >> %LOG% 2>&1

:: Step 4: Install deps
echo [4] Installing Python packages... >> %LOG%
ssh -o BatchMode=yes root@8.137.21.211 "pip3 install -r /root/smart-home/backend/requirements.txt" >> %LOG% 2>&1

:: Step 5: Setup systemd
echo [5] Setting up systemd... >> %LOG%
ssh -o BatchMode=yes root@8.137.21.211 "cp /root/smart-home/backend/smart-home-backend.service /etc/systemd/system/ && systemctl daemon-reload && systemctl enable smart-home-backend" >> %LOG% 2>&1

:: Step 6: Start
echo [6] Starting service... >> %LOG%
ssh -o BatchMode=yes root@8.137.21.211 "systemctl restart smart-home-backend" >> %LOG% 2>&1

:: Wait
ping -n 4 127.0.0.1 >nul

:: Step 7: Check status
echo [7] Checking status... >> %LOG%
ssh -o BatchMode=yes root@8.137.21.211 "systemctl status smart-home-backend --no-pager -l | head -30" >> %LOG% 2>&1

:: Step 8: Firewall
echo [8] Firewall... >> %LOG%
ssh -o BatchMode=yes root@8.137.21.211 "ufw allow 8000/tcp && ufw reload" >> %LOG% 2>&1

:: Step 9: Test
echo [9] Testing... >> %LOG%
ssh -o BatchMode=yes root@8.137.21.211 "curl -s http://localhost:8000/ | head -5" >> %LOG% 2>&1

:: Done
echo ======================== >> %LOG%
echo Done! Check %LOG% for details. >> %LOG%
echo. >> %LOG%
type %LOG%
echo.
echo ========================
echo Check: %LOG%
echo Visit: http://8.137.21.211:8000
echo ========================
pause
