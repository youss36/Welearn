@echo off
setlocal
for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "$route = Get-NetRoute -DestinationPrefix '0.0.0.0/0' ^| Sort-Object RouteMetric ^| Select-Object -First 1; (Get-NetIPAddress -InterfaceIndex $route.ifIndex -AddressFamily IPv4 ^| Where-Object { $_.IPAddress -notlike '169.254*' } ^| Select-Object -First 1 -ExpandProperty IPAddress)"`) do set LAN_IP=%%I
if "%LAN_IP%"=="" set LAN_IP=localhost
echo Frontend accessible at: http://%LAN_IP%:5500/dashboard.html
start "We Learn Frontend" cmd /k "python -m http.server 5500 --bind 0.0.0.0"
timeout /t 2 /nobreak >nul
start "" "http://%LAN_IP%:5500/dashboard.html"
endlocal
