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

    # Ensure directories exist
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

settings = Settings()
