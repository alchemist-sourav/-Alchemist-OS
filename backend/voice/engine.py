import os
import time
import logging
import pygame
import pyttsx3
from core.config import settings

logger = logging.getLogger("AlchemistVoice")

# Initialize Pygame mixer for audio playback
pygame.mixer.init()

class VoiceEngine:
    def __init__(self):
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', 170)
        
        # Try to use a female voice (often index 1 on Windows)
        voices = self.tts_engine.getProperty('voices')
        for voice in voices:
            if "Zira" in voice.name or "female" in voice.name.lower():
                self.tts_engine.setProperty('voice', voice.id)
                break
                
        self.is_interrupted = False

    def speak(self, text: str):
        self.is_interrupted = False
        logger.info(f"Speaking: {text}")
        
        try:
            filename = os.path.join(settings.DATA_DIR, "response.wav")
            
            # Generate the audio file locally using pyttsx3
            self.tts_engine.save_to_file(text, filename)
            self.tts_engine.runAndWait()
            
            # Play via Pygame so we can interrupt it!
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                if self.is_interrupted:
                    logger.info("Speech interrupted.")
                    pygame.mixer.music.stop()
                    break
                time.sleep(0.1)
                
            pygame.mixer.music.unload()
        except Exception as e:
            logger.error(f"Voice Error: {e}")

    def interrupt(self):
        logger.info("Interrupting speech.")
        self.is_interrupted = True
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()
