# ========== Base Image ==========
FROM python:3.10-slim

# ========== System Dependencies ==========
# ffmpeg → required for MoviePy / Whisper / audio ops
# espeak-ng → needed for phonemizer
# git → required for Hugging Face / Whisper downloads
# libsndfile1 → needed for soundfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg espeak-ng git libsndfile1 \
 && rm -rf /var/lib/apt/lists/*

# ========== Working Directory ==========
WORKDIR /app

# ========== Persistent /data directory ==========
RUN mkdir -p /data/uploads /data/outputs && chmod -R 777 /data
VOLUME ["/data"]

# ========== Copy & Install Python Dependencies ==========
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ========== Pre-download NLTK data for g2p_en ==========
RUN python -m nltk.downloader -d /usr/local/share/nltk_data \
    averaged_perceptron_tagger averaged_perceptron_tagger_eng cmudict

# ========== Copy Full Project ==========
COPY . .

# ========== Pre-download Hugging Face Emotion Model ==========
RUN python -c "from transformers import AutoTokenizer, AutoModelForSequenceClassification; \
AutoTokenizer.from_pretrained('esracesur/roberta_weighted'); \
AutoModelForSequenceClassification.from_pretrained('esracesur/roberta_weighted')"

# ========== Environment Variables ==========
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DATA_DIR=/data \
    PORT=7860 \
    NUMBA_CACHE_DIR=/tmp \
    NUMBA_DISABLE_CACHING=1 \
    HF_HOME=/tmp/huggingface \
    TRANSFORMERS_CACHE=/tmp/huggingface \
    TORCH_HOME=/tmp/torch \
    XDG_CACHE_HOME=/tmp \
    WHISPER_CACHE_DIR=/tmp



# ========== Expose Port ==========
EXPOSE 7860

# ========== Run the App ==========
WORKDIR /app/backend
CMD ["python", "app.py"]
