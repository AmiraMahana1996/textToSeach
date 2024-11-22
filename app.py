import os
import uuid
import pyttsx3
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Ensure audio directory exists
os.makedirs('static/audio', exist_ok=True)

def get_voice_by_gender(gender='female'):
    """
    Intelligently select voice based on gender
    """
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    
    # Comprehensive voice matching
    gender_keywords = {
        'female': ['female', 'woman', 'girl'],
        'male': ['male', 'man', 'boy']
    }
    
    for voice in voices:
        # Check voice name and ID for gender keywords
        voice_match = any(
            keyword in voice.name.lower() or 
            keyword in voice.id.lower()
            for keyword in gender_keywords.get(gender.lower(), [])
        )
        
        if voice_match:
            return voice
    
    # Fallback to first available voice if no match
    return voices[0] if voices else None

def text_to_speech(text, voice_gender='female', rate=150):
    """
    Convert text to speech with voice gender selection
    """
    # Initialize text-to-speech engine
    engine = pyttsx3.init()
    
    # Select voice
    selected_voice = get_voice_by_gender(voice_gender)
    
    if selected_voice:
        engine.setProperty('voice', selected_voice.id)
    
    # Set speech rate
    engine.setProperty('rate', rate)
    
    # Generate unique filename
    filename = f'{uuid.uuid4()}.mp3'
    full_path = os.path.join('static', 'audio', filename)
    
    # Save speech to file
    engine.save_to_file(text, full_path)
    engine.runAndWait()
    
    return filename

@app.route('/voices', methods=['GET'])
def list_voices():
    """
    Endpoint to list available voices
    """
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    
    voice_list = [
        {
            'id': voice.id,
            'name': voice.name
        } for voice in voices
    ]
    
    return jsonify(voice_list)

@app.route('/tts', methods=['POST'])
def generate_speech():
    """
    API endpoint for text-to-speech conversion
    """
    data = request.json
    
    # Validate input
    if not data or 'text' not in data:
        return jsonify({"error": "Text is required"}), 400
    
    text = data['text']

    rate = data.get('rate', 150)
    
    try:
        # Convert text to speech
        filename = text_to_speech(text, "female", rate)
        
        # Return audio file details
        return jsonify({
            "message": "Speech generated successfully",
            "audio_url": f"/audio/{filename}",
            "filename": filename
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/audio/<filename>')
def serve_audio(filename):
    """
    Serve audio files
    """
    try:
        return send_file(os.path.join('static', 'audio', filename), 
                         mimetype='audio/mpeg')
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)