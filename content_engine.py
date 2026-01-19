import requests
import io
from PIL import Image
import os
import time

class ContentGenerator:
    def __init__(self, llm_client):
        self.llm = llm_client

    def generate_text(self, topic, platform):
        """
        Generate a social media post using the configured LLM.
        """
        if not self.llm.is_configured():
            return "Error: AI not configured. Please set up API key or Ollama first."

        prompt = f"""
        You are a social media expert. Write a viral, engaging post for {platform} about: "{topic}".
        
        Guidelines:
        - Use appropriate emojis.
        - Include 3-5 relevant hashtags.
        - Keep it concise and punchy.
        - For Twitter: under 280 chars.
        - For LinkedIn: professional but engaging.
        - For Instagram: visual description + caption.
        
        Return ONLY the post text.
        """
        
        # We reuse the interpret_command method for simplicity, or we could add a raw generate method
        # But interpret_command expects JSON. Let's use the provider directly if possible, 
        # or trick interpret_command. 
        # Actually, let's add a simple 'generate_text' method to LLMClient later.
        # For now, we'll try to use the provider's internal methods if we can, 
        # or just ask for JSON wrapping to be safe and unwrap it.
        
        # Better approach: Add generate_text to LLMClient. 
        # But to avoid modifying LLMClient right now, let's use a JSON wrapper hack.
        
        json_prompt = prompt + "\n\nReturn response as JSON: {\"post\": \"...content...\"}"
        
        try:
            response = self.llm.interpret_command(json_prompt, mode="GENERAL")
            if isinstance(response, list) and len(response) > 0:
                return response[0].get("post", "Error parsing response")
            elif isinstance(response, dict):
                return response.get("post", str(response))
            return str(response)
        except Exception as e:
            return f"Generation Error: {e}"

    def generate_image(self, topic):
        """
        Generate an image using Pollinations.ai (No API key required).
        """
        # 1. Refine prompt for image generation
        image_prompt = f"high quality, futuristic, cinematic, 8k render, {topic}"
        
        # 2. Call Pollinations
        encoded_prompt = requests.utils.quote(image_prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
        
        print(f"Fetching image from: {url}")
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            image_bytes = response.content
            image = Image.open(io.BytesIO(image_bytes))
            return image
        except Exception as e:
            print(f"Image Gen Error: {e}")
            return None

    def save_assets(self, text, image, topic):
        """Save generated content to a folder."""
        safe_topic = "".join([c for c in topic if c.isalnum() or c in (' ', '-', '_')]).strip().replace(' ', '_')[:20]
        timestamp = int(time.time())
        folder = f"content_{safe_topic}_{timestamp}"
        os.makedirs(folder, exist_ok=True)
        
        # Save text
        with open(f"{folder}/post.txt", "w", encoding="utf-8") as f:
            f.write(text)
            
        # Save image
        if image:
            image.save(f"{folder}/image.png")
            
        return folder
