"""Start the server detached."""
import subprocess, sys, os, time

log = os.path.join(os.path.dirname(__file__), 'preview-1e67193c-4a2f-4b3a-a000-4280d5fbe87e.log')
log_err = log + '.err'
server = os.path.join(os.path.dirname(__file__), 'server.py')

p = subprocess.Popen(
    [sys.executable, server],
    stdout=open(log, 'w'),
    stderr=open(log_err, 'w'),
    cwd=os.path.dirname(__file__),
    creationflags=getattr(subprocess, 'DETACHED_PROCESS', 0) | getattr(subprocess, 'CREATE_NO_WINDOW', 0),
)
print(f'Server started PID {p.pid}')
