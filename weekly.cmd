@echo off
rem DeckForge weekly maintenance, registered as the Windows task "DeckForge weekly".
rem Steps: pull latest code -> archive live-site history -> Render deploy -> backup + zip.
rem Full log: data\weekly.log
cd /d "%~dp0"
set "PY=python"
where %PY% >nul 2>&1 || set "PY=C:\Program Files\Python311\python.exe"
"%PY%" weekly.py
