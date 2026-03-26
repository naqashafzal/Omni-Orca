import asyncio
from playwright.async_api import async_playwright

class BrowserAgent:
    def __init__(self, headless=False):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.page = None
        self.actions = []  # List to store recorded actions
        self.recording_metadata = {
            "name": "Untitled Recording",
            "mode": "manual",
            "start_time": None,
            "success": False
        }

    async def start(self):
        """Starts the browser session."""
        import os
        
        # Create persistent browser profile directory
        user_data_dir = os.path.join(os.getcwd(), "browser_profile")
        os.makedirs(user_data_dir, exist_ok=True)
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch_persistent_context(
            user_data_dir,
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-infobars"
            ],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.page = self.browser.pages[0] if self.browser.pages else await self.browser.new_page()
        
        # Stealth scripts
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        print("Browser started.")

    async def navigate(self, url, wait_until="networkidle"):
        """Navigates to the specified URL."""
        if not self.page:
            raise Exception("Browser not started. Call start() first.")
        
        # Record action
        self.record_action("navigate", {"url": url})
        
        print(f"Navigating to {url}...")
        try:
            await self.page.goto(url, wait_until=wait_until, timeout=60000)
        except Exception as e:
            print(f"Navigation warning (proceeding anyway): {e}")
            
        print(f"Arrived at {url}")

    async def get_screenshot_bytes(self):
        """Returns screenshot as bytes for AI analysis."""
        if not self.page:
            return None
        try:
            return await self.page.screenshot(type='jpeg', quality=60)
        except:
            return None

    async def click(self, selector):
        """Clicks an element and records the action. Handles iframes."""
        if not self.page:
            raise Exception("Browser not started.")
            
        # Record action
        self.record_action("click", {"selector": selector})
        
        print(f"Clicking {selector}...")
        
        # Check frames first (common for reCAPTCHA)
        target_frame = None
        for frame in self.page.frames:
            try:
                if await frame.query_selector(selector):
                    target_frame = frame
                    break
            except:
                continue
        
        if target_frame:
            print(f"Found {selector} in frame {target_frame.name or 'unknown'}")
            await target_frame.click(selector)
        else:
            # Fallback to main page (will wait if not found)
            await self.page.click(selector)

    async def type(self, selector, text):
        """Types text into an element and records the action."""
        if not self.page:
             raise Exception("Browser not started.")

        # Record action
        self.record_action("type", {"selector": selector, "text": text})

        print(f"Typing '{text}' into {selector}...")
        
        # Check frames first
        target_frame = None
        for frame in self.page.frames:
            try:
                if await frame.query_selector(selector):
                    target_frame = frame
                    break
            except:
                continue
                
        if target_frame:
            print(f"Found {selector} in frame {target_frame.name or 'unknown'}")
            await target_frame.fill(selector, text)
        else:
            await self.page.fill(selector, text)

    async def mouse_click(self, x, y, button="left", click_count=1):
        """Click at specific coordinates"""
        if not self.page:
            raise Exception("Browser not started.")
        
        # Record action
        self.record_action("mouse_click", {"x": x, "y": y, "button": button, "click_count": click_count})
        
        print(f"Mouse clicking at ({x}, {y}) with {button} button...")
        await self.page.mouse.click(x, y, button=button, click_count=click_count)

    async def mouse_move(self, x, y):
        """Move mouse to specific coordinates"""
        if not self.page:
            raise Exception("Browser not started.")
        
        # Record action
        self.record_action("mouse_move", {"x": x, "y": y})
        
        print(f"Moving mouse to ({x}, {y})...")
        await self.page.mouse.move(x, y)

    async def hover(self, selector):
        """Hover over an element"""
        if not self.page:
            raise Exception("Browser not started.")
        
        # Record action
        self.record_action("hover", {"selector": selector})
        
        print(f"Hovering over {selector}...")
        await self.page.hover(selector)

    async def right_click(self, selector):
        """Right-click an element"""
        if not self.page:
            raise Exception("Browser not started.")
        
        # Record action
        self.record_action("right_click", {"selector": selector})
        
        print(f"Right-clicking {selector}...")
        await self.page.click(selector, button="right")

    async def double_click(self, selector):
        """Double-click an element"""
        if not self.page:
            raise Exception("Browser not started.")
        
        # Record action
        self.record_action("double_click", {"selector": selector})
        
        print(f"Double-clicking {selector}...")
        await self.page.dblclick(selector)

    async def drag_and_drop(self, source_selector, target_selector):
        """Drag element from source to target"""
        if not self.page:
            raise Exception("Browser not started.")
        
        # Record action
        self.record_action("drag_and_drop", {"source": source_selector, "target": target_selector})
        
        print(f"Dragging {source_selector} to {target_selector}...")
        await self.page.drag_and_drop(source_selector, target_selector)

    async def scroll(self, x=0, y=0):
        """Scroll the page"""
        if not self.page:
            raise Exception("Browser not started.")
        
        # Record action
        self.record_action("scroll", {"x": x, "y": y})
        
        print(f"Scrolling by ({x}, {y})...")
        await self.page.evaluate(f"window.scrollBy({x}, {y})")

    async def press_key(self, key):
        """Press a keyboard key"""
        if not self.page:
            raise Exception("Browser not started.")
        
        # Record action
        self.record_action("press_key", {"key": key})
        
        print(f"Pressing key: {key}...")
        await self.page.keyboard.press(key)

    async def get_text(self, selector):
        """Get text content from an element"""
        if not self.page:
            raise Exception("Browser not started.")
        
        print(f"Getting text from {selector}...")
        element = await self.page.query_selector(selector)
        if element:
            text = await element.text_content()
            return text
        return None

    async def get_all_text(self):
        """Get all visible text from the page"""
        if not self.page:
            raise Exception("Browser not started.")
        
        print("Extracting all text from page...")
        text = await self.page.evaluate("""
            () => {
                return document.body.innerText;
            }
        """)
        return text

    async def copy_to_clipboard(self, text):
        """Copy text to clipboard"""
        if not self.page:
            raise Exception("Browser not started.")
        
        # Record action
        self.record_action("copy_to_clipboard", {"text": text})
        
        print(f"Copying to clipboard: {text[:50]}...")
        await self.page.evaluate(f"""
            navigator.clipboard.writeText(`{text}`);
        """)

    async def paste_from_clipboard(self, selector):
        """Paste from clipboard into an element"""
        if not self.page:
            raise Exception("Browser not started.")
        
        # Record action
        self.record_action("paste_from_clipboard", {"selector": selector})
        
        print(f"Pasting from clipboard into {selector}...")
        clipboard_text = await self.page.evaluate("""
            async () => {
                return await navigator.clipboard.readText();
            }
        """)
        await self.page.fill(selector, clipboard_text)

    async def select_all_text(self, selector):
        """Select all text in an element"""
        if not self.page:
            raise Exception("Browser not started.")
        
        # Record action
        self.record_action("select_all", {"selector": selector})
        
        print(f"Selecting all text in {selector}...")
        await self.page.click(selector)
        await self.page.keyboard.press("Control+A")

    async def extract_data(self, selector, attribute="textContent"):
        """Extract data from multiple elements"""
        if not self.page:
            raise Exception("Browser not started.")
        
        print(f"Extracting {attribute} from {selector}...")
        elements = await self.page.query_selector_all(selector)
        data = []
        for element in elements:
            if attribute == "textContent":
                value = await element.text_content()
            else:
                value = await element.get_attribute(attribute)
            if value:
                data.append(value.strip())
        return data

    async def scrape_data(self, container_selector, field_selectors):
        """
        Scrape structured data from a list of items.
        
        Args:
            container_selector (str): Selector for the item container (e.g., '.product-card')
            field_selectors (dict): Dict of { "Column Name": "relative_selector" }
        
        Returns:
            list[dict]: List of scraped items.
        """
        if not self.page:
            raise Exception("Browser not started.")
            
        print(f"Scraping structured data from {container_selector}...")
        
        # We use evaluate to run the scraping logic in the browser context for speed
        # passing the dict as an argument
        data = await self.page.evaluate("""
            ([container, fields]) => {
                const items = document.querySelectorAll(container);
                const results = [];
                
                items.forEach(item => {
                    const row = {};
                    for (const [key, selector] of Object.entries(fields)) {
                        const el = item.querySelector(selector);
                        row[key] = el ? el.innerText.trim() : "";
                    }
                    results.push(row);
                });
                
                return results;
            }
        """, [container_selector, field_selectors])
        
        print(f"Scraped {len(data)} items.")
        return data

    async def wait_for_text(self, text, timeout=30000):
        """Wait for specific text to appear on page"""
        if not self.page:
            raise Exception("Browser not started.")
        
        print(f"Waiting for text: '{text}'...")
        await self.page.wait_for_function(
            f"document.body.innerText.includes('{text}')",
            timeout=timeout
        )

    async def take_screenshot(self, path="screenshot.png"):
        """Takes a screenshot of the current page."""
        if not self.page:
            # raise Exception("Browser not started.")
            return None
        # Capture raw bytes
        return await self.page.screenshot()

    async def take_screenshot(self, path="screenshot.png"):
        """Takes a screenshot of the current page."""

    def record_action(self, action_type, params):
        """Records an action to the internal list."""
        self.actions.append({"action": action_type, "params": params})

    def start_recording(self, name="Untitled Recording", mode="manual"):
        """Starts a new recording session."""
        import time
        self.actions = []
        self.recording_metadata = {
            "name": name,
            "mode": mode,
            "start_time": time.time(),
            "success": False
        }

    def save_recording(self, filename=None, success=True):
        """Saves the recorded actions with metadata to a JSON file."""
        import json
        import time
        import os
        import re
        
        # Create recordings directory if it doesn't exist
        os.makedirs("recordings", exist_ok=True)
        
        # Generate filename if not provided
        if not filename:
            # Sanitize name for filename
            safe_name = re.sub(r'[^\w\s-]', '', self.recording_metadata["name"])
            safe_name = re.sub(r'[-\s]+', '_', safe_name)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"recordings/{safe_name}_{timestamp}.json"
        
        # Calculate duration
        duration = 0
        if self.recording_metadata["start_time"]:
            duration = time.time() - self.recording_metadata["start_time"]
        
        # Build recording data
        recording_data = {
            "metadata": {
                "name": self.recording_metadata["name"],
                "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "mode": self.recording_metadata["mode"],
                "success": success,
                "duration_seconds": round(duration, 2),
                "step_count": len(self.actions)
            },
            "actions": self.actions
        }
        
        with open(filename, 'w') as f:
            json.dump(recording_data, f, indent=2)
        print(f"Recording saved to {filename}")
        return filename

    @staticmethod
    def list_recordings():
        """Lists all saved recordings."""
        import os
        import json
        
        if not os.path.exists("recordings"):
            return []
        
        recordings = []
        for filename in os.listdir("recordings"):
            if filename.endswith(".json"):
                filepath = os.path.join("recordings", filename)
                try:
                    with open(filepath, 'r') as f:
                        data = json.load(f)
                        if "metadata" in data:
                            recordings.append({
                                "filename": filename,
                                "filepath": filepath,
                                **data["metadata"]
                            })
                except:
                    pass
        
        # Sort by creation date (newest first)
        recordings.sort(key=lambda x: x.get("created", ""), reverse=True)
        return recordings

    @staticmethod
    def delete_recording(filename):
        """Deletes a recording file."""
        import os
        filepath = os.path.join("recordings", filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"Deleted {filename}")
            return True
        return False

    async def replay_recording(self, filename="recording.json"):
        """Replays actions from a JSON file."""
        import json
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            # Handle new format with metadata
            if isinstance(data, dict) and "actions" in data:
                actions = data["actions"]
                metadata = data.get("metadata", {})
                print(f"Replaying: {metadata.get('name', filename)}")
                print(f"Original duration: {metadata.get('duration_seconds', 'unknown')}s")
            else:
                # Old format: just array of actions
                actions = data
            
            print(f"Replaying {len(actions)} actions from {filename}...")
            
            # Clear current actions so we don't re-record the replay (optional)
            self.actions = []

            for act in actions:
                atype = act["action"]
                params = act["params"]
                
                if atype == "navigate":
                    await self.navigate(params["url"])
                elif atype == "click":
                    await self.click(params["selector"])
                elif atype == "type":
                    await self.type(params["selector"], params["text"])
                
                # Add a small delay for visual clarity
                await asyncio.sleep(1)
                
            print("Replay finished.")
            
        except FileNotFoundError:
            print(f"Recording file {filename} not found.")

    async def get_title(self):
        """Returns the title of the current page."""
        if not self.page:
            return None
        return await self.page.title()

    async def close(self):
        """Closes the browser session."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self.browser = None
        self.page = None
        print("Browser closed.")
