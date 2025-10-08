# Bark TTS Cloud Run Service

Simple Bark TTS API server for Cloud Run deployment.

## Files:
- `bark_server.py` - Flask API server
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container configuration

## Endpoints:
- `GET /healthz` - Health check
- `POST /tts` - Text to speech conversion

## Usage:
```bash
curl -X POST https://your-service.run.app/tts \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world"}' \
  --output speech.wav
```