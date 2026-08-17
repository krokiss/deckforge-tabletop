@echo off
title DeckForge - Presentation Builder
cd /d "%~dp0"
start "" http://127.0.0.1:8420
python server.py
pause
