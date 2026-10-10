@echo off
cd /d "%~dp0"
python app.py
if errorlevel 1 (
  echo.
  echo Could not start with "python". If Python is installed via the Windows launcher, try running "py app.py" in PowerShell.
  pause
)
