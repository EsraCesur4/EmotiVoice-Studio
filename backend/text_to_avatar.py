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

# TTS imports with fallback handling
TTS_AVAILABLE = {}

try:
    from gtts import gTTS
    TTS_AVAILABLE['gtts'] = True
except ImportError:
    TTS_AVAILABLE['gtts'] = False

try:
    import pyttsx3
    TTS_AVAILABLE['pyttsx3'] = True
except ImportError:
    TTS_AVAILABLE['pyttsx3'] = False

try:
    import edge_tts
    import asyncio
    TTS_AVAILABLE['edge'] = True
except ImportError:
    TTS_AVAILABLE['edge'] = False

# Emotion detection
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    HAVE_TRANSFORMERS = True
except ImportError:
    HAVE_TRANSFORMERS = False

EMOTION_LABELS = ["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"]

# ===== NEW: EMOTION-TO-VOICE MAPPING =====
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

# Emotion model cache
EMO_TOKENIZER = None
EMO_MODEL = None

def load_emotion_model(model_name: str):
    """Load emotion classification model"""
    global EMO_TOKENIZER, EMO_MODEL
    if EMO_TOKENIZER is None or EMO_MODEL is None:
        if not HAVE_TRANSFORMERS:
            raise RuntimeError("transformers not installed; pip install transformers torch")
        print(f"Loading emotion model: {model_name}")
        EMO_TOKENIZER = AutoTokenizer.from_pretrained(model_name)
        EMO_MODEL = AutoModelForSequenceClassification.from_pretrained(model_name)
        EMO_MODEL.eval()
    return EMO_TOKENIZER, EMO_MODEL

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

def classify_emotion(text: str, model_name: str) -> str:
    """Classify emotion from text"""
    if not text.strip():
        return "neutral"
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


def get_emotion_voice_config(emotion: str, language: str = "en") -> dict:
    """
    Get voice configuration for a specific emotion and language
    
    Args:
        emotion: Detected emotion (anger, joy, sadness, etc.)
        language: Language code ('en' or 'tr')
    
    Returns:
        Dictionary with voice, rate, pitch, and style settings
    """
    lang_key = "tr" if language.startswith("tr") else "en"
    
    # Get emotion config or fall back to neutral
    emotion_config = EMOTION_VOICE_MAP[lang_key].get(
        emotion, 
        EMOTION_VOICE_MAP[lang_key]["neutral"]
    )
    
    print(f"Voice config for {emotion} ({lang_key}):")
    print(f"   Voice: {emotion_config['voice']}")
    print(f"   Rate: {emotion_config['rate']}")
    print(f"   Pitch: {emotion_config['pitch']}")
    print(f"   Style: {emotion_config['style']}")
    
    return emotion_config


async def generate_speech_edge_emotion_async(
    text: str, 
    output_path: Path, 
    emotion: str = "neutral",
    language: str = "en"
) -> None:
    """Generate speech using Edge TTS with emotion-appropriate voice"""
    
    # Get voice configuration for this emotion
    voice_config = get_emotion_voice_config(emotion, language)
    
    voice = voice_config["voice"]
    rate = voice_config["rate"]
    pitch = voice_config["pitch"]
    
    print(f"Generating speech with Edge-TTS...")
    print(f"  Emotion: {emotion}")
    print(f"  Voice: {voice}")
    print(f"  Rate: {rate}, Pitch: {pitch}")
    
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
    language: str = "en"
) -> None:
    """Wrapper for async Edge TTS with emotion"""
    asyncio.run(generate_speech_edge_emotion_async(text, output_path, emotion, language))


# Legacy TTS functions (unchanged)
def generate_speech_gtts(text: str, output_path: Path, lang: str = "en") -> None:
    """Generate speech using Google TTS (requires internet)"""
    print(f"Generating speech with gTTS (lang={lang})...")
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(str(output_path))
    print(f" Audio saved: {output_path}")


def generate_speech_pyttsx3(text: str, output_path: Path, rate: int = 150) -> None:
    """Generate speech using pyttsx3 (offline)"""
    print(f"Generating speech with pyttsx3 (rate={rate})...")
    engine = pyttsx3.init()
    engine.setProperty('rate', rate)
    engine.save_to_file(text, str(output_path))
    engine.runAndWait()
    print(f" Audio saved: {output_path}")


async def generate_speech_edge_async(text: str, output_path: Path, voice: str = "en-US-AriaNeural") -> None:
    """Generate speech using Edge TTS (requires internet, high quality)"""
    print(f"Generating speech with Edge-TTS (voice={voice})...")
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))
    print(f" Audio saved: {output_path}")


def generate_speech_edge(text: str, output_path: Path, voice: str = "en-US-AriaNeural") -> None:
    """Wrapper for async Edge TTS"""
    asyncio.run(generate_speech_edge_async(text, output_path, voice))


def generate_speech(
    text: str, 
    output_path: Path, 
    engine: str = "auto",
    emotion: Optional[str] = None,
    **kwargs
) -> None:
    """
    Generate speech from text using specified TTS engine
    
    Args:
        text: Input text to synthesize
        output_path: Where to save audio file
        engine: TTS engine ('auto', 'gtts', 'pyttsx3', 'edge')
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
    
    # Generate speech with selected engine
    if engine == 'gtts':
        if not TTS_AVAILABLE.get('gtts'):
            raise RuntimeError("gTTS not available. Install: pip install gtts")
        lang = kwargs.get('lang', 'en')
        generate_speech_gtts(text, output_path, lang)
    
    elif engine == 'pyttsx3':
        if not TTS_AVAILABLE.get('pyttsx3'):
            raise RuntimeError("pyttsx3 not available. Install: pip install pyttsx3")
        rate = kwargs.get('rate', 150)
        generate_speech_pyttsx3(text, output_path, rate)
    
    elif engine == 'edge':
        if not TTS_AVAILABLE.get('edge'):
            raise RuntimeError("edge-tts not available. Install: pip install edge-tts")
        
        # NEW: Use emotion-based voice if emotion is provided
        if emotion and emotion != "neutral":
            language = kwargs.get('lang', 'en')
            generate_speech_edge_emotion(text, output_path, emotion, language)
        else:
            # Legacy: use manual voice selection
            voice = kwargs.get('voice', 'en-US-AriaNeural')
            generate_speech_edge(text, output_path, voice)
    
    else:
        raise ValueError(f"Unknown TTS engine: {engine}. Use 'gtts', 'pyttsx3', 'edge', or 'auto'")


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
    print(f"\n{'='*60}")
    print("Running lipsync pipeline...")
    print(f"{'='*60}")
    
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
    
    print(f"Command: {' '.join(cmd)}")
    
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
                    choices=["auto", "gtts", "pyttsx3", "edge"],
                    help="TTS engine (default: auto-detect, prefers edge for emotion)")
    ap.add_argument("--lang", default="en", 
                    help="Language code (en/tr) for voice selection (default: en)")
    ap.add_argument("--voice", default=None,
                    help="Manual voice override (disables emotion-based selection)")
    ap.add_argument("--rate", type=int, default=150,
                    help="Speech rate for pyttsx3 (default: 150)")
    
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
    print("\n" + "="*60)
    print("Text-to-Avatar Pipeline with Emotion-Based TTS")
    print("="*60)
    print("Available TTS engines:")
    for engine, available in TTS_AVAILABLE.items():
        status = " OK" if available else " NOT AVAILABLE"
        print(f"  {status} {engine}")
    print("="*60 + "\n")
    
    # Get input text
    if args.text:
        text = args.text
    else:
        text = args.text_file.read_text(encoding='utf-8').strip()
    
    if not text:
        print("Error: Empty text input")
        sys.exit(1)
    
    print(f"Input text ({len(text)} chars):")
    print(f"  {text[:100]}{'...' if len(text) > 100 else ''}\n")
    
    # Detect emotion from text (if auto)
    detected_emotion = args.emotion
    if args.emotion == "auto" and HAVE_TRANSFORMERS:
        print(" Detecting emotion from text...")
        detected_emotion = classify_emotion(text, args.emotion_model)
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
        else:
            # Fallback to other TTS engines
            generate_speech(
                text=text,
                output_path=audio_path,
                engine=args.tts,
                lang=args.lang,
                voice=args.voice,
                rate=args.rate
            )
    except Exception as e:
        print(f" TTS generation failed: {e}")
        sys.exit(1)
    
    # Verify lipsync script exists
    if not args.lipsync_script.exists():
        print(f" Lipsync script not found: {args.lipsync_script}")
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
        print(f"\n🗑 Removed temporary audio: {audio_path}")
    
    # Final report
    print("\n" + "="*60)
    if result['success']:
        print(" SUCCESS!")
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