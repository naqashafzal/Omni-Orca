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
            print(f"DEBUG: Sending request to Ollama... (Model: {self.model_name})")
            response = requests.post(url, json=payload, timeout=600)
            print(f"DEBUG: Ollama response status: {response.status_code}")
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
            from PIL import Image
            import io
            
            # Resize image for performance
            try:
                img = Image.open(io.BytesIO(screenshot_bytes))
                img.thumbnail((1024, 1024)) # Resize to max 1024x1024, preserving aspect ratio
                
                # Convert back to bytes
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG", quality=70)
                image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                print(f"DEBUG: Image resized to {img.size}")
            except Exception as e:
                print(f"DEBUG: Image resize failed: {e}")
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

    def test_connection(self):
        """Test connection to Ollama server"""
        import requests
        try:
            # Try to list tags (models) to verify connection
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                return True, "Connection Successful"
            else:
                return False, f"Server returned status {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "Connection Refused. Is Ollama running?"
        except Exception as e:
            return False, f"Error: {str(e)}"


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

    def test_connection(self):
        """Test connection for the current provider"""
        if not self.provider:
            return False, "No provider configured"
        
        if hasattr(self.provider, "test_connection"):
            return self.provider.test_connection()
        
        # Fallback for providers without explicit test (like Gemini where we just try generation)
        return True, "Connection assumed OK (No test method)"
