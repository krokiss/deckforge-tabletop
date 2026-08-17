FROM python:3.11-slim

WORKDIR /app

# DeckForge is Python-stdlib-only — no pip install needed.
COPY . .

EXPOSE 8420

# $PORT (set by Render/Railway/etc.) is honored by server.py automatically.
CMD ["python", "server.py", "--host", "0.0.0.0"]
