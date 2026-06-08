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
        from core.providers import ProviderManager
        self.tts_provider = ProviderManager.get_tts_provider()
        self.is_interrupted = False

    def speak(self, text: str):
        self.is_interrupted = False
        logger.info(f"Speaking: {text}")
        try:
            self.tts_provider.speak(text)
        except Exception as e:
            logger.error(f"TTS execution error: {e}")

    def interrupt(self):
        logger.info("Interrupting speech.")
        self.is_interrupted = True
        try:
            import pygame
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
        except Exception as e:
            logger.error(f"Failed to interrupt Pygame mixer: {e}")
