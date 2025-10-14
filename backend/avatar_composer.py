#!/usr/bin/env python3
"""
Avatar Composer - Combines avatar layers (hair, eyes, mouth) into final frames
"""

from pathlib import Path
from PIL import Image
import json
from typing import Dict, Optional
import logging, sys
logging.basicConfig(stream=sys.stdout, level=logging.INFO)


class AvatarComposer:
    def __init__(self, avatar_root: Path):
        self.avatar_root = Path(avatar_root)
        
    def get_available_options(self):
        """Return available customization options"""
        options = {
            'genders': ['male', 'female'],
            'hair_styles': {
                'male': ['curly', 'shaved', 'straight'],
                'female': ['curly', 'short', 'straight', 'wavy']
            },
            'hair_colors': ['black', 'blonde', 'blue', 'brown', 'light_brown', 'orange', 'red'],
            'eye_colors': ['black', 'blue', 'brown', 'green'],
            'emotions': ['anger', 'disgust', 'fear', 'joy', 'neutral', 'sadness', 'surprise']
        }
        return options
    
    def compose_single_emotion(
        self, 
        config: dict[str, str], 
        output_root: Path,
        emotion: str = "neutral"
    ) -> None:
        """
        Compose avatar mouthsets for ONLY ONE emotion (much faster!)
        """
        output_root = Path(output_root)
        emotion_dir = output_root / emotion
        emotion_dir.mkdir(parents=True, exist_ok=True)
        
        gender = config.get('gender', 'female')
        gender_folder = self.avatar_root / gender
        
        print(f"Composing {emotion} for {gender}...")
        logging.info("Composing %s for %s...", emotion, gender)
        
        # Mouth shapes to compose
        mouth_shapes = ["REST", "AA", "IY", "UW", "FV", "MBP"]
        
        for mouth_shape in mouth_shapes:
            mouth_path = gender_folder / 'mouthshapes' / emotion / f'{mouth_shape}.png'
            
            # LAYER ORDER (bottom to top):
            # 1. Hair (back layer)
            # 2. Eyes (middle layer) 
            # 3. Mouth shape (top layer)
            
            # Load the mouth shape
            mouth_img = Image.open(mouth_path).convert("RGBA")
            canvas_size = mouth_img.size
            
            # Start with transparent canvas
            result = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
            
            # Layer 1: Hair (FIRST/BACK)
            hair_style = config.get('hair_style', 'wavy')
            hair_color = config.get('hair_color', 'brown')
            hair_path = gender_folder / 'hair' / hair_style / f'{hair_color}.png'
            if hair_path.exists():
                hair = Image.open(hair_path).convert("RGBA")
                if hair.size != canvas_size:
                    hair = hair.resize(canvas_size, Image.LANCZOS)
                result = Image.alpha_composite(result, hair)
            
            # Layer 2: Eyes (MIDDLE)
            eye_color = config.get('eye_color', 'brown')
            eyes_path = gender_folder / 'eyes' / emotion / f'{eye_color}.png'  # ← FIXED PATH
            if eyes_path.exists():
                eyes = Image.open(eyes_path).convert("RGBA")
                if eyes.size != canvas_size:
                    eyes = eyes.resize(canvas_size, Image.LANCZOS)
                result = Image.alpha_composite(result, eyes)
            
            # Layer 3: Mouth (TOP/FRONT)
            result = Image.alpha_composite(result, mouth_img)
            
            # Save final composed image
            output_file = emotion_dir / f"{mouth_shape}.png"
            result.save(output_file)
        
        print(f"Composed {len(mouth_shapes)} mouthsets for {emotion}\n")
    
    def get_default_config(self):
        """Return default avatar configuration"""
        return {
            'gender': 'female',
            'hair_style': 'wavy',
            'hair_color': 'brown',
            'eye_color': 'brown',
            'background_color': 'pink'
        }


# Test function
if __name__ == '__main__':
    avatar_root = Path(__file__).parent.parent / 'assets' / 'avatar'
    composer = AvatarComposer(avatar_root)
    
    # Test composition
    config = composer.get_default_config()
    output = Path('test_output')
    composer.compose_single_emotion(config, output, emotion='neutral')
    print(f"Test output saved to: {output}")