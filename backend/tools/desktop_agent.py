import os
import logging
import ctypes
import subprocess
import psutil
from tools.registry import registry

logger = logging.getLogger("AlchemistDesktopAgent")

# ==========================================
# 1. Window Management (ctypes Windows API)
# ==========================================

EnumWindows = ctypes.windll.user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
GetWindowText = ctypes.windll.user32.GetWindowTextW
GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
IsWindowVisible = ctypes.windll.user32.IsWindowVisible

_window_list = []

def _enum_windows_callback(hwnd, lParam):
    if IsWindowVisible(hwnd):
        length = GetWindowTextLength(hwnd)
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            GetWindowText(hwnd, buff, length + 1)
            _window_list.append((hwnd, buff.value))
    return True

def list_active_windows() -> str:
    """Lists currently open/visible windows with their title and HWND handles."""
    global _window_list
    _window_list = []
    try:
        EnumWindows(EnumWindowsProc(_enum_windows_callback), 0)
        if not _window_list:
            return "No active visible windows found."
        res = "Active Visible Windows:\n"
        for hwnd, title in _window_list:
            res += f"HWND: {hwnd} | Title: {title}\n"
        return res
    except Exception as e:
        logger.error(f"Error listing windows: {e}")
        return f"Failed to list windows: {e}"

def minimize_window(title_substring: str) -> str:
    """Minimizes a window matching the title substring."""
    global _window_list
    _window_list = []
    try:
        EnumWindows(EnumWindowsProc(_enum_windows_callback), 0)
        for hwnd, title in _window_list:
            if title_substring.lower() in title.lower():
                ctypes.windll.user32.ShowWindow(hwnd, 6) # SW_MINIMIZE = 6
                return f"Successfully minimized window: '{title}' (HWND: {hwnd})"
        return f"No active window found matching '{title_substring}'."
    except Exception as e:
        logger.error(f"Error minimizing window: {e}")
        return f"Failed to minimize window: {e}"

def maximize_window(title_substring: str) -> str:
    """Maximizes a window matching the title substring."""
    global _window_list
    _window_list = []
    try:
        EnumWindows(EnumWindowsProc(_enum_windows_callback), 0)
        for hwnd, title in _window_list:
            if title_substring.lower() in title.lower():
                ctypes.windll.user32.ShowWindow(hwnd, 3) # SW_MAXIMIZE = 3
                return f"Successfully maximized window: '{title}' (HWND: {hwnd})"
        return f"No active window found matching '{title_substring}'."
    except Exception as e:
        logger.error(f"Error maximizing window: {e}")
        return f"Failed to maximize window: {e}"

def focus_window(title_substring: str) -> str:
    """Brings a window matching the title substring to the foreground."""
    global _window_list
    _window_list = []
    try:
        EnumWindows(EnumWindowsProc(_enum_windows_callback), 0)
        for hwnd, title in _window_list:
            if title_substring.lower() in title.lower():
                ctypes.windll.user32.ShowWindow(hwnd, 9) # SW_RESTORE = 9
                ctypes.windll.user32.SetForegroundWindow(hwnd)
                return f"Successfully focused and restored window: '{title}'"
        return f"No active window found matching '{title_substring}'."
    except Exception as e:
        logger.error(f"Error focusing window: {e}")
        return f"Failed to focus window: {e}"

# ==========================================
# 2. Clipboard Management (ctypes Windows API)
# ==========================================

def read_clipboard() -> str:
    """Reads and returns text currently in the system clipboard."""
    try:
        if not ctypes.windll.user32.OpenClipboard(None):
            return "Error: Could not open system clipboard."
        
        hCd = ctypes.windll.user32.GetClipboardData(13) # CF_UNICODETEXT = 13
        text = ""
        if hCd:
            pchData = ctypes.windll.kernel32.GlobalLock(hCd)
            text = ctypes.c_wchar_p(pchData).value
            ctypes.windll.kernel32.GlobalUnlock(hCd)
        
        ctypes.windll.user32.CloseClipboard()
        return text if text else "Clipboard is empty or does not contain text."
    except Exception as e:
        logger.error(f"Error reading clipboard: {e}")
        return f"Failed to read clipboard: {e}"

def write_clipboard(text: str) -> str:
    """Writes the specified text to the system clipboard."""
    try:
        if not ctypes.windll.user32.OpenClipboard(None):
            return "Error: Could not open system clipboard."
        
        ctypes.windll.user32.EmptyClipboard()
        encoded = text.encode('utf-16le')
        hCd = ctypes.windll.kernel32.GlobalAlloc(2, len(encoded) + 2) # GMEM_MOVEABLE = 2
        pchData = ctypes.windll.kernel32.GlobalLock(hCd)
        ctypes.cdll.msvcrt.wcscpy(ctypes.c_wchar_p(pchData), text)
        ctypes.windll.kernel32.GlobalUnlock(hCd)
        
        ctypes.windll.user32.SetClipboardData(13, hCd) # CF_UNICODETEXT = 13
        ctypes.windll.user32.CloseClipboard()
        return f"Successfully wrote text to clipboard (length: {len(text)})."
    except Exception as e:
        logger.error(f"Error writing clipboard: {e}")
        return f"Failed to write to clipboard: {e}"

# ==========================================
# 3. Process Monitoring (psutil)
# ==========================================

def list_running_processes() -> str:
    """Returns a list of the top 15 running processes sorted by RSS memory usage."""
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
            try:
                processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        processes.sort(key=lambda x: x['memory_info'].rss if x['memory_info'] else 0, reverse=True)
        res = "Top 15 Running Processes by Memory:\n"
        for p in processes[:15]:
            mem_mb = (p['memory_info'].rss / (1024 * 1024)) if p['memory_info'] else 0
            res += f"PID: {p['pid']} | Name: {p['name']} | Memory: {mem_mb:.1f} MB\n"
        return res
    except Exception as e:
        logger.error(f"Error listing processes: {e}")
        return f"Failed to list processes: {e}"

def kill_process(pid_or_name: str) -> str:
    """Terminates a process by its PID or substring matching its process name."""
    try:
        if pid_or_name.isdigit():
            pid = int(pid_or_name)
            proc = psutil.Process(pid)
            proc.terminate()
            return f"Successfully terminated process with PID {pid} ({proc.name()})"
        else:
            count = 0
            for proc in psutil.process_iter(['pid', 'name']):
                if pid_or_name.lower() in proc.info['name'].lower():
                    try:
                        proc.terminate()
                        count += 1
                    except Exception:
                        pass
            if count > 0:
                return f"Successfully terminated {count} process(es) matching '{pid_or_name}'"
            return f"No running process found matching name '{pid_or_name}'"
    except Exception as e:
        logger.error(f"Error killing process {pid_or_name}: {e}")
        return f"Failed to terminate process: {e}"

# ==========================================
# 4. Directory Navigation & Folder Creation
# ==========================================

def create_folder(folder_path: str) -> str:
    """Creates a directory folder recursively at the specified path."""
    try:
        os.makedirs(folder_path, exist_ok=True)
        return f"Successfully created folder at: '{os.path.abspath(folder_path)}'"
    except Exception as e:
        logger.error(f"Error creating folder {folder_path}: {e}")
        return f"Failed to create folder: {e}"

def open_file_explorer(path: str = ".") -> str:
    """Opens Windows File Explorer at the specified folder path."""
    try:
        abs_path = os.path.abspath(path)
        if os.name == 'nt':
            os.startfile(abs_path)
            return f"Successfully opened File Explorer at: '{abs_path}'"
        else:
            return "File explorer launch is only supported on Windows OS."
    except Exception as e:
        logger.error(f"Error opening explorer: {e}")
        return f"Failed to open File Explorer: {e}"

# ==========================================
# 5. Display Monitors & Annotation
# ==========================================

def get_monitors_info() -> str:
    """Queries display devices connected to this Windows workstation using PowerShell."""
    try:
        cmd = "powershell -command \"[System.Windows.Forms.Screen]::AllScreens | ForEach-Object { $_.DeviceName + ': ' + $_.Bounds.Width + 'x' + $_.Bounds.Height + ' (Primary=' + $_.Primary + ')' }\""
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            return "Connected Workstation Displays:\n" + result.stdout.strip()
        else:
            # Fallback to PyAutoGUI screen size
            import pyautogui
            w, h = pyautogui.size()
            return f"Workstation displays list failed. Primary monitor size is: {w}x{h} pixels."
    except Exception as e:
        logger.error(f"Error querying monitors: {e}")
        import pyautogui
        w, h = pyautogui.size()
        return f"Primary display resolution: {w}x{h} (Error querying display monitors: {e})"

def annotate_screenshot(screenshot_path: str, label_text: str, x: int, y: int) -> str:
    """Draws a red target box and overlay label text onto an image screenshot file."""
    try:
        from PIL import Image, ImageDraw
        img = Image.open(screenshot_path)
        draw = ImageDraw.Draw(img)
        
        # Draw target bounds
        draw.rectangle([x - 12, y - 12, x + 12, y + 12], outline="red", width=3)
        draw.text((x + 16, y - 10), label_text, fill="red")
        
        img.save(screenshot_path)
        return f"Successfully annotated screenshot '{os.path.basename(screenshot_path)}' at ({x}, {y}) with label: '{label_text}'"
    except Exception as e:
        logger.error(f"Error annotating image: {e}")
        return f"Failed to annotate image: {e}"

# ==========================================
# Registry Registrations
# ==========================================

registry.register("list_active_windows", list_active_windows)
registry.register("minimize_window", minimize_window)
registry.register("maximize_window", maximize_window)
registry.register("focus_window", focus_window)
registry.register("read_clipboard", read_clipboard)
registry.register("write_clipboard", write_clipboard)
registry.register("list_running_processes", list_running_processes)
registry.register("kill_process", kill_process)
registry.register("create_folder", create_folder)
registry.register("open_file_explorer", open_file_explorer)
registry.register("get_monitors_info", get_monitors_info)
registry.register("annotate_screenshot", annotate_screenshot)
