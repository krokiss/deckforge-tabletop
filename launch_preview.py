#!/usr/bin/env python3
"""Start the DeckForge dev server on port 8420."""
import os, sys, subprocess, time

root = os.path.dirname(os.path.abspath(__file__))
os.chdir(root)
server = os.path.join(root, "server.py")
log = os.path.join(root, "preview-1e67193c-4a2f-4b3a-a000-4280d5fbe87e.log")
log_err = log + ".err"

proc = subprocess.Popen(
    [sys.executable, server],
    cwd=root,
    stdout=open(log, "w", encoding="utf-8"),
    stderr=open(log_err, "w", encoding="utf-8"),
)
print(proc.pid)
sys.exit(0)
