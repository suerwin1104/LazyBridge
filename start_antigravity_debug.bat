@echo off
title LazyBridge - Antigravity Debug Launcher
echo ========================================
echo  LazyBridge - Antigravity 除錯模式啟動器
echo ========================================
echo.

SET AG_EXE=%LOCALAPPDATA%\Programs\Antigravity\Antigravity.exe

IF NOT EXIST "%AG_EXE%" (
    echo [錯誤] 找不到 Antigravity.exe：
    echo   %AG_EXE%
    pause
    exit /b 1
)

echo [路徑] %AG_EXE%
echo.

REM 檢查是否已有帶 debug port 的 Antigravity 在執行
echo [檢查] 偵測現有 Antigravity 程序...
netstat -an | findstr ":9222" >nul 2>&1
if %ERRORLEVEL%==0 (
    echo [OK] CDP 端口 9222 已在監聽中，不需重啟！
    echo 直接執行 main.py 即可。
    goto :end
)

echo [警告] CDP 端口 9222 未偵測到。
echo.
echo 若 Antigravity 已在執行，必須先關閉才能重啟帶 debug port 的版本。
echo.
echo 選項:
echo   [1] 關閉現有 Antigravity 並以 debug port 重新啟動
echo   [2] 取消（保留目前的 Antigravity）
echo.
set /p CHOICE="請選擇 [1/2]: "

if "%CHOICE%"=="1" goto :restart
echo 已取消。
goto :end

:restart
echo.
echo [關閉] 結束現有 Antigravity 程序...
taskkill /IM Antigravity.exe /F >nul 2>&1
timeout /t 2 /nobreak >nul

echo [啟動] 以 remote-debugging-port=9222 啟動 Antigravity...
start "" "%AG_EXE%" --remote-debugging-port=9222

echo.
echo [等待] 請等候 Antigravity 完全載入（約 5-10 秒）...
timeout /t 8 /nobreak

echo.
echo [驗證] 確認 CDP 端口...
netstat -an | findstr ":9222"
if %ERRORLEVEL%==0 (
    echo.
    echo [成功] CDP 9222 已就緒！可以執行 main.py
) else (
    echo.
    echo [警告] 端口尚未就緒，請再等幾秒後手動執行 check.py 確認
)

:end
echo.
pause
