import google.generativeai as genai
import json
import json
import os
from prompts import SYSTEM_PROMPTS

class GeminiClient:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.model = None
        if api_key:
            self.configure(api_key)

    def configure(self, api_key):
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def interpret_command(self, user_text, screenshot_bytes=None, mode="GENERAL"):
        """
        Sends the user text (and optional screenshot) to Gemini.
        Returns a structured JSON command.
        """
        if not self.model:
            return {"error": "API Key not configured."}

        base_prompt = SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["GENERAL"])
        
        prompt = f"""
        {base_prompt}

        Task: Translate this command into valid JSON.
        Command: "{user_text}"
        
        Return ONLY the JSON. No markdown formatting.
        """
        
        content = [prompt]
        if screenshot_bytes:
            # Gemini python lib expects a PIL Image or bytes with mime_type
            from PIL import Image
            import io
            image = Image.open(io.BytesIO(screenshot_bytes))
            content.append(image)
        
        try:
            response = self.model.generate_content(content)
            
            # clean response if it has backticks
            text = response.text.strip()
            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "")
            elif text.startswith("```"):
                text = text.replace("```", "")
                
            try:
                data = json.loads(text)
                # Ensure it's a list
                if isinstance(data, dict):
                    return [data]
                elif isinstance(data, list):
                    return data
                else:
                    return {"error": "Invalid JSON format received."}
            except json.JSONDecodeError:
                 return {"error": f"Invalid JSON: {text}"}
        except Exception as e:
            return {"error": f"Gemini Error: {str(e)}"}

    def autopilot_step(self, goal, screenshot_bytes=None):
        """
        Auto-pilot mode: AI observes page and decides next action(s).
        Returns: {"completed": bool, "reasoning": str, "actions": []}
        """
        if not self.model:
            return {"error": "API Key not configured."}

        prompt = f"""
        {SYSTEM_PROMPTS["AUTOPILOT"]}

        USER GOAL: "{goal}"
        
        Analyze the screenshot and decide the next step(s).
        Return ONLY the JSON. No markdown formatting.
        """
        
        content = [prompt]
        if screenshot_bytes:
            from PIL import Image
            import io
            image = Image.open(io.BytesIO(screenshot_bytes))
            content.append(image)
        
        try:
            response = self.model.generate_content(content)
            
            # clean response
            text = response.text.strip()
            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "")
            elif text.startswith("```"):
                text = text.replace("```", "")
                
            try:
                data = json.loads(text)
                # Validate structure
                if not isinstance(data, dict):
                    return {"error": "Invalid response format"}
                if "completed" not in data or "actions" not in data:
                    return {"error": "Missing required fields"}
                return data
            except json.JSONDecodeError:
                 return {"error": f"Invalid JSON: {text}"}
        except Exception as e:
            return {"error": f"Gemini Error: {str(e)}"}
