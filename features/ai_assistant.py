# Copyright 2026 Bailey Beber and Soumalya Das
#
# Licensed under the Apache License, Version 2.0 (the "License")

"""
AI Assistant for Void editor using Google Gemini API.
Supports code generation, refactoring, debugging, and documentation.
"""

import os
import threading
from typing import Callable, Optional


SYSTEM_PROMPT = """You are Void AI, an expert programming assistant integrated into the Void terminal code editor.
You help developers with:
- Code generation and completion
- Refactoring suggestions  
- Debugging assistance
- Documentation generation
- Code explanation

Be concise, accurate, and helpful. Format code with markdown code blocks."""


class AIAssistant:
    def __init__(self, config: dict):
        self.config = config
        self._client = None
        self._available = False
        self._mcp_enabled = config.get("mcp_enabled", False)
        self._init_client()

    def _init_client(self):
        api_key = self.config.get("gemini_api_key", "") or os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            self._available = False
            return
        try:
            from google import genai
            self._client = genai.Client(api_key=api_key)
            self._available = True
        except ImportError:
            self._available = False
        except Exception:
            self._available = False

    def reload(self, config: dict):
        self.config = config
        self._mcp_enabled = config.get("mcp_enabled", False)
        self._init_client()

    @property
    def available(self) -> bool:
        return self._available and self.config.get("ai_enabled", True)

    def ask(self, prompt: str, context: str = "", callback: Optional[Callable] = None) -> str:
        """
        Ask the AI a question. If callback is provided, streams response chunks to it.
        Returns full response text.
        """
        if not self.available:
            msg = "AI not available. Set gemini_api_key in settings (:settings) or GEMINI_API_KEY env var."
            if callback:
                callback(msg, done=True)
            return msg

        full_prompt = prompt
        if context:
            full_prompt = f"Context (current file content):\n```\n{context}\n```\n\n{prompt}"

        if callback:
            thread = threading.Thread(
                target=self._stream_ask,
                args=(full_prompt, callback),
                daemon=True,
            )
            thread.start()
            return ""
        else:
            return self._sync_ask(full_prompt)

    def _sync_ask(self, prompt: str) -> str:
        try:
            from google import genai
            from google.genai import types
            response = self._client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
            )
            return response.text or ""
        except Exception as e:
            return f"[AI Error: {e}]"

    def _stream_ask(self, prompt: str, callback: Callable):
        try:
            from google import genai
            from google.genai import types
            result = []
            for chunk in self._client.models.generate_content_stream(
                model="gemini-2.0-flash",
                contents=prompt,
            ):
                if chunk.text:
                    result.append(chunk.text)
                    callback(chunk.text, done=False)
            callback("", done=True)
        except Exception as e:
            callback(f"\n[AI Error: {e}]", done=True)

    def explain_code(self, code: str, callback=None) -> str:
        return self.ask(f"Explain this code:\n```\n{code}\n```", callback=callback)

    def suggest_refactor(self, code: str, callback=None) -> str:
        return self.ask(
            f"Suggest refactoring improvements for this code:\n```\n{code}\n```",
            callback=callback
        )

    def debug_code(self, code: str, error: str = "", callback=None) -> str:
        prompt = f"Help debug this code:\n```\n{code}\n```"
        if error:
            prompt += f"\n\nError:\n{error}"
        return self.ask(prompt, callback=callback)

    def generate_docs(self, code: str, callback=None) -> str:
        return self.ask(
            f"Generate documentation/docstrings for this code:\n```\n{code}\n```",
            callback=callback
        )
