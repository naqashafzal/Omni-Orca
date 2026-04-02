import pyautogui
import subprocess
import io
import base64
from PIL import ImageGrab

class OSAgent:
    """
    Provides native OS-level control over the mouse, keyboard, and screen.
    WARNING: Use with caution as this takes physical control of the user's input devices.
    """
    def __init__(self):
        # Configure fail-safes
        pyautogui.FAILSAFE = True
        # Small delay after every PyAutoGUI action to ensure the UI catches up
        pyautogui.PAUSE = 0.5 

    def mouse_move(self, x: int, y: int, duration: float = 0.5) -> str:
        """Moves the mouse to specific absolute coordinates on the screen."""
        try:
            pyautogui.moveTo(x, y, duration=duration, tween=pyautogui.easeInOutQuad)
            return f"Moved mouse to ({x}, {y})"
        except pyautogui.FailSafeException:
            return "ERROR: Mouse moved to a corner (FailSafe triggered). Aborting."
        except Exception as e:
            return f"Error moving mouse: {e}"

    def mouse_click(self, x: int = None, y: int = None, button: str = 'left') -> str:
        """Clicks the mouse at current position or specified coordinates."""
        try:
            if x is not None and y is not None:
                pyautogui.click(x=x, y=y, button=button)
                return f"Clicked {button} button at ({x}, {y})"
            else:
                pyautogui.click(button=button)
                return f"Clicked {button} button at current position"
        except pyautogui.FailSafeException:
            return "ERROR: Mouse moved to a corner (FailSafe triggered). Aborting."
        except Exception as e:
            return f"Error clicking: {e}"

    def mouse_drag(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 1.0) -> str:
        """Drags the mouse from start coordinates to end coordinates."""
        try:
            pyautogui.moveTo(start_x, start_y, duration=0.2)
            pyautogui.dragTo(end_x, end_y, duration=duration, button='left')
            return f"Dragged from ({start_x}, {start_y}) to ({end_x}, {end_y})"
        except pyautogui.FailSafeException:
            return "ERROR: Mouse moved to a corner (FailSafe triggered). Aborting."
        except Exception as e:
            return f"Error dragging mouse: {e}"

    def keyboard_type(self, text: str, interval: float = 0.05) -> str:
        """Types the literal string exactly as passed."""
        try:
            pyautogui.write(text, interval=interval)
            return "Typed string successfully."
        except Exception as e:
            return f"Error typing: {e}"

    def keyboard_press(self, key_combo: str) -> str:
        """
        Presses a single key or a combination of keys.
        Format example: 'enter', 'ctrl+c', 'alt+tab'
        """
        try:
            keys = [k.strip() for k in key_combo.split('+')]
            pyautogui.hotkey(*keys)
            return f"Pressed '{key_combo}'"
        except Exception as e:
            return f"Error pressing keys: {e}"

    def get_screen_size(self) -> str:
        """Returns the current screen resolution to give the LLM bounds."""
        width, height = pyautogui.size()
        return f"Screen resolution: {width}x{height}"

    def take_screenshot(self) -> bytes:
        """Takes a full screen screenshot and returns it as JPEG bytes."""
        try:
            img = ImageGrab.grab()
            img_byte_arr = io.BytesIO()
            # Convert to RGB if it has an alpha channel (JPEG doesn't support RGBA)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(img_byte_arr, format='JPEG', quality=70)
            return img_byte_arr.getvalue()
        except Exception as e:
            print(f"Error taking screen screenshot: {e}")
            return None

    def open_application(self, app_name_or_path: str) -> str:
        """
        Attempts to open an application by spawning a subprocess.
        In Windows, 'start <app_name>' via shell usually works for system apps.
        For UWP apps (like WhatsApp), we use the app protocol (e.g., 'start whatsapp:').
        """
        try:
            import os
            clean_name = str(app_name_or_path).lower().strip()
            
            # Map common human app names to Windows executables
            app_mappings = {
                "task manager": "taskmgr",
                "calculator": "calc",
                "notepad": "notepad",
                "paint": "mspaint",
                "command prompt": "cmd",
                "cmd": "cmd",
                "word": "winword",
                "excel": "excel",
                "powerpoint": "powerpnt",
                "settings": "ms-settings:",
                "explorer": "explorer",
                "file explorer": "explorer",
                "chrome": "chrome",
                "edge": "msedge",
                "firefox": "firefox",
                "whatsapp": "whatsapp:",
                "spotify": "spotify:",
            }
            
            # Translate if necessary
            target = app_mappings.get(clean_name, clean_name)
            
            # Common UWP app protocols
            if target.endswith(':'):
                subprocess.Popen(f'start {target}', shell=True)
                return f"Attempted to launch Windows App via protocol: '{target}'"
            else:
                # Standard desktop apps or absolute paths
                subprocess.Popen(f'start "" "{target}"', shell=True)
                return f"Attempted to launch standard app: '{target}'"
        except Exception as e:
            return f"Error opening application '{app_name_or_path}': {e}"
