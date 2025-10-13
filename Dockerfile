# ========== Base Image ==========
FROM python:3.10-slim

# ========== System Dependencies ==========
# ffmpeg → required for MoviePy / Whisper / audio ops
# espeak-ng → needed for phonemizer
# git → some huggingface models or whisper may need it
# libsndfile1 → needed for soundfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg espeak-ng git libsndfile1 \
 && rm -rf /var/lib/apt/lists/*


# ========== Working Directory ==========
WORKDIR /app

# Writable, persistent storage for Hugging Face / Docker
VOLUME ["/data"]

# ========== Copy & Install Python Dependencies ==========
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

 # ========== Pre-download NLTK data for g2p_en ==========
RUN python -m nltk.downloader -d /usr/local/share/nltk_data averaged_perceptron_tagger averaged_perceptron_tagger_eng cmudict


# ========== Copy Full Project ==========
COPY . .

# ========== Pre-download Hugging Face Emotion Model ==========
# This avoids re-downloading the model at runtime.
# The --user flag prevents permission issues on some hosts (e.g., Spaces)
RUN python -c "from transformers import AutoTokenizer, AutoModelForSequenceClassification; \
AutoTokenizer.from_pretrained('esracesur/roberta_weighted', use_auth_token=False); \
AutoModelForSequenceClassification.from_pretrained('esracesur/roberta_weighted', use_auth_token=False)"

# ========== Environment Variables ==========
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UPLOAD_FOLDER=/app/backend/uploads \
    OUTPUT_FOLDER=/app/backend/outputs \
    PORT=5000

# Make sure upload/output folders exist
RUN mkdir -p /app/backend/uploads /app/backend/outputs

# ========== Expose Port ==========
EXPOSE 7860

# ========== Run the App ==========
WORKDIR /app/backend
CMD ["python", "app.py", "--port", "7860", "--host", "0.0.0.0"]
