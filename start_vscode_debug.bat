@echo off
title LazyBridge - VS Code Debug Launcher
echo ========================================
echo  LazyBridge VS Code 除錯模式啟動器
echo ========================================
echo.
echo 正在以 remote-debugging-port=9222 啟動 VS Code...
echo.

REM 先確認 VS Code 是否已在執行
tasklist /FI "IMAGENAME eq Code.exe" 2>NUL | find /I /N "Code.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [警告] 偵測到 VS Code 已在執行中。
    echo 為了讓 CDP 端口正常運作，建議先關閉所有 VS Code 視窗後再啟動。
    echo.
    echo 按任意鍵繼續啟動（或按 Ctrl+C 取消）...
    pause > nul
)

REM 帶 debug port 啟動 VS Code，並開啟 LazyBridge 資料夾
code --remote-debugging-port=9222 "C:\Users\USER\LazyBridge"

echo.
echo VS Code 啟動命令已發送。
echo 請等待 VS Code 完全載入後，再執行 main.py 或 diagnose.py
echo.
timeout /t 3
