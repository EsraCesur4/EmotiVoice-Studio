#!/usr/bin/env python3
"""
Flask API for EmotiVoice-Avatar Chat Demo
"""

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
import threading
import os
import sys
import subprocess
import json
from pathlib import Path
import uuid
from datetime import datetime
import shutil
import tempfile
import time
from text_to_avatar import classify_emotion, generate_speech
import logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)

# Global progress tracker
progress = {"value": 0, "stage": "idle"}
progress_lock = threading.Lock()

# Language Detection
try:
    from langdetect import detect
    HAVE_LANGDETECT = True
except ImportError:
    HAVE_LANGDETECT = False

def detect_language(text: str) -> str:
    """Detect language from text, return 'en' or 'tr'"""
    if not HAVE_LANGDETECT:
        return "en"  # default fallback
    try:
        lang = detect(text)
        return "tr" if lang == "tr" else "en"
    except:
        return "en"

# Folder Paths
BASE_DIR = Path(__file__).parent.parent

# /data for writability on Hugging Face Spaces
BASE_DATA = Path(os.getenv("DATA_DIR", "/data"))
UPLOAD_FOLDER = BASE_DATA / "uploads"
OUTPUT_FOLDER = BASE_DATA / "outputs"
MOUTH_ROOT = BASE_DIR / "assets" / "mouthsets"
AVATAR_ROOT = BASE_DIR / "assets" / "avatar"
LIPSYNC_SCRIPT = Path(__file__).parent / "lipsync.py"
TEXT_AVATAR_SCRIPT = Path(__file__).parent / "text_to_avatar.py"

# Create folders
UPLOAD_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)

print("EmotiVoice-Avatar Backend Server")

# TTS availability check
TTS_AVAILABLE = {}
try:
    import edge_tts
    TTS_AVAILABLE['edge'] = True
except ImportError:
    TTS_AVAILABLE['edge'] = False

print(f" TTS engines available: {[k for k, v in TTS_AVAILABLE.items() if v]}")

# import avatar_composer
try:
    from avatar_composer import AvatarComposer
    avatar_composer = AvatarComposer(AVATAR_ROOT)
    HAS_AVATAR_COMPOSER = True
except ImportError:
    HAS_AVATAR_COMPOSER = False
    avatar_composer = None

def set_progress(value, stage=""):
    with progress_lock:
        progress["value"] = int(value)
        progress["stage"] = stage

@app.route("/api/progress", methods=["GET"])
def get_progress():
    with progress_lock:
        return jsonify(progress)

@app.route('/api/avatar/options', methods=['GET'])
def get_avatar_options():
    """Get available avatar customization options"""
    if not HAS_AVATAR_COMPOSER:
        return jsonify({
            'error': 'Avatar composer not available',
            'default_options': {
                'gender': ['female', 'male'],
                'hair_style': ['wavy', 'straight', 'curly', 'short'],
                'hair_color': ['brown', 'black', 'blonde', 'red'],
                'eye_color': ['brown', 'blue', 'green', 'hazel'],
                'background_color': ['pink', 'blue', 'green', 'purple', 'white']
            }
        }), 200
    try:
        options = avatar_composer.get_available_options()
        return jsonify(options)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tts/engines', methods=['GET'])
def get_tts_engines():
    """Get available TTS engines"""
    return jsonify({
        'available': TTS_AVAILABLE,
        'default': 'edge' if TTS_AVAILABLE['edge'] else None,
        'voices': {
            'edge': [
                'en-US-AriaNeural',
                'en-US-GuyNeural',
                'en-GB-SoniaNeural',
                'en-GB-RyanNeural',
                'tr-TR-AhmetNeural',
                'tr-TR-EmelNeural'
            ]
        },
        'emotion_based': TTS_AVAILABLE.get('edge', False)
    })

@app.route('/api/process-text', methods=['POST'])
def process_text():
    """
    Process text → EMOTION-BASED TTS → detect emotion → generate lipsync video
    """
    set_progress(0, "Starting...")
    start_total = time.time()
    try:
        data = request.json
        
        # Validate text input
        set_progress(10, "Generating TTS speech")
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400
        
        text = data['text'].strip()
        if not text:
            return jsonify({'error': 'Empty text'}), 400
        
        detected_language = detect_language(text)
        tts_lang = data.get('tts_lang', detected_language)  # Use detected lang as default
        print(f" Detected language: {detected_language}")
        
        # Get TTS settings
        tts_engine = data.get('tts_engine', 'auto')
        tts_lang = data.get('tts_lang', 'en')
        use_emotion_voice = data.get('use_emotion_voice', True)  # NEW: Enable emotion-based voice
        
        # Get avatar configuration
        avatar_config = {
            'gender': data.get('gender', 'female'),
            'hair_style': data.get('hair_style', 'wavy'),
            'hair_color': data.get('hair_color', 'brown'),
            'eye_color': data.get('eye_color', 'brown'),
            'background_color': data.get('background_color', 'pink')
        }
        
        print(f"\n Text input ({len(text)} chars): {text[:100]}...")
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())[:8]
        print(f" New job: {job_id}")
        
        # Create job output directory
        job_output_dir = OUTPUT_FOLDER / job_id
        job_output_dir.mkdir(exist_ok=True)
        
        # STEP 1: Detect emotion FIRST (before TTS and avatar composition)
        print(f" Detecting emotion from text...")
        set_progress(40, "Classifying emotion")
        try:
            from text_to_avatar import classify_emotion
            predicted_emotion = classify_emotion(text, language=detected_language)
            print(f" Predicted emotion: {predicted_emotion}")
        except Exception as e:
            print(f" Emotion detection failed: {e}, using neutral")
            predicted_emotion = "neutral"
        
        # Generate audio from text using EMOTION-BASED TTS
        audio_path = job_output_dir / "tts_speech.wav"
        print(f"Generating speech...")
        
        start_tts = time.time()
        
        # Create a temporary Python script for TTS generation
        temp_tts_script = job_output_dir / "temp_tts.py"
        
        # Build TTS script with emotion support
        if use_emotion_voice and TTS_AVAILABLE.get('edge'):
            tts_script_content = f'''import sys
from pathlib import Path
sys.path.insert(0, r"{Path(__file__).parent}")
from text_to_avatar import generate_speech
try:
    generate_speech(
        text="""{text}""",
        output_path=Path(r"{audio_path}"),
        engine="edge",
        emotion="{predicted_emotion}",
        lang="{detected_language}"
    )
    print("TTS_SUCCESS")
except Exception as e:
    import traceback
    print(f"TTS_ERROR: {{e}}")
    traceback.print_exc()
    sys.exit(1)
'''
        else:
            # Fallback to non-emotion TTS
            tts_script_content = f'''import sys
from pathlib import Path
sys.path.insert(0, r"{Path(__file__).parent}")
from text_to_avatar import generate_speech
try:
    generate_speech(
        text="""{text}""",
        output_path=Path(r"{audio_path}"),
        engine="{tts_engine}",
        lang="{detected_language}",
        gender="{avatar_config.get('gender', 'female')}"
    )
    print("TTS_SUCCESS")
except Exception as e:
    import traceback
    print(f"TTS_ERROR: {{e}}")
    traceback.print_exc()
    sys.exit(1)
'''
        
        temp_tts_script.write_text(tts_script_content, encoding='utf-8')
        
        tts_result = subprocess.run(
            [sys.executable, str(temp_tts_script)],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=str(Path(__file__).parent)
        )
        
        tts_duration = time.time() - start_tts
        
        # Clean up temp script
        try:
            temp_tts_script.unlink()
        except:
            pass
        
        if tts_result.returncode != 0 or "TTS_SUCCESS" not in tts_result.stdout:
            print(f" TTS failed (took {tts_duration:.2f}s): {tts_result.stderr}")
            return jsonify({
                'error': 'TTS generation failed',
                'details': tts_result.stderr
            }), 500
        
        if not audio_path.exists():
            print(f" TTS audio not generated (took {tts_duration:.2f}s)")
            return jsonify({
                'error': 'TTS audio not generated',
                'details': 'Audio file not found after TTS'
            }), 500
        
        
        print(f" Speech generated with emotion: {predicted_emotion} (took {tts_duration:.2f}s)")
        
        # STEP 2: Compose avatar for the predicted emotion
        mouth_composition_duration = 0
        set_progress(70, "Rendering avatar")
        if HAS_AVATAR_COMPOSER:
            custom_mouthsets = job_output_dir / "custom_avatar"
            print(f"Composing avatar for emotion: {predicted_emotion}")
            start_compose = time.time()
            try:
                avatar_composer.compose_single_emotion(
                    avatar_config, 
                    custom_mouthsets, 
                    emotion=predicted_emotion
                )
                mouth_composition_duration = time.time() - start_compose
                print(f" Custom avatar composed ({predicted_emotion}) in {mouth_composition_duration:.2f}s")
                mouth_dir = custom_mouthsets / predicted_emotion
            except Exception as e:
                print(f" Avatar composition failed: {e}, using default")
                mouth_dir = MOUTH_ROOT / predicted_emotion
        else:
            mouth_dir = MOUTH_ROOT / predicted_emotion
        
        # STEP 3: Run lipsync pipeline
        cmd = [
            sys.executable, str(LIPSYNC_SCRIPT),
            "--audio", str(audio_path),
            "--mouths", str(mouth_dir),
            "--out_dir", str(job_output_dir),
            "--fps", "20",
            "--whisper_model", "base",
            "--lipsync_offset", "-0.10" if detected_language == "tr" else "-0.10",
            "--target_height", "720"
        ]
        
        print(f" Running lipsync pipeline...")
        start_pipeline = time.time()
        set_progress(90, "Encoding video")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=Path(__file__).parent
        )
        
        pipeline_duration = time.time() - start_pipeline
        total_duration = time.time() - start_total
        
        if result.returncode != 0:
            print(f" Pipeline failed (took {pipeline_duration:.2f}s, total {total_duration:.2f}s):")
            print(result.stderr)
            return jsonify({
                'error': 'Processing failed',
                'details': result.stderr[-500:],
                'timing': {
                    'total_duration_s': f"{total_duration:.2f}",
                    'tts_s': f"{tts_duration:.2f}",
                    'avatar_compose_s': f"{mouth_composition_duration:.2f}",
                    'pipeline_s': f"{pipeline_duration:.2f}"
                }
            }), 500
        
        print(f" Pipeline completed successfully (took {pipeline_duration:.2f}s)")
        set_progress(100, "Complete")

        # Check video
        video_path = job_output_dir / "message1_lipsync.mp4"
        if not video_path.exists():
            print(f" Video not found (total {total_duration:.2f}s)")
            return jsonify({
                'error': 'Video generation failed',
                'details': 'Output video not found',
                'timing': {
                    'total_duration_s': f"{total_duration:.2f}",
                    'tts_s': f"{tts_duration:.2f}",
                    'avatar_compose_s': f"{mouth_composition_duration:.2f}",
                    'pipeline_s': f"{pipeline_duration:.2f}"
                }
            }), 500
        
        print(f"Video generated (Total duration: {total_duration:.2f}s)")
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'emotion': predicted_emotion,
            'text': text,
            'tts_engine': 'edge',
            'emotion_voice_used': use_emotion_voice and TTS_AVAILABLE.get('edge'),
            'video_url': f'/api/video/{job_id}',
            'avatar_config': avatar_config,
            'timing': {
                'total_duration_s': f"{total_duration:.2f}",
                'tts_s': f"{tts_duration:.2f}",
                'avatar_compose_s': f"{mouth_composition_duration:.2f}",
                'pipeline_s': f"{pipeline_duration:.2f}"
            }
        })
        
    except subprocess.TimeoutExpired:
        timeout_duration = time.time() - start_total if 'start_total' in locals() else -1
        print(f"Processing timeout (lasted {timeout_duration:.2f}s)")
        return jsonify({'error': 'Processing timeout (>5 minutes)'}), 504
    
    except Exception as e:
        error_duration = time.time() - start_total if 'start_total' in locals() else -1
        print(f" Error (lasted {error_duration:.2f}s): {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/process-audio', methods=['POST'])
def process_audio():
    """
    Process audio → detect emotion → generate lipsync video
    """
    set_progress(0, "Starting...")

    start_total = time.time()
    try:
        # Check if using sample audio or uploaded file
        using_sample = 'sample_audio' in request.form

        if using_sample:
            # Handle sample audio
            sample_filename = request.form.get('sample_audio')
            if not sample_filename:
                return jsonify({'error': 'No sample audio specified'}), 400
            
            # Path to sample audio files
            SAMPLES_FOLDER = BASE_DIR / "samples"
            sample_path = SAMPLES_FOLDER / sample_filename
            
            if not sample_path.exists():
                return jsonify({'error': f'Sample audio not found: {sample_filename}'}), 404
            
            print(f"Using sample audio: {sample_filename}")
            
            # Generate unique job ID and copy sample to temp location
            job_id = str(uuid.uuid4())[:8]
            audio_path = UPLOAD_FOLDER / f"{job_id}_input.{sample_path.suffix[1:]}"
            shutil.copy(sample_path, audio_path)
            
        else:
            # Handle uploaded audio file
            if 'audio' not in request.files:
                set_progress(10, "Extracting audio")
                return jsonify({'error': 'No audio file provided'}), 400
            
            audio_file = request.files['audio']
            if audio_file.filename == '':
                return jsonify({'error': 'Empty filename'}), 400
            
            # Generate unique job ID
            job_id = str(uuid.uuid4())[:8]
            print(f"New job: {job_id}")

            # Save uploaded audio
            audio_ext = 'webm' if audio_file.filename.endswith('.webm') else 'wav'
            audio_path = UPLOAD_FOLDER / f"{job_id}_input.{audio_ext}"
            audio_file.save(audio_path)
            print(f"Audio saved: {audio_path}")
        
        
        # Get avatar configuration from form data
        avatar_config = {
            'gender': request.form.get('gender', 'female'),
            'hair_style': request.form.get('hair_style', 'wavy'),
            'hair_color': request.form.get('hair_color', 'brown'),
            'eye_color': request.form.get('eye_color', 'brown'),
            'background_color': request.form.get('background_color', 'pink')
        }

        print(f"\nAvatar config: {avatar_config}")
        

        # STEP 1: Quick transcription to detect emotion
        print(f" Transcribing audio for emotion detection...")
        try:
            import whisper
            set_progress(25, "Running Whisper")
            model = whisper.load_model("tiny")
            result = model.transcribe(str(audio_path))
            transcript = result.get("text", "")
            print(f" Transcript: {transcript[:100]}...")
            detected_language = detect_language(transcript)
            from text_to_avatar import classify_emotion
            set_progress(40, "Classifying emotion")
            predicted_emotion = classify_emotion(transcript, language=detected_language)
            print(f" Predicted emotion: {predicted_emotion}")
        except Exception as e:
            print(f" Emotion detection failed: {e}, using neutral")
            predicted_emotion = "neutral"
        

        # Create job output directory
        job_output_dir = OUTPUT_FOLDER / job_id
        job_output_dir.mkdir(exist_ok=True)

        # STEP 2: Compose avatar ONLY for predicted emotion
        mouth_composition_duration = 0
        if HAS_AVATAR_COMPOSER:
            set_progress(70, "Rendering frames")
            custom_mouthsets = job_output_dir / "custom_avatar"
            print(f"🎨 Composing avatar for emotion: {predicted_emotion}")
            start_compose = time.time()
            try:
                avatar_composer.compose_single_emotion(
                    avatar_config,
                    custom_mouthsets,
                    emotion=predicted_emotion
                )
                mouth_composition_duration = time.time() - start_compose
                print(f" Custom avatar composed ({predicted_emotion}) in {mouth_composition_duration:.2f}s")
                mouth_dir = custom_mouthsets / predicted_emotion
            except Exception as e:
                print(f" Avatar composition failed: {e}, using default")
                mouth_dir = MOUTH_ROOT / predicted_emotion
        else:
            mouth_dir = MOUTH_ROOT / predicted_emotion

        # STEP 3: Run lipsync
        
        cmd = [
            sys.executable, str(LIPSYNC_SCRIPT),
            "--audio", str(audio_path),
            "--mouths", str(mouth_dir),
            "--out_dir", str(job_output_dir),
            "--fps", "20",
            "--whisper_model", "base",
            "--lipsync_offset", "-0.10",
            "--target_height", "720"
        ]

        print(f" Running pipeline...")
        start_pipeline = time.time()
        set_progress(90, "Encoding video")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=Path(__file__).parent
        )
        
        pipeline_duration = time.time() - start_pipeline
        total_duration = time.time() - start_total
        
        if result.returncode != 0:
            print(f" Pipeline failed (took {pipeline_duration:.2f}s, total {total_duration:.2f}s):")
            print(result.stderr)
            return jsonify({
                'error': 'Processing failed',
                'details': result.stderr[-500:],
                'timing': {
                    'total_duration_s': f"{total_duration:.2f}",
                    'avatar_compose_s': f"{mouth_composition_duration:.2f}",
                    'pipeline_s': f"{pipeline_duration:.2f}"
                }
            }), 500
        
        print(f" Pipeline completed successfully (took {pipeline_duration:.2f}s)")
        
        # Check if video was generated
        video_path = job_output_dir / "message1_lipsync.mp4"
        if not video_path.exists():
            print(f" Video not found (total {total_duration:.2f}s)")
            return jsonify({
                'error': 'Video generation failed',
                'details': 'Output video not found',
                'timing': {
                    'total_duration_s': f"{total_duration:.2f}",
                    'avatar_compose_s': f"{mouth_composition_duration:.2f}",
                    'pipeline_s': f"{pipeline_duration:.2f}"
                }
            }), 500
        
        set_progress(100, "Complete")
        print(f"🎬 Video generated (Total duration: {total_duration:.2f}s)")
        
        # Clean up input audio
        try:
            audio_path.unlink()
        except:
            pass
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'emotion': predicted_emotion,
            'transcription': transcript if 'transcript' in locals() else 'Audio processed successfully',
            'video_url': f'/api/video/{job_id}',
            'avatar_config': avatar_config,
            'using_sample': using_sample,
            'timing': {
                'total_duration_s': f"{total_duration:.2f}",
                'avatar_compose_s': f"{mouth_composition_duration:.2f}",
                'pipeline_s': f"{pipeline_duration:.2f}"
            }
        })
        
    except subprocess.TimeoutExpired:
        timeout_duration = time.time() - start_total if 'start_total' in locals() else -1
        print(f"⏱️ Processing timeout (lasted {timeout_duration:.2f}s)")
        return jsonify({'error': 'Processing timeout (>5 minutes)'}), 504
    
    except Exception as e:
        error_duration = time.time() - start_total if 'start_total' in locals() else -1
        print(f" Error (lasted {error_duration:.2f}s): {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/')
def serve_frontend():
    """Serve the frontend HTML"""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'tts_available': TTS_AVAILABLE,
        'avatar_composer_available': HAS_AVATAR_COMPOSER,
        'language_detection_available': HAVE_LANGDETECT, 
        'emotion_models': {  
            'en': 'esracesur/roberta_weighted',
            'tr': 'esracesur/roberta_turkish_emotion_recognition'
        },
        'features': {
            'language_detection': HAVE_LANGDETECT  
        }
    })

@app.route('/samples/<filename>')
def serve_sample_audio(filename):
    """Serve sample audio files for preview"""
    try:
        SAMPLES_FOLDER = BASE_DIR / "samples"
        sample_path = SAMPLES_FOLDER / filename
        
        if not sample_path.exists():
            return jsonify({'error': 'Sample not found'}), 404
        
        return send_file(sample_path, mimetype='audio/mpeg')
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/assets/avatar/<path:filepath>')
def serve_avatar_assets(filepath):
    """Serve avatar image assets for preview"""
    try:
        avatar_file = AVATAR_ROOT / filepath
        if avatar_file.exists():
            return send_file(avatar_file)
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/video/<job_id>', methods=['GET'])
def get_video(job_id):
    """Serve the generated lipsync video"""
    video_path = OUTPUT_FOLDER / job_id / "message1_lipsync.mp4"
    
    if not video_path.exists():
        return jsonify({'error': 'Video not found'}), 404
    
    return send_file(
        video_path,
        mimetype='video/mp4',
        as_attachment=False,
        download_name=f'lipsync_{job_id}.mp4'
    )


@app.route('/api/timeline/<job_id>', methods=['GET'])
def get_timeline(job_id):
    """Get the lipsync timeline JSON"""
    timeline_path = OUTPUT_FOLDER / job_id / "lipsync_timeline.json"
    
    if not timeline_path.exists():
        return jsonify({'error': 'Timeline not found'}), 404
    
    with open(timeline_path, 'r') as f:
        timeline = json.load(f)
    
    return jsonify(timeline)


@app.route('/api/cleanup/<job_id>', methods=['DELETE'])
def cleanup_job(job_id):
    """Clean up files for a specific job"""
    try:
        job_dir = OUTPUT_FOLDER / job_id
        if job_dir.exists():
            shutil.rmtree(job_dir)
        
        for audio_file in UPLOAD_FOLDER.glob(f"{job_id}_*"):
            audio_file.unlink()
        
        return jsonify({'success': True, 'message': f'Job {job_id} cleaned up'})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("\n Starting Flask server...")
    print(" Open http://localhost:5000 in your browser")
    print("\n Features:")
    print("    Audio upload → lipsync")
    print("    Text input → Emotion-Based TTS → lipsync")
    print("    Emotion detection")
    if TTS_AVAILABLE.get('edge'):
        print("    Emotion-based voice selection (Edge-TTS)")
    if HAS_AVATAR_COMPOSER:
        print("    Avatar customization")
    else:
        print("    Avatar customization disabled")
    print("\n Ctrl+C to stop\n")
    
    UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)
    app.config["OUTPUT_FOLDER"] = str(OUTPUT_FOLDER)

    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 7860)))