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
                
            return json.loads(text)
        except Exception as e:
            return {"error": f"Gemini Error: {str(e)}"}
