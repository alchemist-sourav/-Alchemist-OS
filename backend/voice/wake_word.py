import logging
import time
import threading
import speech_recognition as sr
from typing import Callable
from core.config import settings

logger = logging.getLogger("AlchemistWakeWord")

class WakeWordSystem:
    def __init__(self, voice_engine=None, planner_callback: Callable=None, broadcast_func=None, main_loop=None):
        self.state = "sleeping"
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.voice_engine = voice_engine
        self.planner_callback = planner_callback
        self.broadcast_func = broadcast_func
        self.main_loop = main_loop
        
        from core.providers import ProviderManager
        self.stt_provider = ProviderManager.get_stt_provider()
        
        self.running = False
        self.listen_thread = None
        self.last_speech_time = time.time()
        self.timeout_seconds = getattr(settings, "WAKE_WORD_TIMEOUT", 15.0)
        self._audio_ready = False

    def _init_audio(self):
        try:
            import pygame
            pygame.mixer.init()
            self._audio_ready = True
        except Exception as e:
            logger.warning(f"Audio initialization failed (continuing without sound): {e}")
            self._audio_ready = False

    def start(self):
        if self.running:
            return

        self._init_audio()
        self.running = True
        logger.info("Starting Wake Word System in background...")
        self.listen_thread = threading.Thread(target=self._run_loop, daemon=True)
        self.listen_thread.start()

    def stop(self):
        self.running = False
        if self.listen_thread:
            self.listen_thread.join(timeout=2.0)

    def set_state(self, new_state: str):
        if self.state != new_state:
            logger.info(f"State transition: {self.state} -> {new_state}")
            self.state = new_state
            if new_state == "listening":
                self.last_speech_time = time.time()
                
            if self.broadcast_func and self.main_loop:
                status_map = {
                    "sleeping": "idle",
                    "listening": "listening",
                    "thinking": "stt",
                    "speaking": "tts"
                }
                status = status_map.get(new_state, "idle")
                try:
                    import asyncio
                    asyncio.run_coroutine_threadsafe(
                        self.broadcast_func({"type": "status_update", "status": status}),
                        self.main_loop
                    )
                except Exception as e:
                    logger.error(f"Error broadcasting state transition: {e}")

    def _play_activation_sound(self):
        # We can play a simple ding if Pygame is available
        # But since we don't have an asset, we'll just log it.
        # In a real setup, we'd load an mp3/wav here.
        logger.info("[Activation Sound Played]")

    def _handle_interruption(self):
        logger.info("Interruption detected! Halting operations.")
        if self.voice_engine:
            self.voice_engine.interrupt()
        self.set_state("sleeping")

    def _process_audio(self, audio: sr.AudioData):
        try:
            text = self.stt_provider.recognize(audio, self.recognizer).lower()
            logger.info(f"Heard: '{text}'")
            
            # Interruption check
            if "stop" in text:
                self._handle_interruption()
                return

            assistant_state = self.state
            if assistant_state == "speaking":
                logger.info("Microphone input ignored: Assistant is speaking.")
                return

            if self.state == "sleeping":
                if "alchemist" in text:
                    self._play_activation_sound()
                    self.set_state("listening")
            
            elif self.state == "listening":
                self.last_speech_time = time.time()
                
                # If they say something while listening, process it
                if text.strip() and text != "hey alchemist":
                    self.set_state("thinking")
                    
                    if self.planner_callback:
                        # We execute in a separate thread to not block the wake word loop
                        threading.Thread(target=self._execute_planner, args=(text,), daemon=True).start()
                    else:
                        self.set_state("sleeping")

        except sr.UnknownValueError:
            pass # Ignore silence/unrecognized
        except sr.RequestError as e:
            logger.error(f"STT Request Error: {e}")

    def _execute_planner(self, text: str):
        try:
            logger.info("Sending to planner...")
            if self.planner_callback:
                if self.broadcast_func and self.main_loop:
                    import asyncio
                    asyncio.run_coroutine_threadsafe(
                        self.broadcast_func({"type": "status_update", "status": "planning"}),
                        self.main_loop
                    )
                response = self.planner_callback(text)
                self.set_state("speaking")
                if self.voice_engine:
                    logger.info("[Microphone Paused]")
                    logger.info("[TTS Started]")
                    self.voice_engine.speak(response)
                    logger.info("[TTS Finished]")
                    logger.info("[Microphone Resumed]")
        except Exception as e:
            logger.error(f"Planner execution error: {e}")
        finally:
            if self.state not in ["sleeping", "listening"]: # Ensure it didn't get interrupted
                self.set_state("sleeping")

    def _run_loop(self):
        while self.running:
            try:
                if not self.microphone:
                    self.microphone = sr.Microphone()
                    with self.microphone as source:
                        self.recognizer.adjust_for_ambient_noise(source)
                        logger.info("Microphone calibrated. System is ready.")
            except Exception as e:
                logger.error(f"Microphone error: {e}. Retrying in 5 seconds...")
                self.microphone = None
                time.sleep(5)
                continue

            try:
                # If assistant is speaking, pause listening/processing and wait
                if self.state == "speaking":
                    time.sleep(0.5)
                    continue

                # Timeout logic for listening state
                if self.state == "listening":
                    elapsed = time.time() - self.last_speech_time
                    remaining = max(0.0, self.timeout_seconds - elapsed)
                    logger.info(f"Listening... {int(remaining)} seconds remaining.")
                    if elapsed > self.timeout_seconds:
                        logger.info(f"{int(self.timeout_seconds)}-second timeout reached.")
                        self.set_state("sleeping")

                with self.microphone as source:
                    try:
                        audio = self.recognizer.listen(source, timeout=1.0, phrase_time_limit=5.0)
                        self._process_audio(audio)
                    except sr.WaitTimeoutError:
                        pass # Normal timeout if silence
                        
            except OSError as e:
                logger.error(f"Microphone disconnected: {e}. Will attempt to reconnect.")
                self.microphone = None
                time.sleep(5)
            except Exception as e:
                logger.error(f"Wake loop error: {e}")
                time.sleep(1)
