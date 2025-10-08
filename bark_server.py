# bark_server.py
import io, os, time, json, math
from flask import Flask, request, send_file, Response
from flask_cors import CORS
from bark import generate_audio, SAMPLE_RATE
import soundfile as sf
import numpy as np

MAX_TEXT_CHARS = 600        # keep requests bounded
SYNTH_TIMEOUT_S = 30        # avoid runaway jobs

app = Flask(__name__)
CORS(app, resources={r"/tts": {"origins": "*"}})

@app.get("/healthz")
def health():
    return {"ok": True}, 200

@app.post("/tts")
def tts():
    # 1) validate
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return {"error": "Missing JSON body with { text }"}, 400
    if len(text) > MAX_TEXT_CHARS:
        return {"error": f"text too long (>{MAX_TEXT_CHARS})"}, 413

    start = time.time()

    # 2) synthesize with a timeout guard
    try:
        audio_array = generate_audio(text)  # float32 numpy [-1..1]
    except Exception as e:
        return {"error": f"TTS failed: {e}"}, 500

    if time.time() - start > SYNTH_TIMEOUT_S:
        return {"error": "TTS timeout"}, 504

    # 3) encode WAV to memory
    buf = io.BytesIO()
    sf.write(buf, audio_array, SAMPLE_RATE, format="WAV")
    buf.seek(0)

    # OPTIONAL: compute a coarse loudness envelope and send as header (json)
    # client can read it from 'X-Envelope' header; small array ~200 points
    try:
        hop = int(SAMPLE_RATE * 0.05)  # 50 ms windows
        env = []
        arr = audio_array.astype(np.float32)
        for i in range(0, len(arr), hop):
            window = arr[i:i+hop]
            if len(window) == 0: break
            rms = float(np.sqrt(np.mean(window**2)) or 0.0)
            env.append(round(rms, 5))
        envelope_json = json.dumps(env)
    except Exception:
        envelope_json = "[]"

    # 4) return streaming response with headers
    headers = {
        "Content-Type": "audio/wav",
        "Cache-Control": "no-store",
        "X-Envelope": envelope_json,  # optional loudness envelope
    }
    return send_file(buf, mimetype="audio/wav",
                     download_name="speech.wav",
                     as_attachment=False,
                     headers=headers)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)