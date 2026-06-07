# Troubleshooting Guide

### 1. "ModuleNotFoundError: No module named 'X'"
Ensure that your virtual environment is activated and the `backend` directory is correctly mapped to your `PYTHONPATH`. The `main.py` entrypoint automatically appends the local path.

### 2. Microphone Not Registering Wake Word
- Verify that your system microphone is selected as the default input device in Windows Sound Settings.
- PyAudio might fail to initialize if another application has taken exclusive control. Restart the `Alchemist.exe` daemon.
- Check `logs/errors.log` for `OSError: [Errno -9999] Unanticipated host error`.

### 3. Playwright Browser Crashes or Hangs
- If `browser_agent.py` hangs, you may be missing the Playwright browser binaries.
- Run: `playwright install chromium`
- If you notice heavy RAM usage, note that the BrowserSession automatically closes tabs on completion of tasks.

### 4. Vision Agent Hallucinating Screen Bounds
- Ensure your display scaling (DPI) in Windows is set to 100%. Custom display scaling can cause `pyautogui` and PIL to capture offset coordinates.

### 5. API Rate Limits
- If Groq returns a `429 Too Many Requests`, check the `system.log`. Alchemist OS will gracefully swallow the error and respond via voice that it cannot process the request currently. Wait 1 minute and try again.
