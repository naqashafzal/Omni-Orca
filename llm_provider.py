"""
LLM Provider Abstraction Layer
Supports multiple LLM backends: Gemini, Ollama, OpenAI, etc.
"""

import json
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Base class for LLM providers"""
    
    @abstractmethod
    def interpret_command(self, user_text, screenshot_bytes=None, mode="GENERAL"):
        """
        Interpret a user command and return action(s).
        Returns: list of action dicts or dict with error
        """
        pass
    
    @abstractmethod
    def autopilot_step(self, goal, screenshot_bytes=None):
        """
        Auto-pilot mode: observe and decide next action.
        Returns: {"completed": bool, "reasoning": str, "actions": []}
        """
        pass


class GeminiProvider(LLMProvider):
    """Google Gemini AI Provider"""
    
    def __init__(self, api_key):
        import google.generativeai as genai
        from prompts import SYSTEM_PROMPTS
        
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.prompts = SYSTEM_PROMPTS
    
    def interpret_command(self, user_text, screenshot_bytes=None, mode="GENERAL"):
        base_prompt = self.prompts.get(mode, self.prompts["GENERAL"])
        
        prompt = f"""
        {base_prompt}

        ⚠️ IMPORTANT: If the command requires multiple steps (like "search for X"), 
        return ALL steps needed to complete the task, not just the first one!
        
        For example, "search for X on Google" needs:
        1. navigate to Google
        2. click search box
        3. type the search term
        4. press Enter
        
        Task: Translate this command into valid JSON.
        Command: "{user_text}"
        
        Return ONLY the JSON LIST. No markdown formatting.
        """
        
        content = [prompt]
        if screenshot_bytes:
            from PIL import Image
            import io
            image = Image.open(io.BytesIO(screenshot_bytes))
            content.append(image)
        
        try:
            response = self.model.generate_content(content)
            text = response.text.strip()
            
            # Clean markdown
            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "")
            elif text.startswith("```"):
                text = text.replace("```", "")
            
            try:
                data = json.loads(text)
                # Ensure list format
                if isinstance(data, dict):
                    return [data]
                elif isinstance(data, list):
                    return data
                else:
                    return {"error": "Invalid JSON format"}
            except json.JSONDecodeError:
                return {"error": f"Invalid JSON: {text}"}
        except Exception as e:
            return {"error": f"Gemini Error: {str(e)}"}
    
    def autopilot_step(self, goal, screenshot_bytes=None):
        prompt = f"""
        {self.prompts["AUTOPILOT"]}

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
            text = response.text.strip()
            
            # Clean markdown
            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "")
            elif text.startswith("```"):
                text = text.replace("```", "")
            
            try:
                data = json.loads(text)
                if not isinstance(data, dict):
                    return {"error": "Invalid response format"}
                if "completed" not in data or "actions" not in data:
                    return {"error": "Missing required fields"}
                return data
            except json.JSONDecodeError:
                return {"error": f"Invalid JSON: {text}"}
        except Exception as e:
            return {"error": f"Gemini Error: {str(e)}"}


class OllamaProvider(LLMProvider):
    """Local Ollama LLM Provider"""
    
    def __init__(self, model_name="llava:latest", base_url="http://localhost:11434"):
        from prompts import SYSTEM_PROMPTS
        
        self.model_name = model_name
        self.base_url = base_url
        self.prompts = SYSTEM_PROMPTS
    
    def _call_ollama(self, prompt, image_base64=None):
        """Call Ollama API using chat endpoint"""
        import requests
        
        url = f"{self.base_url}/api/chat"
        
        # Build messages array
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        # Add image if provided
        if image_base64:
            messages[0]["images"] = [image_base64]
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "format": "json"
        }
        
        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            result = response.json()
            # Extract message content from chat response
            message = result.get("message", {})
            return message.get("content", "")
        except requests.exceptions.ConnectionError:
            return {"error": "Cannot connect to Ollama. Is it running?"}
        except requests.exceptions.Timeout:
            return {"error": "Ollama request timed out"}
        except Exception as e:
            return {"error": f"Ollama Error: {str(e)}"}
    
    def interpret_command(self, user_text, screenshot_bytes=None, mode="GENERAL"):
        base_prompt = self.prompts.get(mode, self.prompts["GENERAL"])
        
        prompt = f"""
        {base_prompt}

        Task: Translate this command into valid JSON.
        Command: "{user_text}"
        
        Return ONLY the JSON array. No markdown, no explanation.
        """
        
        image_base64 = None
        if screenshot_bytes:
            import base64
            image_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        
        response_text = self._call_ollama(prompt, image_base64)
        
        if isinstance(response_text, dict) and "error" in response_text:
            return response_text
        
        try:
            data = json.loads(response_text)
            if isinstance(data, dict):
                return [data]
            elif isinstance(data, list):
                return data
            else:
                return {"error": "Invalid JSON format"}
        except json.JSONDecodeError:
            return {"error": f"Invalid JSON from Ollama: {response_text}"}
    
    def autopilot_step(self, goal, screenshot_bytes=None):
        prompt = f"""
        {self.prompts["AUTOPILOT"]}

        USER GOAL: "{goal}"
        
        Analyze the screenshot and decide the next step(s).
        Return ONLY the JSON object. No markdown, no explanation.
        """
        
        image_base64 = None
        if screenshot_bytes:
            import base64
            image_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        
        response_text = self._call_ollama(prompt, image_base64)
        
        if isinstance(response_text, dict) and "error" in response_text:
            return response_text
        
        try:
            data = json.loads(response_text)
            if not isinstance(data, dict):
                return {"error": "Invalid response format"}
            if "completed" not in data or "actions" not in data:
                return {"error": "Missing required fields"}
            return data
        except json.JSONDecodeError:
            return {"error": f"Invalid JSON from Ollama: {response_text}"}


class LLMClient:
    """Unified LLM client that can use different providers"""
    
    def __init__(self):
        self.provider = None
        self.provider_type = "none"
    
    def configure_gemini(self, api_key):
        """Configure to use Google Gemini"""
        self.provider = GeminiProvider(api_key)
        self.provider_type = "gemini"
        return True
    
    def configure_ollama(self, model_name="llava:latest", base_url="http://localhost:11434"):
        """Configure to use local Ollama"""
        self.provider = OllamaProvider(model_name, base_url)
        self.provider_type = "ollama"
        return True
    
    def is_configured(self):
        """Check if any provider is configured"""
        return self.provider is not None
    
    def interpret_command(self, user_text, screenshot_bytes=None, mode="GENERAL"):
        """Interpret a command using the configured provider"""
        if not self.provider:
            return {"error": "No LLM provider configured"}
        return self.provider.interpret_command(user_text, screenshot_bytes, mode)
    
    def autopilot_step(self, goal, screenshot_bytes=None):
        """Execute one auto-pilot step using the configured provider"""
        if not self.provider:
            return {"error": "No LLM provider configured"}
        return self.provider.autopilot_step(goal, screenshot_bytes)
    
    def get_provider_name(self):
        """Get the name of the current provider"""
        return self.provider_type
