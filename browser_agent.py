import asyncio
from playwright.async_api import async_playwright

class BrowserAgent:
    def __init__(self, headless=False):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.page = None
        self.actions = []  # List to store recorded actions

    async def start(self):
        """Starts the browser session."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()
        print("Browser started.")

    async def navigate(self, url):
        """Navigates to the specified URL."""
        if not self.page:
            raise Exception("Browser not started. Call start() first.")
        
        # Record action
        self.record_action("navigate", {"url": url})
        
        print(f"Navigating to {url}...")
        await self.page.goto(url)
        # Wait for load state to ensure page is ready
        await self.page.wait_for_load_state("networkidle")
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
        """Clicks an element and records the action."""
        if not self.page:
            raise Exception("Browser not started.")
            
        # Record action
        self.record_action("click", {"selector": selector})
        
        print(f"Clicking {selector}...")
        await self.page.click(selector)

    async def type(self, selector, text):
        """Types text into an element and records the action."""
        if not self.page:
             raise Exception("Browser not started.")

        # Record action
        self.record_action("type", {"selector": selector, "text": text})

        print(f"Typing '{text}' into {selector}...")
        await self.page.fill(selector, text)

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

    def save_recording(self, filename="recording.json"):
        """Saves the recorded actions to a JSON file."""
        import json
        with open(filename, 'w') as f:
            json.dump(self.actions, f, indent=4)
        print(f"Recording saved to {filename}")

    async def replay_recording(self, filename="recording.json"):
        """Replays actions from a JSON file."""
        import json
        try:
            with open(filename, 'r') as f:
                actions = json.load(f)
            
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
        print("Browser closed.")
