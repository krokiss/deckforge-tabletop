#!/usr/bin/env python3
"""Launcher for DeckForge dev server."""
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.argv = ['server.py', '--port', '8420']
import server
server.main()
