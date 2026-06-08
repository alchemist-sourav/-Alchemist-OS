import os
import logging
import json
import speech_recognition as sr
import pyttsx3
import pygame
from core.config import settings

logger = logging.getLogger("AlchemistProviders")

# Initialize pygame mixer for audio playback
if not pygame.mixer.get_init():
    try:
        pygame.mixer.init()
    except Exception as e:
        logger.error(f"Failed to initialize Pygame mixer: {e}")

# ==========================================
# 1. LLM Provider Abstraction
# ==========================================

class BaseLLMProvider:
    def generate_completion(self, messages: list, response_format: dict = None) -> str:
        raise NotImplementedError()

class GroqLLMProvider(BaseLLMProvider):
    def __init__(self):
        from groq import Groq
        self.client = Groq(api_key=settings.GROQ_API_KEY)

    def generate_completion(self, messages: list, response_format: dict = None) -> str:
        kwargs = {
            "model": "llama-3.3-70b-versatile",
            "messages": messages,
        }
        if response_format:
            kwargs["response_format"] = response_format
        
        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content

class LocalLLMProvider(BaseLLMProvider):
    """
    Offline local LLM provider. Attempts to connect to Ollama (http://localhost:11434).
    If Ollama is offline or not installed, falls back to a rules-based mock engine
    to guarantee the system never crashes when completely disconnected.
    """
    def __init__(self):
        self.ollama_url = "http://localhost:11434/api/chat"
        import urllib.request
        self.urllib = urllib.request

    def generate_completion(self, messages: list, response_format: dict = None) -> str:
        # Check if Ollama is running
        try:
            payload = {
                "model": "llama3", # Default local model
                "messages": messages,
                "stream": False
            }
            if response_format and response_format.get("type") == "json_object":
                payload["format"] = "json"
                
            req = self.urllib.Request(
                self.ollama_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with self.urllib.urlopen(req, timeout=5) as response:
                res = json.loads(response.read().decode("utf-8"))
                return res["message"]["content"]
        except Exception as e:
            logger.warning(f"Local Ollama connection failed: {e}. Falling back to Mock Offline LLM.")
            return self._mock_offline_completion(messages, response_format)

    def _mock_offline_completion(self, messages: list, response_format: dict = None) -> str:
        # Extract user content
        user_query = ""
        for m in reversed(messages):
            if m["role"] == "user":
                user_query = m["content"].lower()
                break
        
        # Simple local keyword mapper for standard queries when completely offline
        thought = "Offline Mode: AI server unavailable. Executing predefined local fallback logic."
        steps = []
        goal = "respond"

        if "open google" in user_query or "search google" in user_query:
            goal = "Search Google"
            steps = [{"tool": "open_google", "args": {}}]
            thought = "Opening Google in your browser."
        elif "open youtube" in user_query:
            goal = "Open YouTube"
            steps = [{"tool": "open_youtube", "args": {}}]
            thought = "Opening YouTube."
        elif "open notepad" in user_query:
            goal = "Open Notepad"
            steps = [{"tool": "open_notepad", "args": {}}]
            thought = "Opening Notepad editor."
        elif "screenshot" in user_query or "capture screen" in user_query:
            goal = "Capture Screenshot"
            steps = [{"tool": "take_screenshot", "args": {}}]
            thought = "Taking a screenshot of your active desktop."
        elif "time" in user_query or "date" in user_query:
            goal = "Check Date/Time"
            steps = [{"tool": "get_current_datetime", "args": {}}]
            thought = "Checking current system date and time."
        else:
            thought = f"I am currently offline and couldn't match a local tool for '{user_query}'. Please reconnect or launch a local Ollama server."

        response_dict = {
            "goal": goal,
            "steps": steps,
            "thought": thought
        }
        return json.dumps(response_dict)

# ==========================================
# 2. STT Provider Abstraction
# ==========================================

class BaseSTTProvider:
    def recognize(self, audio: sr.AudioData, recognizer: sr.Recognizer) -> str:
        raise NotImplementedError()

class GoogleSTTProvider(BaseSTTProvider):
    def recognize(self, audio: sr.AudioData, recognizer: sr.Recognizer) -> str:
        return recognizer.recognize_google(audio)

class LocalWhisperSTTProvider(BaseSTTProvider):
    """
    Offline Speech-To-Text using whisper.
    Gracefully imports whisper/faster_whisper. If not installed, falls back to pocketsphinx or basic offline recognition.
    """
    def __init__(self):
        self.model = None
        try:
            from faster_whisper import WhisperModel
            logger.info("Initializing faster-whisper model (base)...")
            self.model = WhisperModel("base", device="cpu", compute_type="int8")
        except ImportError:
            try:
                import whisper
                logger.info("Initializing openai-whisper model (base)...")
                self.model = whisper.load_model("base")
            except ImportError:
                logger.warning("Whisper packages not found. Whisper STT will use local google/sphinx fallback.")

    def recognize(self, audio: sr.AudioData, recognizer: sr.Recognizer) -> str:
        if self.model:
            try:
                # Write audio file temporarily
                wav_data = audio.get_wav_data()
                temp_file = os.path.join(settings.DATA_DIR, "temp_stt.wav")
                with open(temp_file, "wb") as f:
                    f.write(wav_data)
                
                # Run transcription
                if hasattr(self.model, "transcribe"):
                    # Check if faster_whisper or openai whisper
                    try:
                        # faster_whisper
                        segments, info = self.model.transcribe(temp_file, beam_size=5)
                        text = " ".join([segment.text for segment in segments])
                    except Exception:
                        # openai-whisper
                        result = self.model.transcribe(temp_file)
                        text = result["text"]
                    
                    try:
                        os.remove(temp_file)
                    except Exception:
                        pass
                    return text.strip()
            except Exception as e:
                logger.error(f"Whisper transcription failed: {e}. Falling back to standard recognizer.")
        
        # Fallback to Sphinx (offline) or Google
        try:
            return recognizer.recognize_sphinx(audio)
        except Exception:
            return recognizer.recognize_google(audio)

# ==========================================
# 3. TTS Provider Abstraction
# ==========================================

class BaseTTSProvider:
    def speak(self, text: str):
        raise NotImplementedError()

class Pyttsx3TTSProvider(BaseTTSProvider):
    def __init__(self):
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', 170)
        voices = self.tts_engine.getProperty('voices')
        for voice in voices:
            if "Zira" in voice.name or "female" in voice.name.lower():
                self.tts_engine.setProperty('voice', voice.id)
                break

    def speak(self, text: str):
        filename = os.path.join(settings.DATA_DIR, "response.wav")
        self.tts_engine.save_to_file(text, filename)
        self.tts_engine.runAndWait()
        
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            import time
            time.sleep(0.1)
        pygame.mixer.music.unload()

class EdgeTTSProvider(BaseTTSProvider):
    """
    Offline/Online Microsoft Edge TTS. Generates natural-sounding speech for free.
    Falls back to Pyttsx3 if edge-tts package is missing or fails.
    """
    def __init__(self):
        self.has_edge = False
        try:
            import edge_tts
            self.edge_tts = edge_tts
            self.has_edge = True
        except ImportError:
            logger.warning("edge-tts library not found. Falling back to pyttsx3 for TTS.")
            self.fallback = Pyttsx3TTSProvider()

    def speak(self, text: str):
        if not self.has_edge:
            self.fallback.speak(text)
            return

        filename = os.path.join(settings.DATA_DIR, "response.wav")
        try:
            import asyncio
            async def generate():
                communicate = self.edge_tts.Communicate(text, "en-US-EmmaMultilingualNeural")
                await communicate.save(filename)
            
            # Run async function synchronously
            loop = asyncio.new_event_loop()
            loop.run_until_complete(generate())
            loop.close()

            # Play
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                import time
                time.sleep(0.1)
            pygame.mixer.music.unload()
        except Exception as e:
            logger.error(f"EdgeTTS failed: {e}. Using pyttsx3 fallback.")
            self.fallback = Pyttsx3TTSProvider()
            self.fallback.speak(text)

class ElevenLabsTTSProvider(BaseTTSProvider):
    """
    ElevenLabs API TTS. Falls back to EdgeTTS / Pyttsx3 if key is missing or fails.
    """
    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        if not self.api_key:
            logger.warning("ElevenLabs API key missing. Using EdgeTTS fallback.")
            self.fallback = EdgeTTSProvider()
        else:
            try:
                from elevenlabs.client import ElevenLabs
                self.client = ElevenLabs(api_key=self.api_key)
            except ImportError:
                logger.warning("elevenlabs library not found. Using EdgeTTS fallback.")
                self.fallback = EdgeTTSProvider()

    def speak(self, text: str):
        if not hasattr(self, 'client'):
            self.fallback.speak(text)
            return

        filename = os.path.join(settings.DATA_DIR, "response.wav")
        try:
            audio = self.client.generate(
                text=text,
                voice="Rachel",
                model="eleven_monolingual_v1"
            )
            # Write generator bytes to file
            with open(filename, "wb") as f:
                for chunk in audio:
                    f.write(chunk)
            
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                import time
                time.sleep(0.1)
            pygame.mixer.music.unload()
        except Exception as e:
            logger.error(f"ElevenLabs TTS failed: {e}. Using EdgeTTS fallback.")
            self.fallback = EdgeTTSProvider()
            self.fallback.speak(text)

# ==========================================
# 4. Provider Manager / Factory
# ==========================================

class ProviderManager:
    @staticmethod
    def get_llm_provider() -> BaseLLMProvider:
        prov = settings.LLM_PROVIDER.lower()
        if prov == "groq":
            return GroqLLMProvider()
        elif prov == "local":
            return LocalLLMProvider()
        else:
            logger.warning(f"Unknown LLM provider: {settings.LLM_PROVIDER}. Using Groq.")
            return GroqLLMProvider()

    @staticmethod
    def get_stt_provider() -> BaseSTTProvider:
        prov = settings.STT_PROVIDER.lower()
        if prov == "google":
            return GoogleSTTProvider()
        elif prov == "whisper":
            return LocalWhisperSTTProvider()
        else:
            logger.warning(f"Unknown STT provider: {settings.STT_PROVIDER}. Using Google.")
            return GoogleSTTProvider()

    @staticmethod
    def get_tts_provider() -> BaseTTSProvider:
        prov = settings.TTS_PROVIDER.lower()
        if prov == "pyttsx3":
            return Pyttsx3TTSProvider()
        elif prov == "edge_tts":
            return EdgeTTSProvider()
        elif prov == "elevenlabs":
            return ElevenLabsTTSProvider()
        else:
            logger.warning(f"Unknown TTS provider: {settings.TTS_PROVIDER}. Using Pyttsx3.")
            return Pyttsx3TTSProvider()
