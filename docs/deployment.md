# Deployment Guide

Alchemist OS can be deployed either as a standard Python background daemon or bundled into a native Windows executable.

## 1. Local Python Daemon (Development/Standard)
For running locally across long periods, it is highly recommended to run the system via PM2 or a Windows Service to ensure automatic restarts.

```bash
# Using PM2
pm2 start backend/main.py --name "alchemist-os" --interpreter .\venv\Scripts\python.exe
pm2 save
```

## 2. Native Windows Executable (RC1 Packaged)
During the RC1 Hardening Phase, a `.spec` file is generated.
To build the standalone `.exe`:

```bash
pyinstaller Alchemist.spec
```

The resulting binary will be located in the `dist/` directory as `Alchemist.exe`. 
You can place this `.exe` in your Startup folder (`shell:startup`) for it to launch silently in the background every time Windows boots.

### Configuration for Executable
When running the `.exe`, ensure that `.env` is located in the same directory as the executable, or set the Environment Variables globally in Windows System Properties.
