@echo off
rem Inicia o servidor e abre o sistema no navegador (http://localhost:8000)
cd /d "%~dp0"
python app_web.py
pause
