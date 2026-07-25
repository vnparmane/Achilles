@echo off
cd /d "%~dp0.."
echo Installing dependencies...
pip install -r requirements.txt
echo Building TextileERP...
pyinstaller TextileERP.spec
echo Build complete. Output in dist/TextileERP.exe
pause
