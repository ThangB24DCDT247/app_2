@echo off
set UV=C:\Users\THANG\.local\bin\uv.exe
set APP=%~dp0main.py
cd /d "%~dp0"
echo Dang khoi dong PTIT MQTT Controller...
"%UV%" run --with paho-mqtt --with Pillow "%APP%"
pause
