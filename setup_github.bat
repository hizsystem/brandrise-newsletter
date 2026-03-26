@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo HIZ 뉴스레터 GitHub Pages 초기 설정
echo.
python setup_github.py
pause
