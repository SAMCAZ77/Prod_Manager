@echo off
REM Builds Prod_Manager.exe on Windows. Run this from inside this folder,
REM with Python installed and requirements.txt already pip-installed:
REM     pip install -r requirements.txt
REM     build.bat

pyinstaller --onefile --windowed --name Prod_Manager --icon=icon.ico main.py

echo.
echo Done. Find Prod_Manager.exe inside the "dist" folder.
pause
