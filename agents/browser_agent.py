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
        self.is_listening_to_human = False

    @property
    def _context(self):
        """Returns the active context, whether self.browser is a Browser or a BrowserContext."""
        if not self.browser: return None
        if hasattr(self.browser, 'contexts'):
            return self.browser.contexts[0] if self.browser.contexts else None
        return self.browser

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
        # Enable Python-JS bridge for organic human recording
        await self.browser.expose_binding("report_organic_action", self._handle_organic_action)
        
        # Stealth and tracking scripts
        await self.page.add_init_script("""
            // Stealth
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Human action tracker
            document.addEventListener('click', (e) => {
                if (!window._omni_is_recording) return;
                
                // Attempt to generate a unique CSS selector for what the user clicked
                let el = e.target;
                let selector = el.tagName.toLowerCase();
                if (el.id) selector += '#' + el.id;
                else if (el.className && typeof el.className === 'string') 
                    selector += '.' + el.className.trim().replace(/\\s+/g, '.');
                
                // Exclude clicks on the main body/html if accidental
                if (selector !== 'html' && selector !== 'body') {
                    window.report_organic_action({
                        action: "click",
                        params: { selector: selector, text: el.innerText ? el.innerText.substring(0, 30) : "" }
                    });
                }
            }, true);
            
            document.addEventListener('change', (e) => {
                if (!window._omni_is_recording) return;
                let el = e.target;
                if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                    let selector = el.tagName.toLowerCase();
                    if (el.id) selector += '#' + el.id;
                    else if (el.name) selector += `[name="${el.name}"]`;
                    
                    window.report_organic_action({
                        action: "type",
                        params: { selector: selector, text: el.value }
                    });
                }
            });
        """)
        print("Browser started. Human Action Tracker ready.")

    def _handle_organic_action(self, source, payload):
        """Callback from JS to record organic human actions into the runbook"""
        if getattr(self, 'is_listening_to_human', False):
            # Print to log so user sees the system learning
            print(f"[OMNI WATCHING] Learned action: {payload['action']} -> {payload['params']}")
            self.record_action(payload['action'], payload['params'])

    async def attach_to_existing_browser(self, port=9222) -> bool:
        """Attempts to connect to an existing Chrome instance over CDP."""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.connect_over_cdp(f"http://localhost:{port}")
            ctx = self._context
            if ctx:
                self.page = ctx.pages[0] if ctx.pages else await ctx.new_page()
            else:
                self.page = await self.browser.new_page()
            print(f"Attached to existing browser on port {port}.")
            return True
        except Exception as e:
            print(f"Failed to attach to browser on port {port}. Is Chrome running with --remote-debugging-port={port}?")
            return False

    async def get_open_tabs(self):
        """Returns a list of titles for all open tabs in the current context."""
        ctx = self._context
        if not ctx:
            return []
        pages = ctx.pages
        tabs = []
        for i, p in enumerate(pages):
            try:
                tabs.append(f"[{i}] {await p.title()}")
            except:
                tabs.append(f"[{i}] Unknown")
        return tabs

    async def switch_tab(self, index: int):
        """Switches to the tab at the given index."""
        ctx = self._context
        if not ctx:
            return "No browser context."
        pages = ctx.pages
        if 0 <= index < len(pages):
            self.page = pages[index]
            await self.page.bring_to_front()
            return f"Switched to tab {index}: {await self.page.title()}"
        return f"Invalid tab index {index}."

    async def close_tab(self, index: int):
        """Closes the tab at the given index."""
        ctx = self._context
        if not ctx:
            return "No browser context."
        pages = ctx.pages
        if 0 <= index < len(pages):
            target_page = pages[index]
            try:
                title = await target_page.title()
            except:
                title = "Unknown"
            await target_page.close()
            # If we closed the active page, fallback to remaining
            if self.page == target_page:
                remaining = ctx.pages
                if remaining:
                    self.page = remaining[0]
                    await self.page.bring_to_front()
                else:
                    self.page = None
            return f"Closed tab {index}: {title}"
        return f"Invalid tab index {index}."

    async def navigate(self, url, wait_until="domcontentloaded"):
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

    async def inject_som_overlay(self):
        """Injects Set-of-Mark numbered badges on interactive elements."""
        if not self.page: return
        js_code = """
        () => {
            document.querySelectorAll('.__som_badge').forEach(e => e.remove());
            
            const interactiveSelectors = [
                'a', 'button', 'input', 'select', 'textarea',
                '[role="button"]', '[role="link"]', '[role="checkbox"]',
                '[role="switch"]', '[role="tab"]', '[role="menuitem"]',
                '[onclick]'
            ].join(', ');
            
            const elements = document.querySelectorAll(interactiveSelectors);
            let count = 0;
            
            for (const el of elements) {
                const rect = el.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0 || rect.top < -10) continue;
                if (rect.top > window.innerHeight + 10 || rect.left > window.innerWidth + 10) continue;
                
                el.setAttribute('data-som-id', count);
                
                const badge = document.createElement('div');
                badge.className = '__som_badge';
                badge.textContent = count;
                badge.style.position = 'absolute';
                badge.style.left = Math.max(0, rect.left + window.scrollX) + 'px';
                badge.style.top = Math.max(0, rect.top + window.scrollY) + 'px';
                badge.style.backgroundColor = '#cc0000';
                badge.style.color = 'white';
                badge.style.fontSize = '12px';
                badge.style.fontWeight = 'bold';
                badge.style.padding = '1px 3px';
                badge.style.borderRadius = '3px';
                badge.style.zIndex = '2147483647';
                badge.style.pointerEvents = 'none';
                badge.style.border = '1px solid white';
                document.body.appendChild(badge);
                count++;
            }
        }
        """
        try:
            await self.page.evaluate(js_code)
            await self.page.wait_for_timeout(200) # Give DOM time to update
        except Exception as e:
            print(f"Overlay injection failed: {e}")

    async def remove_som_overlay(self):
        """Removes the Set-of-Mark badges."""
        if not self.page: return
        try:
            await self.page.evaluate("() => { document.querySelectorAll('.__som_badge').forEach(e => e.remove()); }")
        except:
            pass

    async def get_screenshot_bytes(self):
        """Returns screenshot as bytes for AI analysis."""
        if not self.page:
            return None
        try:
            return await self.page.screenshot(type='jpeg', quality=60)
        except:
            return None
            
    async def click_id(self, som_id):
        """Clicks an element by its SoM ID."""
        if not self.page: raise Exception("Browser not started.")
        self.record_action("click_id", {"id": som_id})
        print(f"Clicking SoM ID {som_id}...")
        selector = f"[data-som-id='{som_id}']"
        await self.page.click(selector, timeout=3000)

    async def type_id(self, som_id, text):
        """Types text into an element by its SoM ID."""
        if not self.page: raise Exception("Browser not started.")
        self.record_action("type_id", {"id": som_id, "text": text})
        print(f"Typing '{text}' into SoM ID {som_id}...")
        selector = f"[data-som-id='{som_id}']"
        try:
            await self.page.fill(selector, text, timeout=2000)
        except:
            await self.page.click(selector, timeout=3000)
            await self.page.keyboard.type(text)

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
            await target_frame.click(selector, timeout=3000)
        else:
            # Fallback to main page (will fail fast if not found to let AI retry)
            await self.page.click(selector, timeout=3000)

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
            try:
                await target_frame.fill(selector, text, timeout=2000)
            except:
                await target_frame.click(selector, timeout=5000)
                await self.page.keyboard.type(text)
        else:
            try:
                # Try fill first for normal inputs
                await self.page.fill(selector, text, timeout=2000)
            except:
                # Fallback to click and type for rich text editors (like Facebook)
                await self.page.click(selector, timeout=5000)
                await self.page.keyboard.type(text)

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

    def start_recording(self, name="Untitled Training Sequence", mode="manual"):
        """Starts a new recording session."""
        import time
        self.actions = []
        self.is_listening_to_human = True
        self.recording_metadata = {
            "name": name,
            "mode": mode,
            "start_time": time.time(),
            "success": False
        }
        
        # If page is active, tell JS to start listening
        if self.page:
            try:
                # Fire and forget; safe to run synchronous eval if we don't await result
                import asyncio
                asyncio.create_task(self.page.evaluate("window._omni_is_recording = true;"))
            except: pass

    def save_recording(self, filename=None, success=True):
        """Saves the recorded actions with metadata to a JSON file."""
        import json
        import time
        import os
        import re
        
        self.is_listening_to_human = False
        if self.page:
            try:
                import asyncio
                asyncio.create_task(self.page.evaluate("window._omni_is_recording = false;"))
            except: pass
        
        # Create recordings directory if it doesn't exist
        os.makedirs("recordings", exist_ok=True)
        
        # Generate filename if not provided
        if not filename:
            # Sanitize name for filename
            safe_name = re.sub(r'[^\w\s-]', '', self.recording_metadata.get("name", "untitled"))
            safe_name = re.sub(r'[-\s]+', '_', safe_name)
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{safe_name}_{timestamp}.json"

        # Force save into recordings directory
        if not filename.startswith("recordings"):
            filename = os.path.join("recordings", filename)
        
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
        import os
        if not filename.startswith("recordings") and not os.path.exists(filename):
            filename = os.path.join("recordings", filename)
        
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
