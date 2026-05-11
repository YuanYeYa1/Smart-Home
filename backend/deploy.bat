@echo off
cd /d "%~dp0"
echo Running deployment script...
python run_deploy.py > deploy_result.txt 2>&1
type deploy_result.txt
echo.
echo Done! Check deploy_result.txt for full output.
pause
