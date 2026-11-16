@echo off
setlocal
set "ROOT=%~dp0"

start "FiremeX model 8101" powershell.exe -NoExit -Command "$env:PORT='8101'; Set-Location '%ROOT%firemex-model'; python .\detect_service.py"
start "FiremeX backend 8081" powershell.exe -NoExit -Command "$env:PORT='8081'; $env:ADDITIONAL_PORTS=','; $env:MODEL_URL='http://127.0.0.1:8101'; $env:CORS_ORIGINS='http://localhost:5173,http://localhost:5174'; Set-Location '%ROOT%backend'; go run .\main.go"
start "FiremeX frontend 5174" powershell.exe -NoExit -Command "$env:VITE_DEV_BACKEND='http://localhost:8081'; Set-Location '%ROOT%frontend'; npm run dev -- --host 127.0.0.1 --port 5174 --strictPort"

endlocal
