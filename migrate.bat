@echo off
cd /d "%~dp0"
echo Migrating phrase history from Korean to Japanese format...
py migrate_history.py
pause
