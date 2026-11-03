@echo off
chcp 65001 >nul
title LexiFragment - 英语碎片化知识库本地服务器
echo ========================================================
echo   LexiFragment · 英语碎片化知识库 本地启动器
echo ========================================================
echo.
echo [1/2] 正在启动本地极速 HTTP 服务器 (端口 8000)...
start http://localhost:8000
python -m http.server 8000
pause
