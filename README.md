---
title: EmotiVoice Avatar Chat
emoji: 🎭
colorFrom: pink
colorTo: purple
sdk: docker
pinned: false
license: mit
---

# 🎭 EmotiVoice-Avatar Chat Demo

An AI-powered avatar that speaks with emotion-appropriate voices!

## Features

- 🎤 **Text-to-Speech**: Convert text to emotional speech
- 🎨 **Avatar Customization**: Customize hair, eyes, background
- 😊 **Emotion Detection**: Automatic emotion classification
- 🗣️ **Emotional Voices**: Voice changes based on detected emotion
- 🎬 **Lip Sync**: Realistic mouth movements

## How to Use

1. Enter text or upload audio
2. Customize your avatar appearance
3. Click "Generate" and wait for processing
4. Watch your personalized avatar video!

## Technology Stack

- **Backend**: Flask + Python
- **TTS**: Edge-TTS with emotion-based voices
- **Emotion Detection**: RoBERTa transformer model
- **Lip Sync**: Whisper + phoneme mapping
- **Video Generation**: MoviePy

## Note

Processing takes 30-60 seconds depending on text length. Please be patient!