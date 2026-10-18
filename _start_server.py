import subprocess, os, sys, signal, time

PORT = 8420
LOG = os.path.join(os.path.dirname(__file__), "preview-1e67193c-4a2f-4b3a-a000-4280d5fbe87e.log")
LOG_ERR = LOG + ".err"

# Kill existing process on port
try:
    out = subprocess.check_output(
        f'netstat -ano | findstr ":{PORT}" | findstr LISTENING',
        shell=True, text=True, stderr=subprocess.DEVNULL
    )
    for line in out.strip().splitlines():
        pid = line.strip().split()[-1]
        subprocess.run(f"taskkill /F /PID {pid}", shell=True,
                       capture_output=True, timeout=5)
except Exception:
    pass

time.sleep(1)

# Start server detached via PowerShell
ps = (
    f'(Start-Process -FilePath "python.exe" '
    f'-ArgumentList "server.py","--host","0.0.0.0","--port","{PORT}" '
    f'-RedirectStandardOutput "{LOG}" -RedirectStandardError "{LOG_ERR}" '
    f'-WindowStyle Hidden -PassThru).Id'
)
result = subprocess.run(
    ["powershell", "-NoProfile", "-Command", ps],
    capture_output=True, text=True, timeout=15
)
pid = result.stdout.strip()
print(f"Started DeckForge on port {PORT}, PID {pid}")

# Confirm it's alive
time.sleep(3)
try:
    check = subprocess.run(
        ["powershell", "-NoProfile", "-Command", f"Get-Process -Id {pid}"],
        capture_output=True, text=True, timeout=10
    )
    if check.returncode == 0:
        print("Process confirmed alive")
    else:
        print("WARNING: process may have exited")
except Exception:
    pass
