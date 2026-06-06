import logging
import time
import threading
import speech_recognition as sr
import pygame
from typing import Callable, Optional

logger = logging.getLogger("AlchemistWakeWord")

class WakeWordSystem:
    def __init__(self, voice_engine=None, planner_callback: Callable=None):
        self.state = "sleeping"
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.voice_engine = voice_engine
        self.planner_callback = planner_callback
        
        self.running = False
        self.listen_thread = None
        self.last_speech_time = time.time()
        self.timeout_seconds = 10.0

    def start(self):
        if self.running:
            return
            
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

    def _play_activation_sound(self):
        # We can play a simple ding if Pygame is available
        # But since we don't have an asset, we'll just log it.
        # In a real setup, we'd load an mp3/wav here.
        logger.info("🎵 [Activation Sound Played] 🎵")

    def _handle_interruption(self):
        logger.info("Interruption detected! Halting operations.")
        if self.voice_engine:
            self.voice_engine.interrupt()
        self.set_state("sleeping")

    def _process_audio(self, audio: sr.AudioData):
        try:
            # For efficiency in a real setup we'd use a local model like Vosk.
            # We use Google STT here as a fallback placeholder.
            text = self.recognizer.recognize_google(audio).lower()
            logger.info(f"Heard: '{text}'")
            
            # Interruption check
            if "stop" in text:
                self._handle_interruption()
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
                response = self.planner_callback(text)
                self.set_state("speaking")
                if self.voice_engine:
                    self.voice_engine.speak(response)
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
                # Timeout logic for listening state
                if self.state == "listening":
                    if time.time() - self.last_speech_time > self.timeout_seconds:
                        logger.info("10-second timeout reached.")
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
