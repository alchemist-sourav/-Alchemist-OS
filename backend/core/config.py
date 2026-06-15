import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "Alchemist AI"
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    LOGS_DIR: str = os.path.join(BASE_DIR, "logs")
    SCREENSHOTS_DIR: str = os.path.join(BASE_DIR, "screenshots")
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", os.path.join(DATA_DIR, "memory.db"))
    WAKE_WORD_TIMEOUT: float = float(os.getenv("WAKE_WORD_TIMEOUT", "15.0"))
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")
    STT_PROVIDER: str = os.getenv("STT_PROVIDER", "google")
    TTS_PROVIDER: str = os.getenv("TTS_PROVIDER", "pyttsx3")
    API_KEY: str = os.getenv("API_KEY", "alchemist_default_secret")

    # Ensure directories exist
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

    def validate(self):
        if not self.GROQ_API_KEY:
            raise ValueError("CRITICAL: GROQ_API_KEY environment variable is missing!")
        if self.API_KEY == "alchemist_default_secret" and os.getenv("NODE_ENV") == "production":
            import logging
            logging.warning("WARNING: Using default API_KEY in production. This is highly insecure.")

settings = Settings()
settings.validate()
