# 找到佔用 9222 的 PID 並強制關閉
#Stop-Process -Id (Get-NetTCPConnection -LocalPort 9222).OwningProcess -Force
#taskkill /F /IM Antigravity.exe /T
& "C:\Users\USER\AppData\Local\Programs\Antigravity\Antigravity.exe" --remote-debugging-port=9222