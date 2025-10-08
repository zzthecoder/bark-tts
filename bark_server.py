# Bark TTS Server for AI Avatar
# pip install bark flask flask-cors soundfile numpy

from bark import generate_audio, SAMPLE_RATE
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import io
import soundfile as sf
import numpy as np
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Pre-load Bark models for faster generation
logger.info("Loading Bark models...")
# This will download models on first run (can take a few minutes)
try:
    # Generate a test audio to initialize models
    test_audio = generate_audio("Hello", history_prompt="v2/en_speaker_6")
    logger.info("Bark models loaded successfully!")
except Exception as e:
    logger.error(f"Error loading Bark models: {e}")

@app.route("/")
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "Bark TTS Server",
        "version": "1.0.0"
    })

@app.route("/tts", methods=["GET", "POST"])
def text_to_speech():
    """Convert text to speech using Bark"""
    try:
        # Get text from query params or POST body
        if request.method == "GET":
            text = request.args.get("text", "")
        else:
            data = request.get_json()
            text = data.get("text", "") if data else ""
        
        if not text:
            return jsonify({"error": "No text provided"}), 400
        
        # Limit text length for reasonable generation time
        if len(text) > 200:
            text = text[:200] + "..."
        
        logger.info(f"Generating speech for: {text[:50]}...")
        
        # Generate audio with Bark
        # Use a specific voice preset for consistency
        audio_array = generate_audio(
            text, 
            history_prompt="v2/en_speaker_6",  # Professional female voice
            text_temp=0.7,
            waveform_temp=0.7
        )
        
        # Convert to audio file
        buffer = io.BytesIO()
        sf.write(buffer, audio_array, SAMPLE_RATE, format='WAV')
        buffer.seek(0)
        
        logger.info("Audio generated successfully!")
        
        return send_file(
            buffer,
            mimetype="audio/wav",
            as_attachment=False,
            download_name="speech.wav"
        )
        
    except Exception as e:
        logger.error(f"TTS Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/voices")
def get_available_voices():
    """Get list of available voice presets"""
    voices = [
        {"id": "v2/en_speaker_0", "name": "Professional Male", "gender": "male"},
        {"id": "v2/en_speaker_1", "name": "Casual Male", "gender": "male"},
        {"id": "v2/en_speaker_2", "name": "Young Male", "gender": "male"},
        {"id": "v2/en_speaker_3", "name": "Mature Male", "gender": "male"},
        {"id": "v2/en_speaker_4", "name": "Professional Female", "gender": "female"},
        {"id": "v2/en_speaker_5", "name": "Casual Female", "gender": "female"},
        {"id": "v2/en_speaker_6", "name": "Young Female", "gender": "female"},
        {"id": "v2/en_speaker_7", "name": "Mature Female", "gender": "female"},
        {"id": "v2/en_speaker_8", "name": "Energetic", "gender": "neutral"},
        {"id": "v2/en_speaker_9", "name": "Calm", "gender": "neutral"},
    ]
    return jsonify({"voices": voices})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"Starting Bark TTS Server on port {port}")
    logger.info("Note: First audio generation may take longer as models initialize")
    app.run(host="0.0.0.0", port=port, debug=False)