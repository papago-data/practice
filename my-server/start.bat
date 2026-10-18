@echo off
chcp 65001 >nul
title 纪念相册一键启动
cd /d "%~dp0"

echo ==========================================
echo      一周年纪念相册 · 一键启动
echo ==========================================
echo.
echo [1/2] 启动本地服务器 (端口 3000) ...
start "Server" cmd /k ""C:\Program Files\node.exe" server.js"

timeout /t 2 /nobreak >nul

echo [2/2] 建立公网隧道，链接显示在下方 ...
echo.
echo   把下面的 xxx.trycloudflare.com 链接发给任何手机或电脑即可访问
echo   （本机也可用 http://localhost:3000 访问）
echo.
echo   停止请在本窗口按 Ctrl+C
echo ==========================================
echo.
cloudflared.exe tunnel --url http://localhost:3000

echo.
echo 隧道已停止，按任意键退出...
pause >nul
