# Alchemist OS

Alchemist OS is a futuristic, highly autonomous AI operating system designed to serve as a continuous background companion and digital operator. Built with a robust Python backend and a stunning 3D Next.js holographic interface, Alchemist is capable of understanding its environment, operating your computer, and performing complex multi-step reasoning.

## Core Capabilities

- **🎙️ Always-On Voice Interface**: Seamlessly interact using wake word detection ("Hey Alchemist") and offline text-to-speech (`pyttsx3`). 
- **🧠 Continuous Memory**: Features a persistent SQLite database tracking short-term conversations, long-term semantic memory, active projects, and user preferences.
- **👁️ Real Vision Engine**: Periodically captures screenshots and active windows, using the `llama-3.2-90b-vision-preview` model to structurally analyze UI elements, applications, and text (OCR).
- **🤖 Operator Mode**: Directly operates your machine using `PyAutoGUI` for precise mouse movements, clicking, and keyboard typing.
- **🌐 Browser Agent**: Uses Playwright for fully autonomous web navigation, Google searching, page extraction, and form submission.
- **⚙️ Planner & Executor**: Powered by `Llama-3.3-70b-versatile` via Groq. Alchemist dynamically constructs JSON execution plans and securely delegates them to a robust internal tool registry.
- **📈 Self-Improvement**: Automatically reflects on task execution outcomes, saving successful workflows and failure lessons into its database to improve future performance.
- **🛡️ High Reliability**: Built for 24/7 uptime with global error recovery, exponential backoffs, and auto-restart loops for hardware disconnections and browser crashes.

## System Architecture

```text
AlchemistAI/
├── backend/                  # Python Agent Core
│   ├── agents/               # Planner, Executor, and Browser agents
│   ├── core/                 # Config, WebSocket Server, Logger
│   ├── memory/               # SQLite MemoryManager
│   ├── tools/                # Extensible Tool Registry (System, File, Operator)
│   ├── vision/               # Screenshot and Groq Vision Analyzer
│   ├── voice/                # Wake word and PyTTSx3 synthesis
│   └── main.py               # Main Event Loop
│
├── frontend/                 # Next.js Holographic UI
│   ├── components/           # Three.js Orb, Live Telemetry Feeds
│   └── pages/                # Desktop UI
│
├── data/                     # Persistent JSON caches (calendar, notes)
├── logs/                     # System, Action, and Error Rotating Logs
└── screenshots/              # Temporary buffer for Vision Agent
```

## Setup & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- A Groq API Key (Exported as `GROQ_API_KEY`)

### Backend Initialization
1. Activate your virtual environment and install dependencies:
```powershell
.\venv\Scripts\activate
pip install -r requirements.txt
```
2. Run the main backend loop:
```powershell
python backend/main.py
```

### Frontend Initialization
1. Navigate to the frontend directory:
```powershell
cd frontend
npm install
```
2. Launch the futuristic UI:
```powershell
npm run dev
```

## Running the 24-Hour Stability Test
To verify the endurance of the memory, vision, planner, and browser subsystems without risking a full system crash, run the background test script:

```powershell
python backend/tests/stability_test.py
```
This test outputs a live `stability_report.md` tracking heap allocations, CPU usage, and crash counts.
