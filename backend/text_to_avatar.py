#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Text-to-Avatar Pipeline with Emotion-Based TTS
Takes text input → detects emotion → generates speech with emotion-appropriate voice → creates lipsync video
"""

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Optional
import tempfile
import shutil
import logging, sys
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


try:
    from langdetect import detect
    HAVE_LANGDETECT = True
except ImportError:
    HAVE_LANGDETECT = False

def detect_language(text: str) -> str:
    """Detect language from text, return 'en' or 'tr'"""
    if not HAVE_LANGDETECT:
        return "en"
    try:
        lang = detect(text)
        return "tr" if lang == "tr" else "en"
    except:
        return "en"
    
# TTS imports with fallback handling
TTS_AVAILABLE = {}
try:
    import edge_tts
    import asyncio
    TTS_AVAILABLE['edge'] = True
except ImportError:
    TTS_AVAILABLE['edge'] = False

try:
    import pyttsx3
    TTS_AVAILABLE['pyttsx3'] = True
except ImportError:
    TTS_AVAILABLE['pyttsx3'] = False

try:
    from gtts import gTTS
    TTS_AVAILABLE['gtts'] = True
except ImportError:
    TTS_AVAILABLE['gtts'] = False

# Emotion detection
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    HAVE_TRANSFORMERS = True
except ImportError:
    HAVE_TRANSFORMERS = False

EMOTION_LABELS = ["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"]

# ===== EMOTION-TO-VOICE MAPPING =====
EMOTION_VOICE_MAP = {
    # English voices
    "en": {
        "anger": {
            "voice": "en-US-GuyNeural",
            "rate": "+10%",
            "pitch": "+5Hz",
            "style": "angry"
        },
        "joy": {
            "voice": "en-US-AriaNeural",
            "rate": "+5%",
            "pitch": "+10Hz",
            "style": "cheerful"
        },
        "sadness": {
            "voice": "en-US-JennyNeural",
            "rate": "-10%",
            "pitch": "-5Hz",
            "style": "sad"
        },
        "fear": {
            "voice": "en-US-JennyNeural",
            "rate": "+15%",
            "pitch": "+8Hz",
            "style": "terrified"
        },
        "surprise": {
            "voice": "en-US-AriaNeural",
            "rate": "+8%",
            "pitch": "+12Hz",
            "style": "excited"
        },
        "disgust": {
            "voice": "en-GB-RyanNeural",
            "rate": "-5%",
            "pitch": "-3Hz",
            "style": "angry"
        },
        "neutral": {
            "voice": "en-US-AriaNeural",
            "rate": "+0%",
            "pitch": "+0Hz",
            "style": "neutral"
        }
    },
    # Turkish voices
    "tr": {
        "anger": {
            "voice": "tr-TR-AhmetNeural",
            "rate": "+10%",
            "pitch": "+5Hz",
            "style": "angry"
        },
        "joy": {
            "voice": "tr-TR-EmelNeural",
            "rate": "+5%",
            "pitch": "+10Hz",
            "style": "cheerful"
        },
        "sadness": {
            "voice": "tr-TR-EmelNeural",
            "rate": "-10%",
            "pitch": "-5Hz",
            "style": "sad"
        },
        "fear": {
            "voice": "tr-TR-EmelNeural",
            "rate": "+15%",
            "pitch": "+8Hz",
            "style": "terrified"
        },
        "surprise": {
            "voice": "tr-TR-EmelNeural",
            "rate": "+8%",
            "pitch": "+12Hz",
            "style": "excited"
        },
        "disgust": {
            "voice": "tr-TR-AhmetNeural",
            "rate": "-5%",
            "pitch": "-3Hz",
            "style": "angry"
        },
        "neutral": {
            "voice": "tr-TR-EmelNeural",
            "rate": "+0%",
            "pitch": "+0Hz",
            "style": "neutral"
        }
    }
}

EMO_MODELS = {}  # Model cache

def load_emotion_model(model_name: str):
    """Load emotion classification model with proper caching"""
    global EMO_MODELS
    
    # Check if already loaded
    if model_name in EMO_MODELS:
        return EMO_MODELS[model_name]
    
    if not HAVE_TRANSFORMERS:
        raise RuntimeError("transformers not installed; pip install transformers torch")
    
    print(f"Loading emotion model: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    model.eval()
    
    # Cache it
    EMO_MODELS[model_name] = (tokenizer, model)
    
    return tokenizer, model

# Normalize emotion labels
_CANON = {
    "angry": "anger", "anger": "anger",
    "disgust": "disgust", "disgusted": "disgust",
    "fear": "fear", "fearful": "fear",
    "joy": "joy", "happy": "joy", "happiness": "joy",
    "neutral": "neutral",
    "sad": "sadness", "sadness": "sadness",
    "surprised": "surprise", "surprise": "surprise",
}

def classify_emotion(text: str, model_name: str = None, language: str = None) -> str:
    """Classify emotion from text"""
    if not text.strip():
        return "neutral"
    
    
    if language is None:
        language = detect_language(text)
    
    # Select model based on language
    if model_name is None:
        model_name = (
            "esracesur/roberta_turkish_emotion_recognition" if language == "tr" 
            else "esracesur/roberta_weighted"
        )
    
    print(f"Using emotion model: {model_name} (language: {language})")

    try:
        tok, mdl = load_emotion_model(model_name)
        toks = tok(text, truncation=True, max_length=256, return_tensors="pt")
        with torch.no_grad():
            logits = mdl(**toks).logits[0]
        pred_idx = int(torch.argmax(logits).item())
        id2label = getattr(mdl.config, "id2label", None) or {}
        raw = str(id2label.get(pred_idx, "neutral")).lower()
        emotion = _CANON.get(raw, raw if raw in EMOTION_LABELS else "neutral")
        confidence = torch.softmax(logits, dim=0)[pred_idx]
        print(f"Detected emotion: {emotion} (confidence: {confidence:.2f})")
        return emotion
    except Exception as e:
        print(f"Emotion classification failed: {e}, defaulting to neutral")
        return "neutral"


def get_emotion_voice_config(emotion: str, language: str = "en", gender: str = "female") -> dict:
    lang_key = "tr" if language.startswith("tr") else "en"
    
    # Get emotion config or fall back to neutral
    emotion_config = EMOTION_VOICE_MAP[lang_key].get(
        emotion, 
        EMOTION_VOICE_MAP[lang_key]["neutral"]
    ).copy()  # IMPORTANT: Make a copy to avoid modifying the original

    # Override voice based on gender
    if lang_key == "tr":
        if gender == "male":
            emotion_config["voice"] = "tr-TR-AhmetNeural"
        else:
            emotion_config["voice"] = "tr-TR-EmelNeural"
    elif lang_key == "en":
        if gender == "male":
            emotion_config["voice"] = "en-US-GuyNeural"
        else:
            emotion_config["voice"] = "en-US-AriaNeural"
    
    return emotion_config

    # Override voice based on gender
    if lang_key == "tr":
        if gender == "male":
            emotion_config["voice"] = "tr-TR-AhmetNeural"
        else:
            emotion_config["voice"] = "tr-TR-EmelNeural"
    elif lang_key == "en":
        if gender == "male":
            emotion_config["voice"] = "en-US-GuyNeural"
        else:
            emotion_config["voice"] = "en-US-AriaNeural"
    return emotion_config


async def generate_speech_edge_emotion_async(
    text: str, 
    output_path: Path, 
    emotion: str = "neutral",
    language: str = "en",
    gender: str = "female"
) -> None:
    """Generate speech using Edge TTS with emotion-appropriate voice"""
    
    # Get voice configuration for the emotion
    voice_config = get_emotion_voice_config(emotion, language, gender)
    
    voice = voice_config["voice"]
    rate = voice_config["rate"]
    pitch = voice_config["pitch"]
    
    # Create communicate object with emotion parameters
    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate,
        pitch=pitch
    )
    
    await communicate.save(str(output_path))
    print(f" Emotional speech saved: {output_path}")





def generate_speech_edge_emotion(
    text: str, 
    output_path: Path, 
    emotion: str = "neutral",
    language: str = "en",
    gender: str = "female"
) -> None:
    """Wrapper for async Edge TTS with emotion"""
    asyncio.run(generate_speech_edge_emotion_async(text, output_path, emotion, language, gender))

async def generate_speech_edge_async(text: str, output_path: Path, voice: str = "en-US-AriaNeural") -> None:
    """Generate speech using Edge TTS (requires internet, high quality)"""
    print(f"Generating speech with Edge-TTS (voice={voice})...")
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))
    print(f" Audio saved: {output_path}")

def generate_speech_edge(text: str, output_path: Path, voice: str = "en-US-AriaNeural") -> None:
    """Wrapper for async Edge TTS"""
    asyncio.run(generate_speech_edge_async(text, output_path, voice))


def generate_speech_pyttsx3(text: str, output_path: Path, rate: int = 150, gender: str = "female") -> None:
    """Generate speech using pyttsx3 (offline, works everywhere)"""
    print(f" Using offline TTS (pyttsx3)...")
    
    try:
        engine = pyttsx3.init()
        
        # Set properties
        engine.setProperty('rate', rate)
        
        # Try to select voice based on gender
        voices = engine.getProperty('voices')
        if voices:
            # Try to find a voice matching the gender
            target_voice = None
            gender_lower = gender.lower()
            
            for voice in voices:
                voice_name = voice.name.lower()
                # Simple heuristic: look for male/female indicators
                if gender_lower == "female" and any(x in voice_name for x in ["female", "woman", "zira", "hazel"]):
                    target_voice = voice.id
                    break
                elif gender_lower == "male" and any(x in voice_name for x in ["male", "man", "david", "mark"]):
                    target_voice = voice.id
                    break
            
            # If found a matching voice, use it; otherwise use first available
            if target_voice:
                engine.setProperty('voice', target_voice)
            elif voices:
                engine.setProperty('voice', voices[0].id)
        
        engine.save_to_file(text, str(output_path))
        engine.runAndWait()
        print(f" Offline audio saved: {output_path}")
        
    except Exception as e:
        print(f" pyttsx3 failed: {e}")
        raise


def generate_speech_gtts(text: str, output_path: Path, lang: str = 'en', gender: str = 'female') -> None:
    """Generate speech using Google TTS (requires internet, simple)"""
    print(f"Using Google TTS (lang={lang}, gender={gender})...")
    
    try:
        # Map language codes
        if lang.startswith('tr'):
            tld = 'com.tr'  # Turkish domain for more natural Turkish voice
            lang_code = 'tr'
        else:
            # For English, use different domains for slight voice variation
            if gender == 'male':
                tld = 'co.uk'  # UK English tends to sound slightly different
            else:
                tld = 'com'  # US English
            lang_code = 'en'
        
        tts = gTTS(text=text, lang=lang_code, tld=tld, slow=False)
        tts.save(str(output_path))
        print(f"✓ Google TTS audio saved: {output_path}")
        print(f"⚠️ Note: Google TTS has limited voice variety. Gender selection may not be noticeable.")
        
    except Exception as e:
        print(f"❌ Google TTS failed: {e}")
        raise

def generate_speech(
    text: str, 
    output_path: Path, 
    engine: str = "auto",
    emotion: Optional[str] = None,
    **kwargs
) -> None:
    """
    Generate speech from text using specified TTS engine with automatic fallback
    
    Args:
        text: Input text to synthesize
        output_path: Where to save audio file
        engine: TTS engine ('auto', 'edge', 'gtts', 'pyttsx3')
        emotion: Emotion for voice selection (only for Edge-TTS)
        **kwargs: Engine-specific parameters
    """
    # Auto-select best available engine
    if engine == "auto":
        if TTS_AVAILABLE.get('edge'):
            engine = 'edge'
        elif TTS_AVAILABLE.get('gtts'):
            engine = 'gtts'
        elif TTS_AVAILABLE.get('pyttsx3'):
            engine = 'pyttsx3'
        else:
            raise RuntimeError("No TTS engine available. Install: pip install gtts pyttsx3 edge-tts")
    
    # Try primary engine with fallback
    engines_to_try = [engine]
    
    # Add fallback engines if primary fails
    if engine == 'edge':
        if TTS_AVAILABLE.get('gtts'):
            engines_to_try.append('gtts')
        if TTS_AVAILABLE.get('pyttsx3'):
            engines_to_try.append('pyttsx3')
    
    last_error = None
    
    for try_engine in engines_to_try:
        try:
            if try_engine == 'edge':
                if not TTS_AVAILABLE.get('edge'):
                    continue
                
                # Use emotion-based voice if emotion is provided
                if emotion and emotion != "neutral":
                    language = kwargs.get('lang', 'en')
                    gender = kwargs.get('gender', 'female')
                    generate_speech_edge_emotion(text, output_path, emotion, language, gender)
                else:
                    voice = kwargs.get('voice', 'en-US-AriaNeural')
                    generate_speech_edge(text, output_path, voice)
                
                return  # Success!
                
            elif try_engine == 'gtts':
                if not TTS_AVAILABLE.get('gtts'):
                    continue
                    
                lang = kwargs.get('lang', 'en')
                gender = kwargs.get('gender', 'female')
                # Map language codes
                if lang.startswith('tr'):
                    lang = 'tr'
                elif lang.startswith('en'):
                    lang = 'en'
                    
                generate_speech_gtts(text, output_path, lang, gender)
                return  # Success!
                
            elif try_engine == 'pyttsx3':
                if not TTS_AVAILABLE.get('pyttsx3'):
                    continue
                    
                rate = kwargs.get('rate', 150)
                gender = kwargs.get('gender', 'female')
                lang = kwargs.get('lang', 'en')
                generate_speech_pyttsx3(text, output_path, rate, gender, lang)
                return  # Success!
                
        except Exception as e:
            last_error = e
            error_msg = str(e)
            
            # Check if it's a network error
            if "Network is unreachable" in error_msg or "Cannot connect" in error_msg:
                print(f"⚠️ {try_engine} failed (network error), trying fallback...")
            else:
                print(f"⚠️ {try_engine} failed: {e}, trying fallback...")
            
            continue
    
    # If all engines failed
    if last_error:
        raise RuntimeError(f"All TTS engines failed. Last error: {last_error}")
    else:
        raise RuntimeError("No TTS engine available")
    

def run_lipsync_pipeline(
    audio_path: Path,
    mouths_dir: Path,
    output_dir: Path,
    lipsync_script: Path,
    emotion: str = "auto",
    emotion_model: str = "esracesur/roberta_weighted",
    fps: int = 20,
    lipsync_offset: float = -0.10,
    whisper_model: str = "tiny",
    emotions_root: Optional[Path] = None,
    target_height: int = 720
) -> dict:
    """Run the lipsync pipeline"""
    print("Running lipsync pipeline...")
    
    cmd = [
        sys.executable, str(lipsync_script),
        "--audio", str(audio_path),
        "--mouths", str(mouths_dir),
        "--out_dir", str(output_dir),
        "--fps", str(fps),
        "--whisper_model", whisper_model,
        "--lipsync_offset", str(lipsync_offset),
        "--target_height", str(target_height)
    ]
    
    # Add emotion parameters if provided
    if emotions_root:
        cmd.extend([
            "--emotions_root", str(emotions_root),
            "--emotion", emotion,
            "--emotion_model", emotion_model
        ])
    
    # Run pipeline
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f" Pipeline failed:")
        print(result.stderr)
        return {
            'success': False,
            'error': result.stderr,
            'video_path': None,
            'emotion': None,
            'output_dir': output_dir
        }
    
    print(result.stdout)
    
    # Extract detected emotion from output
    detected_emotion = emotion if emotion != "auto" else "neutral"
    for line in result.stdout.split('\n'):
        if "Emotion chosen:" in line:
            try:
                detected_emotion = line.split("Emotion chosen:")[1].strip().split()[0].lower()
            except:
                pass
            break
    
    # Check for output video
    video_path = output_dir / "message1_lipsync.mp4"
    if not video_path.exists():
        return {
            'success': False,
            'error': 'Output video not found',
            'video_path': None,
            'emotion': detected_emotion,
            'output_dir': output_dir
        }
    
    print(f"\n Pipeline completed successfully!")
    print(f"  Emotion: {detected_emotion}")
    print(f"  Video: {video_path}")
    
    return {
        'success': True,
        'video_path': video_path,
        'emotion': detected_emotion,
        'output_dir': output_dir
    }


def main():
    ap = argparse.ArgumentParser(
        description="Text-to-Avatar Pipeline with Emotion-Based TTS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Auto emotion detection with emotion-based voice
  python text_to_avatar.py --text "I'm so happy today!" --mouths assets/mouthsets/neutral
  
  # Use emotion-based mouthsets with auto voice
  python text_to_avatar.py --text "This is terrible!" --emotions_root assets/mouthsets
  
  # Manual emotion selection
  python text_to_avatar.py --text "Hello" --emotion joy --emotions_root assets/mouthsets
  
  # Turkish with emotion
  python text_to_avatar.py --text "Çok mutluyum!" --lang tr --emotions_root assets/mouthsets
        """
    )
    
    # Input
    input_group = ap.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--text", help="Input text to synthesize")
    input_group.add_argument("--text_file", type=Path, help="Read text from file")
    
    # TTS settings
    ap.add_argument("--tts", default="auto", 
                    choices=["auto", "edge"],
                    help="TTS engine (default: auto-detect, prefers edge for emotion)")
    ap.add_argument("--lang", default="auto",  # Change from "en" to "auto"
                help="Language code (en/tr/auto) for voice selection (default: auto-detect)")
    ap.add_argument("--voice", default=None,
                    help="Manual voice override (disables emotion-based selection)")
    # Lipsync settings
    ap.add_argument("--mouths", type=Path, required=True,
                    help="Folder containing mouth images (REST.png, AA.png, etc.)")
    ap.add_argument("--emotions_root", type=Path,
                    help="Root folder with emotion subfolders (anger, joy, etc.)")
    ap.add_argument("--emotion", default="auto",
                    choices=["auto"] + EMOTION_LABELS,
                    help="Emotion to use (default: auto-detect from text)")
    ap.add_argument("--emotion_model", default="esracesur/roberta_weighted",
                    help="Hugging Face emotion model")
    # Output settings
    ap.add_argument("--out_dir", type=Path, default=Path("output_tts"),
                    help="Output directory (default: output_tts)")
    ap.add_argument("--keep_audio", action="store_true",
                    help="Keep generated audio file")
    
    # Pipeline settings
    ap.add_argument("--fps", type=int, default=20, help="Video FPS")
    ap.add_argument("--lipsync_offset", type=float, default=-0.10,
                    help="Lipsync timing offset in seconds")
    ap.add_argument("--whisper_model", default="tiny",
                    choices=["tiny", "base", "small", "medium", "large"],
                    help="Whisper model size")
    ap.add_argument("--lipsync_script", type=Path, default=Path("lipsync.py"),
                    help="Path to lipsync.py script")
    ap.add_argument("--target_height", type=int, default=720,
                help="Target video height (480, 720, 1080)")
    
    args = ap.parse_args()
    
    # Print available TTS engines
    print("Available TTS engines:")
    for engine, available in TTS_AVAILABLE.items():
        status = " OK" if available else " NOT AVAILABLE"
        print(f"  {status} {engine}")
    
    # Get input text
    if args.text:
        text = args.text
    else:
        text = args.text_file.read_text(encoding='utf-8').strip()
    
    if not text:
        print("Error: Empty text input")
        sys.exit(1)

    detected_language = detect_language(text)
    if not args.lang or args.lang == "auto":
        args.lang = detected_language
    print(f"Detected language: {detected_language}")

    print(f"Input text ({len(text)} chars):")
    print(f"  {text[:100]}{'...' if len(text) > 100 else ''}\n")
    
    # Detect emotion from text (if auto)
    detected_emotion = args.emotion
    if args.emotion == "auto" and HAVE_TRANSFORMERS:
        print(" Detecting emotion from text...")
        detected_emotion = classify_emotion(text, language=detected_language)
        print(f"→ Using emotion: {detected_emotion}\n")
    elif args.emotion == "auto":
        print(" Transformers not available, defaulting to neutral emotion\n")
        detected_emotion = "neutral"
    
    # Create output directory
    args.out_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate speech with emotion-based voice
    audio_path = args.out_dir / "generated_speech.wav"
    try:
        print(f" Generating speech with emotion: {detected_emotion}")
        
        # Use emotion-based voice selection for Edge-TTS
        if args.tts in ["auto", "edge"] and TTS_AVAILABLE.get('edge'):
            generate_speech(
                text=text,
                output_path=audio_path,
                engine='edge',
                emotion=detected_emotion,
                lang=args.lang
            )

    except Exception as e:
        print(f" TTS generation failed: {e}")
        sys.exit(1)
    
    # Run lipsync pipeline
    result = run_lipsync_pipeline(
        audio_path=audio_path,
        mouths_dir=args.mouths,
        output_dir=args.out_dir,
        lipsync_script=args.lipsync_script,
        emotion=detected_emotion,
        emotion_model=args.emotion_model,
        fps=args.fps,
        lipsync_offset=args.lipsync_offset,
        whisper_model=args.whisper_model,
        emotions_root=args.emotions_root,
        target_height=args.target_height
    )
    
    # Cleanup
    if not args.keep_audio and audio_path.exists():
        audio_path.unlink()
    
    # Final report
    if result['success']:
        print(" VIDEO CREATION SUCCESS!")
        print(f"  Video: {result['video_path']}")
        print(f"  Emotion: {result['emotion']}")
        print(f"  Output: {result['output_dir']}")
    else:
        print(" FAILED")
        print(f"  Error: {result.get('error', 'Unknown error')}")
        sys.exit(1)
    print("="*60)

if __name__ == "__main__":
    main()