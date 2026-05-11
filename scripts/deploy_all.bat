@echo off
chcp 65001 >nul
cd /d C:\Users\yuany\Documents\Person\smart-home

echo ======================================== > deploy_log.txt 2>&1
echo ESP32 Smart Home - Deploy to Cloud Server >> deploy_log.txt 2>&1
echo ======================================== >> deploy_log.txt 2>&1
echo. >> deploy_log.txt 2>&1

echo Step 1: Create remote directory >> deploy_log.txt 2>&1
ssh root@8.137.21.211 "mkdir -p /root/smart-home/backend/static" >> deploy_log.txt 2>&1
echo. >> deploy_log.txt 2>&1

echo Step 2: Copy files to server >> deploy_log.txt 2>&1
scp backend/main.py root@8.137.21.211:/root/smart-home/backend/ >> deploy_log.txt 2>&1
scp backend/requirements.txt root@8.137.21.211:/root/smart-home/backend/ >> deploy_log.txt 2>&1
scp backend/smart-home-backend.service root@8.137.21.211:/root/smart-home/backend/ >> deploy_log.txt 2>&1
scp backend/deploy.sh root@8.137.21.211:/root/smart-home/backend/ >> deploy_log.txt 2>&1
scp backend/static/index.html root@8.137.21.211:/root/smart-home/backend/static/ >> deploy_log.txt 2>&1
echo. >> deploy_log.txt 2>&1

echo Step 3: Install Python dependencies >> deploy_log.txt 2>&1
ssh root@8.137.21.211 "pip3 install -r /root/smart-home/backend/requirements.txt" >> deploy_log.txt 2>&1
echo. >> deploy_log.txt 2>&1

echo Step 4: Setup systemd service >> deploy_log.txt 2>&1
ssh root@8.137.21.211 "cp /root/smart-home/backend/smart-home-backend.service /etc/systemd/system/ && systemctl daemon-reload && systemctl enable smart-home-backend" >> deploy_log.txt 2>&1
echo. >> deploy_log.txt 2>&1

echo Step 5: Start the service >> deploy_log.txt 2>&1
ssh root@8.137.21.211 "systemctl restart smart-home-backend" >> deploy_log.txt 2>&1
echo. >> deploy_log.txt 2>&1

echo Step 6: Check service status >> deploy_log.txt 2>&1
ssh root@8.137.21.211 "sleep 3 && systemctl status smart-home-backend --no-pager -l" >> deploy_log.txt 2>&1
echo. >> deploy_log.txt 2>&1

echo Step 7: Configure firewall >> deploy_log.txt 2>&1
ssh root@8.137.21.211 "ufw allow 8000/tcp && ufw reload" >> deploy_log.txt 2>&1
echo. >> deploy_log.txt 2>&1

echo Step 8: Verify access >> deploy_log.txt 2>&1
ssh root@8.137.21.211 "curl -s -o /dev/null -w 'HTTP Status: %%{http_code}\n' http://localhost:8000/" >> deploy_log.txt 2>&1
echo. >> deploy_log.txt 2>&1

type deploy_log.txt
echo.
echo ========================================
echo Check deploy_log.txt for full details.
echo.
echo To visit: http://8.137.21.211:8000
echo ========================================
pause
