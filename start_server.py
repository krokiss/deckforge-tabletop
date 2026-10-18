#!/usr/bin/env python3
"""Start DeckForge server as a detached background process."""
import os
import sys
import subprocess

def main():
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create the detached process
    creationflags = 0
    if sys.platform == 'win32':
        creationflags = subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
    
    proc = subprocess.Popen(
        [sys.executable, 'launch.py'],
        cwd=script_dir,
        stdout=open(os.path.join(script_dir, 'preview-1e67193c-4a2f-4b3a-a000-4280d5fbe87e.log'), 'w'),
        stderr=open(os.path.join(script_dir, 'preview-1e67193c-4a2f-4b3a-a000-4280d5fbe87e.log.err'), 'w'),
        creationflags=creationflags
    )
    
    # Output the PID so the calling process can track it
    print(f"PID:{proc.pid}")
    
    # Detach by leaving the process running
    return proc.pid

if __name__ == '__main__':
    main()
