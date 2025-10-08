FROM python:3.10-slim

# soundfile system dependency
RUN apt-get update && apt-get install -y --no-install-recommends libsndfile1 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY bark_server.py ./

# Cloud Run uses $PORT
ENV PORT=8080
CMD exec gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 4 bark_server:app