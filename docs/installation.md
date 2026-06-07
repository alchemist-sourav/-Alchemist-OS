# Installation Guide

Follow these steps to deploy Alchemist OS RC1 locally on your Windows machine.

## Prerequisites
- Python 3.10+
- Git
- Microsoft Visual C++ Build Tools (required for PyAudio/Playwright compilation)

## Step-by-Step Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-repo/AlchemistAI.git
cd AlchemistAI
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install Requirements
```bash
pip install -r requirements.txt
playwright install
```

### 4. Configure Environment Variables
Rename `.env.example` to `.env` and fill in your API credentials:
```env
GROQ_API_KEY=gsk_your_key_here
ELEVENLABS_API_KEY=sk_your_key_here
LOG_LEVEL=INFO
FRONTEND_URL=http://localhost:3000
```

### 5. Launch
```bash
python backend/main.py
```
Your backend will start successfully at `http://0.0.0.0:8000`.
