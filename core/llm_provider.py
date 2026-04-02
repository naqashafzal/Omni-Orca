"""
LLM Provider Abstraction Layer
Supports multiple LLM backends: Gemini, Ollama, OpenAI, OpenRouter.
"""

import json
import requests
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

    def generate_text(self, prompt: str) -> str:
        """
        Generate plain-text response. Default implementation — subclasses should override.
        """
        return f"[generate_text not implemented for {type(self).__name__}]"

    @abstractmethod
    def execute_agent_prompt(self, prompt_text: str, screenshot_bytes=None) -> dict:
        """
        Execute a raw agent prompt (for the Agentic Orchestrator).
        Returns a parsed JSON dictionary.
        """
        pass


class GeminiProvider(LLMProvider):
    """Google Gemini AI Provider"""

    def __init__(self, api_key):
        import google.generativeai as genai
        from core.prompts import SYSTEM_PROMPTS

        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.prompts = SYSTEM_PROMPTS

    def generate_text(self, prompt: str) -> str:
        """Generate plain text response from Gemini."""
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"[Gemini Error: {e}]"

    def execute_agent_prompt(self, prompt_text: str, screenshot_bytes=None) -> dict:
        content = [prompt_text]
        if screenshot_bytes:
            from PIL import Image
            import io
            content.append(Image.open(io.BytesIO(screenshot_bytes)))
        try:
            response = self.model.generate_content(content)
            text = response.text.strip()
            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "")
            elif text.startswith("```"):
                text = text.replace("```", "")
            
            import json
            return json.loads(text.strip())
        except Exception as e:
            return {"error": f"Gemini Execution Error: {e}"}

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
        from core.prompts import SYSTEM_PROMPTS

        self.model_name = model_name
        self.base_url = base_url
        self.prompts = SYSTEM_PROMPTS

    def _call_ollama(self, prompt, image_base64=None):
        """Call Ollama API using generate endpoint for broader compatibility"""
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        
        if image_base64:
            payload["images"] = [image_base64]

        try:
            response = requests.post(url, json=payload, timeout=600)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")
        except requests.exceptions.HTTPError as e:
            try:
                err_detail = e.response.json().get("error", "")
                if err_detail:
                    return {"error": f"Ollama Error: {err_detail} (Did you download the model? Try 'ollama run {self.model_name}')"}
            except Exception:
                pass
            return {"error": f"Ollama HTTP Error: {str(e)}"}
        except requests.exceptions.ConnectionError:
            return {"error": "Cannot connect to Ollama. Is it running?"}
        except requests.exceptions.Timeout:
            return {"error": "Ollama request timed out"}
        except Exception as e:
            return {"error": f"Ollama Error: {str(e)}"}

    def generate_text(self, prompt: str) -> str:
        """Generate plain text using Ollama (without JSON format)."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False
        }
        try:
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "").strip()
        except requests.exceptions.HTTPError as e:
            try:
                err_detail = e.response.json().get("error", "")
                if err_detail:
                    return f"[Ollama Error: {err_detail} - Did you pull the model?]"
            except Exception:
                pass
            return f"[Ollama HTTP Error: {str(e)}]"
        except Exception as e:
            return f"[Ollama Error: {e}]"

    def execute_agent_prompt(self, prompt_text: str, screenshot_bytes=None) -> dict:
        image_base64 = None
        if screenshot_bytes:
            import base64
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(screenshot_bytes))
            img.thumbnail((1024, 1024))
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG", quality=70)
            image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
        try:
            response_text = self._call_ollama(prompt_text, image_base64)
            if isinstance(response_text, dict) and "error" in response_text:
                return response_text
                
            text = str(response_text).strip()
            if text.startswith("```json"):
                text = text.replace("```json", "").replace("```", "")
            elif text.startswith("```"):
                text = text.replace("```", "")
                
            import json
            return json.loads(text.strip())
        except Exception as e:
            return {"error": f"Ollama Execution Error: {e}"}

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

            try:
                img = Image.open(io.BytesIO(screenshot_bytes))
                img.thumbnail((1024, 1024))
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG", quality=70)
                image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            except Exception as e:
                print(f"DEBUG: Image resize failed: {e}")
                image_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')

        response_text = self._call_ollama(prompt, image_base64)

        if isinstance(response_text, dict) and "error" in response_text:
            return response_text

        import re
        text = str(response_text).strip()
        
        # Regex to find JSON arrays
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            text = match.group(0)
            
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return [data]
            elif isinstance(data, list):
                return data
            else:
                return {"error": "Invalid JSON format"}
        except json.JSONDecodeError:
            return {"error": f"Invalid JSON from Ollama: {text}"}

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

        import re
        text = str(response_text).strip()
        
        # Regex to find JSON object
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            text = match.group(0)

        try:
            data = json.loads(text)
            if not isinstance(data, dict):
                return {"error": "Invalid response format"}
            if "completed" not in data or "actions" not in data:
                return {"error": "Missing required fields"}
            return data
        except json.JSONDecodeError:
            return {"error": f"Invalid JSON from Ollama: {text}"}

    def execute_agent_prompt(self, prompt_text: str, screenshot_bytes=None) -> dict:
        image_base64 = None
        if screenshot_bytes:
            import base64
            image_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')

        response_text = self._call_ollama(prompt_text, image_base64)
        if isinstance(response_text, dict) and "error" in response_text:
            return response_text

        import re
        text = str(response_text).strip()
        # Clean markdown
        if "```json" in text:
            text = text.split("```json")[-1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].strip()

        # Robust JSON extraction via regex if still wrapped
        if not text.startswith("{"):
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                text = match.group(0)

        try:
            return json.loads(text)
        except Exception as e:
            return {"error": f"Agent Execution Error: {str(e)}"}

    def test_connection(self):
        """Test connection to Ollama server"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                return True, "Connection Successful"
            else:
                return False, f"Server returned status {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "Connection Refused. Is Ollama running?"
        except Exception as e:
            return False, f"Error: {str(e)}"


class OpenRouterProvider(LLMProvider):
    """OpenRouter AI Provider — OpenAI-compatible API supporting 100+ models"""

    ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key, model="google/gemini-2.0-flash-001"):
        from core.prompts import SYSTEM_PROMPTS
        self.api_key = api_key
        self.model = model
        self.prompts = SYSTEM_PROMPTS

    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/neural-automater",
            "X-OpenRouter-Title": "Neural Automater",
        }

    def _call(self, messages) -> str:
        """Send a chat/completions request to OpenRouter. Returns raw text."""
        payload = {
            "model": self.model,
            "messages": messages,
        }
        try:
            resp = requests.post(
                self.ENDPOINT,
                headers=self._get_headers(),
                data=json.dumps(payload),
                timeout=120
            )
            resp.raise_for_status()
            data = resp.json()
            if "error" in data:
                err_msg = data["error"].get("message", str(data["error"]))
                return f"ERROR: OpenRouter Error Payload: {err_msg}"
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.ConnectionError:
            return "ERROR: Cannot connect to OpenRouter. Check internet."
        except requests.exceptions.Timeout:
            return "ERROR: OpenRouter request timed out."
        except requests.exceptions.HTTPError as e:
            # Try to extract detail from response
            try:
                detail = resp.json().get("error", {}).get("message", str(e))
            except Exception:
                detail = str(e)
            return f"ERROR: OpenRouter HTTP {resp.status_code} - {detail}"
        except Exception as e:
            return f"ERROR: {str(e)}"

    def generate_text(self, prompt: str) -> str:
        """Generate plain text from OpenRouter."""
        messages = [{"role": "user", "content": prompt}]
        result = self._call(messages)
        return result

    def _build_user_message(self, prompt_text, screenshot_bytes=None):
        """Build a user message, optionally with an inline image."""
        if screenshot_bytes:
            import base64
            b64 = base64.b64encode(screenshot_bytes).decode("utf-8")
            return {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                    },
                ],
            }
        return {"role": "user", "content": prompt_text}

    def interpret_command(self, user_text, screenshot_bytes=None, mode="GENERAL"):
        base_prompt = self.prompts.get(mode, self.prompts["GENERAL"])
        prompt = (
            f"{base_prompt}\n\n"
            f"Task: Translate this command into valid JSON.\n"
            f"Command: \"{user_text}\"\n\n"
            f"Return ONLY the JSON LIST. No markdown formatting."
        )
        messages = [self._build_user_message(prompt, screenshot_bytes)]
        result = self._call(messages)

        if result.startswith("ERROR:") and screenshot_bytes:
            messages = [{"role": "user", "content": prompt}]
            result = self._call(messages)

        if result.startswith("ERROR:"):
            return {"error": result}

        text = result.strip()
        if text.startswith("```json"):
            text = text.replace("```json", "").replace("```", "")
        elif text.startswith("```"):
            text = text.replace("```", "")

        try:
            data = json.loads(text)
            if isinstance(data, dict):
                return [data]
            elif isinstance(data, list):
                return data
            return {"error": "Invalid JSON format"}
        except json.JSONDecodeError:
            return {"error": f"Invalid JSON from OpenRouter: {text}"}

    def autopilot_step(self, goal, screenshot_bytes=None):
        prompt = (
            f"{self.prompts['AUTOPILOT']}\n\n"
            f"USER GOAL: \"{goal}\"\n\n"
            f"Analyze the screenshot and decide the next step(s).\n"
            f"Return ONLY the JSON. No markdown formatting."
        )
        messages = [self._build_user_message(prompt, screenshot_bytes)]
        result = self._call(messages)

        if result.startswith("ERROR:") and screenshot_bytes:
            messages = [{"role": "user", "content": prompt}]
            result = self._call(messages)

        if result.startswith("ERROR:"):
            return {"error": result}

        text = result.strip()
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
            return {"error": f"Invalid JSON from OpenRouter: {text}"}

    def execute_agent_prompt(self, prompt_text: str, screenshot_bytes=None) -> dict:
        messages = [self._build_user_message(prompt_text, screenshot_bytes)]
        result = self._call(messages)

        if result.startswith("ERROR:") and screenshot_bytes:
            messages = [{"role": "user", "content": prompt_text}]
            result = self._call(messages)

        if result.startswith("ERROR:"):
            return {"error": result}

        text = result.strip()
        if text.startswith("```json"):
            text = text.replace("```json", "").replace("```", "")
        elif text.startswith("```"):
            text = text.replace("```", "")

        try:
            return json.loads(text)
        except Exception as e:
            return {"error": f"Agent Execution Error: {str(e)}"}

    def test_connection(self):
        """Verify the API key with a minimal request."""
        messages = [{"role": "user", "content": "Reply with the word OK only."}]
        result = self._call(messages)
        if result.startswith("ERROR:"):
            return False, result
        return True, f"Connection Successful — Model: {self.model}"


class LLMClient:
    """Unified LLM client that can use different providers"""

    def __init__(self):
        self.provider: LLMProvider | None = None
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

    def configure_openrouter(self, api_key, model="google/gemini-2.0-flash-001"):
        """Configure to use OpenRouter"""
        self.provider = OpenRouterProvider(api_key, model)
        self.provider_type = "openrouter"
        return True

    def is_configured(self):
        """Check if any provider is configured"""
        return self.provider is not None

    def generate_text(self, prompt: str) -> str:
        """Generate plain text using the configured provider."""
        if not self.provider:
            return "ERROR: No LLM provider configured"
        return self.provider.generate_text(prompt)

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

    def execute_agent_prompt(self, prompt_text: str, screenshot_bytes=None) -> dict:
        """Execute raw agent prompt (JSON object output)"""
        if not self.provider:
            return {"error": "No LLM provider configured"}
        return self.provider.execute_agent_prompt(prompt_text, screenshot_bytes)

    def get_provider_name(self):
        """Get the name of the current provider"""
        return self.provider_type

    def test_connection(self):
        """Test connection for the current provider"""
        if not self.provider:
            return False, "No provider configured"
        if hasattr(self.provider, "test_connection"):
            return self.provider.test_connection()
        return True, "Connection assumed OK (No test method)"
