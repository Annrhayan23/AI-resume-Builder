import os
import json
from typing import Optional, Dict, Any
from backend.config import load_settings

class AIService:
    def __init__(self):
        self._client = None
        self._model = "gemini-2.5-flash"
        self._init_client()

    def _init_client(self):
        settings = load_settings()
        api_key = settings.get("gemini_api_key") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self._model = settings.get("gemini_model") or "gemini-2.5-flash"
        if api_key:
            try:
                from google import genai
                self._client = genai.Client(api_key=api_key)
            except Exception as e:
                print(f"Failed to initialize Gemini Client: {e}")
                self._client = None
        else:
            self._client = None

    def is_available(self) -> bool:
        self._init_client()
        return self._client is not None

    def generate_text(self, prompt: str, system_instruction: str = "") -> Optional[str]:
        self._init_client()
        if not self._client:
            return None
        try:
            from google.genai import types
            config = types.GenerateContentConfig(
                temperature=0.3,
                system_instruction=system_instruction if system_instruction else None,
            )
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=config
            )
            return response.text
        except Exception as e:
            print(f"Gemini generation error: {e}")
            return None

    def generate_json(self, prompt: str, system_instruction: str = "") -> Optional[Dict[str, Any]]:
        self._init_client()
        if not self._client:
            return None
        try:
            from google.genai import types
            config = types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
                system_instruction=system_instruction if system_instruction else None,
            )
            response = self._client.models.generate_content(
                model=self._model,
                contents=prompt,
                config=config
            )
            if response.text:
                return json.loads(response.text)
        except Exception as e:
            print(f"Gemini JSON generation error: {e}")
        return None

ai_service = AIService()
