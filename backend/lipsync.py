#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Local lipsync pipeline (CPU-only, Windows-friendly)

- Whisper (openai-whisper) -> words + timestamps
- English phonemes via g2p_en (no eSpeak) [default for EN]
- Turkish phonemes via phonemizer+eSpeak NG if available; else naive fallback
- Phones -> visemes (AA, IY, UW, F/V, M/B/P, REST)
- Energy-based vowel nudging
- Timeline cleaning & stabilization
- Render frames + MP4 (moviepy)

Robustness:
- Load audio with librosa -> avoids Whisper's internal ffmpeg
- MoviePy can use system ffmpeg or imageio-ffmpeg
- Works even if eSpeak NG is not detected (EN via g2p_en; TR falls back)
"""
import sys, logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# Add after imports
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
    

# NLP Libraries
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    HAVE_TRANSFORMERS = True
except Exception:
    HAVE_TRANSFORMERS = False


# ---------------------------
# Early environment helpers
# ---------------------------
import os, shutil
from pathlib import Path

# Prefer a common Windows ffmpeg location if present (harmless elsewhere)
# Ensure ffmpeg and espeak-ng paths are available in Docker (Linux) or Windows
_ffmpeg_path = shutil.which("ffmpeg")
if _ffmpeg_path:
    print(f"✅ ffmpeg found at: {_ffmpeg_path}")
else:
    print("⚠️ ffmpeg not found in PATH — ensure it’s installed (Dockerfile already handles this).")

# Optional: print espeak-ng info if available
_espeak_path = shutil.which("espeak-ng")
if _espeak_path:
    os.environ["PHONEMIZER_ESPEAK_PATH"] = _espeak_path
    print(f"✅ eSpeak NG found at: {_espeak_path}")


# Let moviepy find a bundled ffmpeg if installed
try:
    import imageio_ffmpeg
    os.environ["IMAGEIO_FFMPEG_EXE"] = imageio_ffmpeg.get_ffmpeg_exe()
except Exception:
    pass


_exe = os.environ.get("PHONEMIZER_ESPEAK_PATH")
if _exe and Path(_exe).is_file():
    exe_dir = str(Path(_exe).parent)
    os.environ["PATH"] = exe_dir + os.pathsep + os.environ.get("PATH", "")
    data_dir = Path(_exe).parent / "espeak-ng-data"
    if data_dir.is_dir() and "ESPEAKNG_DATA_PATH" not in os.environ:
        os.environ["ESPEAKNG_DATA_PATH"] = str(data_dir)

# ---------------------------
# Standard imports
# ---------------------------
import argparse, re, math, json
from typing import List, Dict
import numpy as np
from PIL import Image, Image as PILImage
from tqdm.auto import tqdm


import librosa
import whisper

import os, tempfile
os.environ["IMAGEIO_FFMPEG_EXE"] = "/usr/bin/ffmpeg"
os.environ["TMPDIR"] = "/tmp"
tempfile.tempdir = "/tmp"



# Optional phonemizers
try:
    from phonemizer import phonemize
    from phonemizer.separator import Separator
    HAVE_PHONEMIZER = True
except Exception:
    HAVE_PHONEMIZER = False

try:
    from g2p_en import G2p
    G2P_EN = G2p()
except Exception:
    G2P_EN = None

from moviepy.editor import ImageSequenceClip, AudioFileClip

# ---------------------------
# Config-like constants
# ---------------------------

EMOTION_LABELS = ["anger","disgust","fear","joy","neutral","sadness","surprise"]

MOUTH_FILES_DEFAULT = {
    "REST": "REST.png",
    "AA":   "AA.png",
    "IY":   "IY.png",
    "UW":   "UW.png",
    "F/V":  "FV.png",
    "M/B/P":"MBP.png"
}

VOWEL_WEIGHT   = 3.0
FV_WEIGHT      = 0.8
MBP_WEIGHT     = 0.6
DEFAULT_WEIGHT = 1.0
ALIGN_STRENGTH = 0.5

MIN_SEG_MS      = 80
MIN_HOLD_FRAMES = 3

# ---------------------------
# File & image utilities
# ---------------------------
def ensure_dirs(*dirs: Path):
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def find_file(stem_or_name: str, roots: List[Path]) -> Path:
    exts = [".png",".webp",".jpg",".jpeg",".PNG",".WEBP",".JPG",".JPEG"]
    for d in roots:
        p = d / stem_or_name
        if p.exists(): return p
    stem = Path(stem_or_name).stem
    for d in roots:
        for ext in exts:
            p = d / f"{stem}{ext}"
            if p.exists(): return p
    raise FileNotFoundError(f"Could not find {stem_or_name} in {roots}")

def load_mouth_images_original(mouth_map: Dict[str,str], roots: List[Path]):
    imgs = {}
    base_size = None
    for k, v in mouth_map.items():
        p = find_file(v, roots)
        img = Image.open(p).convert("RGBA")
        if base_size is None:
            base_size = img.size
        if img.size != base_size:
            img = img.resize(base_size, Image.LANCZOS)
        imgs[k] = img
    return imgs, base_size

def time_to_frame_floor(t, fps): return int(math.floor(t * fps))
def time_to_frame_ceil(t, fps):  return int(math.ceil (t * fps))

# ---------------------------
# Phone/Viseme mapping
# ---------------------------
def normalize_phone(p: str) -> str:
    p = p.lower()
    p = re.sub(r"[ːˑˈˌ̪̃̆ʲʰ]", "", p)
    p = p.replace("ɫ","l").replace("ɟ","g").replace("c","k")
    return p

VOWELS = set(list("aeiouyɪɯıɔœøʏəɛæɑɜɐʊɵɒ"))
def is_vowel_char(ch): return ch in VOWELS

# ARPAbet helpers (for g2p_en)
ARPABET_VOWELS = {
    "AA","AE","AH","AO","AW","AY",
    "EH","ER","EY","IH","IY",
    "OW","OY","UH","UW"
}
def strip_digits(arpa: str) -> str:
    return re.sub(r"\d+$","",arpa.upper())

def is_arpabet_vowel(tok: str) -> bool:
    return strip_digits(tok) in ARPABET_VOWELS

def is_vowel_phone(ph: str) -> bool:
    # ARPAbet vowel (g2p_en) or IPA vowel (eSpeak)
    return is_arpabet_vowel(ph) or (vowel_nucleus(normalize_phone(ph)) is not None)

# heuristics: spelling patterns that usually mean a rounded/long "o"
O_ROUND_PATTERNS = [
    r"oo", r"oa", r"oe", r"ow", r"oh",
    r"o(?=[^aeiouy]*e\b)",   # "o_e" magic-e: home, code
    r"oar", r"oor", r"ore",  # "or" families
    r"sou", r"tho",          # soul/though-ish
]

import re as _re_o
def looks_like_rounded_o(word: str) -> bool:
    w = word.lower()
    return any(_re_o.search(p, w) for p in O_ROUND_PATTERNS)


def arpa_to_viseme(tok: str) -> str:
    t = strip_digits(tok)
    if t in {"AA","AE","AH","AO"}: return "AA"
    if t in {"IY","IH"}:           return "IY"
    if t in {"UW","UH","OW","OY"}: return "UW"
    # consonant closures handled elsewhere; default mid-open → IY, else REST
    return "IY"

# IPA-based mapping (for phonemizer/espeak)
V_DEFAULT = "REST"
V_MAP_BASE_VOWEL = {
    "a":"AA","æ":"AA","ɑ":"AA",
    "e":"IY","ɛ":"IY","ə":"IY",
    "i":"IY","ɪ":"IY","ɯ":"IY","ı":"IY",
    "o":"UW","ɔ":"UW","ø":"UW","ɵ":"UW",
    "u":"UW","ʊ":"UW","y":"UW"
}
MID_OPEN_SET = {"s","z","t","d","n","l","r","ɾ","j","y","h","k","g","ʃ","ʒ","ʧ","ʤ","ç","ğ","ɹ"}
SPECIAL_TO_VISEME = {
    "oʊ":"UW","əʊ":"UW",
    "ɔɹ":"UW","oɹ":"UW","ɚ":"UW","ɝ":"UW",
    "ɔː":"UW","oː":"UW","ou":"UW"
}

def vowel_nucleus(phone: str):
    for ch in phone:
        if is_vowel_char(ch):
            return ch
    return None

def phone_to_viseme(phone_token: str) -> str:
    # respect explicit closure labels from naive mapper
    if phone_token in {"F/V","M/B/P"}:
        return phone_token
    # ARPAbet token?
    if re.match(r"^[A-Z]{2,3}\d?$", phone_token):
        return arpa_to_viseme(phone_token)
    # IPA token
    b = normalize_phone(phone_token)
    if b in SPECIAL_TO_VISEME:
        return SPECIAL_TO_VISEME[b]
    v = vowel_nucleus(b)
    if v is not None:
        return V_MAP_BASE_VOWEL.get(v, "IY")
    return "IY" if b in MID_OPEN_SET else V_DEFAULT

def phones_to_visemes(phone_str: str):
    return [phone_to_viseme(t) for t in phone_str.split() if t]

def phone_weights(phones, visemes):
    w = []
    for ph, vi in zip(phones, visemes):
        phn = ph
        if is_arpabet_vowel(phn) or vowel_nucleus(normalize_phone(phn)) is not None:
            w.append(VOWEL_WEIGHT)
        elif vi == "F/V":
            w.append(FV_WEIGHT)
        elif vi == "M/B/P":
            w.append(MBP_WEIGHT)
        else:
            w.append(DEFAULT_WEIGHT)
    s = sum(w) or 1.0
    return [wi/s for wi in w]

def energy_peak_time(y, sr, t0, t1):
    s = int(max(0, np.floor(t0*sr)))
    e = int(min(len(y), np.ceil(t1*sr)))
    if e <= s+1: return (t0+t1)/2
    win = y[s:e]
    hop = max(1, int(0.010*sr))
    frame = max(hop, int(0.040*sr))
    rms = librosa.feature.rms(y=win, frame_length=frame, hop_length=hop)[0]
    if len(rms)==0: return (t0+t1)/2
    idx = int(np.argmax(rms))
    return float(np.clip(t0 + (idx*hop)/sr, t0, t1))

def condense_same_visemes(tl):
    if not tl: return []
    out = [tl[0].copy()]
    for seg in tl[1:]:
        if seg["viseme"] == out[-1]["viseme"] and abs(seg["start"] - out[-1]["end"]) < 1e-6:
            out[-1]["end"] = seg["end"]
        else:
            out.append(seg.copy())
    return out

def squash_micro_segments(tl, min_ms=80):
    if not tl: return tl
    min_s = min_ms/1000.0
    out = []
    for i, seg in enumerate(tl):
        dur = seg["end"] - seg["start"]
        if dur >= min_s or not out:
            out.append(seg); continue
        prev = out[-1]
        if prev["viseme"] == seg["viseme"]:
            prev["end"] = seg["end"]
        else:
            if i+1 < len(tl) and tl[i+1]["viseme"] == prev["viseme"]:
                prev["end"] = seg["end"]
            elif i+1 < len(tl):
                tl[i+1]["start"] = min(tl[i+1]["start"], seg["start"])
            else:
                prev["end"] = seg["end"]
    return condense_same_visemes(out)

def carry_vowel(tl, carry_ms=40):
    VOWELS_5 = {"AA","IY","UW"}
    CLOSURES = {"F/V","M/B/P"}
    out = []
    for i, seg in enumerate(tl):
        out.append(seg)
        if seg["viseme"] in VOWELS_5 and i+1 < len(tl):
            nxt = tl[i+1]
            if nxt["viseme"] not in CLOSURES:
                extend = carry_ms/1000.0
                seg["end"] = min(seg["end"] + extend, nxt["start"])
    return condense_same_visemes(out)

def stabilize_schedule(seq, min_hold=3):
    if not seq: return seq
    out = []
    curr = seq[0]; count = 0
    for v in seq:
        if v == curr:
            count += 1; out.append(v)
        else:
            if count < min_hold and len(out) > count:
                out[-count:] = [out[-count-1]] * count
            curr = v; count = 1; out.append(v)
    if count < min_hold and len(out) > count:
        out[-count:] = [out[-count-1]] * count
    return out

# ---------------------------
# Naive fallback (no eSpeak)
# ---------------------------
def naive_word_to_phones(word: str) -> str:
    # crude grapheme→"phones" signals closures for viseme mapping
    w = re.sub(r"[^a-zçğıöşüA-ZÇĞİÖŞÜ']", "", word.lower())
    if not w: return ""
    w = (w.replace("f"," F/V ").replace("v"," F/V ")
           .replace("m"," M/B/P ").replace("b"," M/B/P ").replace("p"," M/B/P "))
    return " ".join(w.split())

def naive_phonemize_words(words):
    return [naive_word_to_phones(w["text"]) for w in words]

def turkish_word_to_phones(word: str) -> str:
    """Simple Turkish grapheme-to-phoneme mapper"""
    w = word.lower()
    
    # Turkish-specific replacements
    w = w.replace('ç', 'ch').replace('ş', 'sh').replace('ğ', '')
    w = w.replace('ı', 'i').replace('ö', 'o').replace('ü', 'u')
    
    # Mark closures for viseme mapping
    w = (w.replace("f", " F/V ").replace("v", " F/V ")
           .replace("m", " M/B/P ").replace("b", " M/B/P ").replace("p", " M/B/P "))
    
    return " ".join(w.split())

def smart_phonemize_words(words, language="en"):
    """Phonemize words based on language"""
    if language == "tr":
        return [turkish_word_to_phones(w["text"]) for w in words]
    elif language == "en" and G2P_EN is not None:
        def _g2p_word(txt: str) -> str:
            toks = G2P_EN(txt)
            toks = [t for t in toks if re.match(r"^[A-Z]+[0-9]?$", t)]
            return " ".join(toks)
        return [_g2p_word(w["text"]) for w in words]
    else:
        return naive_phonemize_words(words)

# ---------------------------
# Emotion classification (Hugging Face)
# ---------------------------
EMO_TOKENIZER = None
EMO_MODEL = None

def load_emotion_model(model_name: str):
    global EMO_TOKENIZER, EMO_MODEL
    if EMO_TOKENIZER is None or EMO_MODEL is None:
        if not HAVE_TRANSFORMERS:
            raise RuntimeError("transformers not installed; pip install transformers")
        EMO_TOKENIZER = AutoTokenizer.from_pretrained(model_name)
        EMO_MODEL = AutoModelForSequenceClassification.from_pretrained(model_name)
        EMO_MODEL.eval()
    return EMO_TOKENIZER, EMO_MODEL

# normalize common label variants
_CANON = {
    "angry":"anger", "anger":"anger",
    "disgust":"disgust", "disgusted":"disgust",
    "fear":"fear","fearful":"fear",
    "joy":"joy","happy":"joy","happiness":"joy",
    "neutral":"neutral",
    "sad":"sadness","sadness":"sadness",
    "surprised":"surprise","surprise":"surprise",
}

def classify_emotion(text: str, model_name: str = None, language: str = None) -> str:
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
        return _CANON.get(raw, raw if raw in EMOTION_LABELS else "neutral")
    except Exception as e:
        print("Emotion model failed, defaulting to neutral:", e)
        return "neutral"


# ---------------------------
# Main
# ---------------------------
def main():
    ap = argparse.ArgumentParser(description="Local lipsync (CPU) – Whisper + (g2p_en|phonemizer|naive) + moviepy")
    ap.add_argument("--audio", required=True, help="Path to input audio (wav/mp3)")
    ap.add_argument("--mouths", required=True, help="Folder containing mouth PNG/WebP")
    ap.add_argument("--out_dir", default="output", help="Output folder")
    ap.add_argument("--fps", type=int, default=20, help="Video FPS")
    ap.add_argument("--lipsync_offset", type=float, default=-0.10, help="Seconds to nudge visemes")
    ap.add_argument("--bg", default="0,0,0", help="RGB background, e.g. 0,0,0")
    ap.add_argument("--min_seg_ms", type=int, default=MIN_SEG_MS, help="Drop segments shorter than this (ms)")
    ap.add_argument("--min_hold", type=int, default=MIN_HOLD_FRAMES, help="Debounce frame flips (#frames)")
    ap.add_argument("--whisper_model", default="tiny", choices=["tiny","base","small","medium","large"],
                    help="Whisper model size")
    ap.add_argument("--skip_video", action="store_true", help="Only build timeline and frames, skip MP4 assembly")
    ap.add_argument("--emotions_root", help="Root folder with emotion subfolders: anger, disgust, fear, joy, neutral, sadness, surprise")
    ap.add_argument("--emotion", default="auto",
                choices=["auto"] + EMOTION_LABELS,
                help="Which emotion mouthset to use; 'auto' runs the classifier")
    ap.add_argument("--emotion_model", default="esracesur/roberta_weighted",
                help="Hugging Face model id for emotion classification")
    ap.add_argument("--target_height", type=int, default=720,
                help="Target video height (480, 720, 1080). Lower = faster. Default: 720")

    args = ap.parse_args()


    # Echo encoder
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        print("Using ffmpeg:", ffmpeg_path)

    AUDIO_PATH = Path(args.audio)
    MOUTH_DIRS = [Path(args.mouths)]
    OUT_DIR    = Path(args.out_dir)
    FRAMES_DIR = OUT_DIR / "debug_frames"
    TIMELINE_JSON = OUT_DIR / "lipsync_timeline.json"
    OUT_VIDEO     = OUT_DIR / "message1_lipsync.mp4"
    FRAMERATE = args.fps
    LIPSYNC_OFFSET_SEC = args.lipsync_offset
    SOLID_BG_RGB = tuple(int(x.strip()) for x in args.bg.split(","))

    ensure_dirs(OUT_DIR, FRAMES_DIR)

    # ✅ OPTIMIZED: Load audio ONCE at native sample rate
    print("Loading audio...")
    y_native, sr_native = librosa.load(str(AUDIO_PATH), sr=None, mono=True)
    dur_audio = len(y_native) / sr_native
    print(f"Using audio: {AUDIO_PATH.resolve()} ({dur_audio:.2f}s)")

    # 1) Whisper on CPU - resample in memory (don't reload!)
    print("Loading Whisper…")
    model = whisper.load_model(args.whisper_model, device="cpu")
    y_16k = librosa.resample(y_native, orig_sr=sr_native, target_sr=16000)
    res = model.transcribe(y_16k, word_timestamps=True, language=None)
    detected_lang = res.get("language", "en")
    print("Detected language:", detected_lang)

    
    # Build transcript for emotion classifier
    transcript_text = " ".join(seg.get("text","") for seg in res.get("segments", [])).strip()

    # Choose mouth folder: emotion-driven (if provided) or single-folder legacy
    if args.emotions_root:
        if args.emotion == "auto":
            chosen_emotion = classify_emotion(transcript_text, args.emotion_model)
        else:
            chosen_emotion = args.emotion
        emotion_dir = Path(args.emotions_root) / chosen_emotion
        print(f"Emotion chosen: {chosen_emotion} -> {emotion_dir.resolve()}")
        MOUTH_DIRS = [emotion_dir]
    else:
        # keep your existing single-folder mode
        MOUTH_DIRS = [Path(args.mouths)]
        print(f"Emotion mode disabled; using single mouth folder: {MOUTH_DIRS[0].resolve()}")


    # words with timestamps
    words = []
    for seg in res.get("segments", []):
        for w in seg.get("words", []):
            words.append({"text": w["word"], "start": float(w["start"]), "end": float(w["end"])})

    if not words:
        # fallback—split segment text evenly
        for seg in res.get("segments", []):
            tokens = re.findall(r"\S+", seg.get("text",""))
            if not tokens: continue
            dur = seg["end"] - seg["start"]
            slot = max(1e-3, dur/len(tokens))
            for i, tk in enumerate(tokens):
                words.append({"text": tk, "start": float(seg["start"]+i*slot), "end": float(seg["start"]+(i+1)*slot)})

    if not words:
        raise RuntimeError("No words/timestamps found in audio.")

    # 2) Phonemize per word - smart language detection
    detected_language = detect_language(" ".join(w["text"] for w in words))
    print(f"Phonemizing as: {detected_language} (smart mapper)")
    split_by_word = smart_phonemize_words(words, language=detected_language)

    # Align lengths
    min_len = min(len(split_by_word), len(words))
    split_by_word = split_by_word[:min_len]
    words = words[:min_len]

    # 3) Load original audio (native sr) for energy snapping
    y, sr = y_native, sr_native

    # 4) Build timeline
    timeline = []
    for w, ph in zip(words, split_by_word):
        phones = [p for p in ph.split() if p.strip()]
        if not phones:
            continue
        vis = phones_to_visemes(ph)

        # ---- FORCE "O" SOUNDS TO USE UW (rounded-o mouth) ----
        word_txt = w["text"]
        force_o = looks_like_rounded_o(word_txt)

        for j, (phn, vi) in enumerate(zip(phones, vis)):
            # If ARPAbet O-vowel (OW, AO, OY...), make it UW
            if _re_o.match(r"^[AOY]O\d?$", phn.upper()):
                if is_vowel_phone(phn):
                    vis[j] = "UW"
                    continue

            # If spelling looks like "o" sound, force vowel viseme(s) to UW
            if force_o and is_vowel_phone(phn):
                vis[j] = "UW"

            # ---- FORCE "ee" and "eh" sounds to AA.png ----
        # ARPAbet: IY = “ee” (see), EH = “eh” (bed)
        for j, (phn, vi) in enumerate(zip(phones, vis)):
            # ARPAbet override
            if re.match(r"^(IY|EH)\d?$", phn.upper()):
                vis[j] = "AA"
                continue
            # IPA override: i (ee), e/ɛ (eh)
            b = normalize_phone(phn)
            nucl = vowel_nucleus(b)
            if nucl in {"i", "e", "ɛ"}:
                vis[j] = "AA"


        dur = max(1e-3, w["end"] - w["start"])
        shares = phone_weights(phones, vis)

        # cumulative bounds
        bounds = [w["start"]]
        acc = 0.0
        for sh in shares:
            acc += sh
            bounds.append(w["start"] + acc*dur)

        # vowel energy nudging
        for i,(phn,vi) in enumerate(zip(phones, vis)):
            if is_arpabet_vowel(phn) or vowel_nucleus(normalize_phone(phn)) is not None:
                a,b = bounds[i], bounds[i+1]
                peak = energy_peak_time(y, sr, a, b)
                mid  = (a+b)/2
                shift = (peak - mid) * ALIGN_STRENGTH
                new_a = max(w["start"], min(a + shift, b - 1e-3))
                new_b = max(new_a + 1e-3, min(b + shift, w["end"]))
                bounds[i], bounds[i+1] = new_a, new_b

        for i, vi in enumerate(vis):
            a, b = bounds[i], bounds[i+1]
            if b > a:
                timeline.append({"viseme": vi, "start": round(a,3), "end": round(b,3), "weight": 1.0})

    # 5) Clean timeline
    timeline = condense_same_visemes(timeline)
    timeline = squash_micro_segments(timeline, min_ms=args.min_seg_ms)
    timeline = carry_vowel(timeline, carry_ms=40)

    ensure_dirs(OUT_DIR, FRAMES_DIR)
    # Optional: only save if debugging
    
    print(f"imeline saved: {TIMELINE_JSON} | entries={len(timeline)}")
    if timeline[:10]:
        print("peek:", timeline[:10])

    # 6) Load mouth images (original size)
    # 6) Load mouth images and downscale for faster processing
    print("Loading mouth images...")
    mouth_imgs, (CANVAS_W, CANVAS_H) = load_mouth_images_original(MOUTH_FILES_DEFAULT, MOUTH_DIRS)
    print(f"Original canvas size: {CANVAS_W} x {CANVAS_H}")

    # Downscale for MUCH faster rendering (2048px → 720px)
    TARGET_HEIGHT = args.target_height  # Options: 480 (fastest), 720 (balanced), 1080 (quality)

    if CANVAS_H > TARGET_HEIGHT:
        scale_factor = TARGET_HEIGHT / CANVAS_H
        new_width = int(CANVAS_W * scale_factor)
        new_height = TARGET_HEIGHT
        
        print(f" Downscaling to {new_width}x{new_height} for {scale_factor*100:.1f}% size ({(1-scale_factor)*100:.1f}% faster)")
        
        # Resize all mouth images
        for key in mouth_imgs:
            mouth_imgs[key] = mouth_imgs[key].resize(
                (new_width, new_height), 
                Image.LANCZOS  # High-quality downscaling
            )
        
        CANVAS_W, CANVAS_H = new_width, new_height
        print(f" Resized to: {CANVAS_W} x {CANVAS_H}")
    else:
        print(f" Using original size: {CANVAS_W} x {CANVAS_H}")

    # 7) Build frame schedule

    total_frames = int(math.ceil(dur_audio * FRAMERATE))
    schedule = ["REST"] * total_frames

    for seg in timeline:
        s = time_to_frame_floor(max(0.0, seg["start"] + LIPSYNC_OFFSET_SEC), FRAMERATE)
        e = time_to_frame_ceil (max(0.0, seg["end"]   + LIPSYNC_OFFSET_SEC), FRAMERATE)
        s = max(0, min(total_frames-1, s))
        e = max(s+1, min(total_frames, e))
        for f in range(s, e):
            v = seg["viseme"] if seg["viseme"] in mouth_imgs else "REST"
            schedule[f] = v

    schedule = stabilize_schedule(schedule, args.min_hold)

    # 8) Render frames
    # 8) Render frames (optimized with caching)
    print("Rendering frames…")
    for p in Path(FRAMES_DIR).glob("frame_*.png"):
        try: p.unlink()
        except: pass

    # Pre-render unique visemes (cache)
    print("Pre-rendering unique mouth positions...")
    mouth_cache = {}
    bg_rgb = SOLID_BG_RGB
    for viseme_key in set(schedule):
        mouth = mouth_imgs.get(viseme_key, mouth_imgs["REST"])
        rgba = PILImage.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        rgba.alpha_composite(mouth, dest=(0, 0))
        rgb = PILImage.new("RGB", (CANVAS_W, CANVAS_H), bg_rgb)
        rgb.paste(rgba, mask=rgba.split()[-1])
        mouth_cache[viseme_key] = rgb

    # Fast rendering using cached images
    print(f"Rendering {len(schedule)} frames using {len(mouth_cache)} cached mouths...")
    frames_out = []
    if len(schedule) > 100:
        iterator = tqdm(schedule, desc="Rendering frames")
    else:
        print(f"Rendering {len(schedule)} frames...")
        iterator = schedule

    for i, viseme in enumerate(iterator):
        cached_img = mouth_cache[viseme]
        out_path = FRAMES_DIR / f"frame_{i:06d}.png"
        cached_img.save(out_path, optimize=False)
        frames_out.append(str(out_path))

    if args.skip_video:
        print("Skipping video assembly (--skip_video).")
        return

    # 9) Assemble video
    # 9) Assemble video with optimized settings
    print("Assembling video…")
    import multiprocessing
    clip = ImageSequenceClip(frames_out, fps=FRAMERATE)
    audio = AudioFileClip(str(AUDIO_PATH))
    clip = clip.set_audio(audio)
    # Generate unique temp path inside /tmp
    temp_audio_path = f"/tmp/temp_audio_{os.getpid()}.m4a"

    clip.write_videofile(
        str(OUT_VIDEO),
        codec="libx264",
        audio_codec="aac",
        fps=FRAMERATE,
        temp_audiofile=temp_audio_path,
        remove_temp=True,
        preset="ultrafast",
        threads=multiprocessing.cpu_count(),
        bitrate="1000k",
        logger=None,
        ffmpeg_params=[
            "-pix_fmt", "yuv420p",
            "-crf", "28",
            "-movflags", "+faststart"
        ]
    )


    print("Video saved:", OUT_VIDEO, "| size:", (CANVAS_W, CANVAS_H))
    print("Tip: tweak --lipsync_offset ±0.02 and --min_seg_ms / --min_hold if needed.")

if __name__ == "__main__":
    main()