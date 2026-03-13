# Copyright 2026 Bailey Beber and Soumalya Das
#
# Licensed under the Apache License, Version 2.0 (the "License")

"""
Model Context Protocol (MCP) server for Void editor.
Runs a local HTTP server that exposes editor context and AI responses
to external tools.

Endpoint:
    POST /prompt  {"prompt": "...", "context": "..."}
    -> {"response": "AI answer", "status": "ok"}

    GET /context
    -> {"file": "...", "content": "...", "cursor": [...], "status": "ok"}
"""

import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Callable


class MCPHandler(BaseHTTPRequestHandler):
    """HTTP request handler for MCP protocol."""

    def log_message(self, format, *args):
        pass  # suppress default logging

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/context":
            ctx = self.server.mcp_server.get_context()
            self._send_json({"status": "ok", **ctx})
        elif self.path == "/status":
            self._send_json({
                "status": "ok",
                "name": "Void MCP Server",
                "version": "0.3.0",
                "authors": "Bailey Beber and Soumalya Das",
            })
        else:
            self._send_json({"status": "error", "message": "Not found"}, 404)

    def do_POST(self):
        if self.path == "/prompt":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
                prompt = data.get("prompt", "")
                context = data.get("context", "")
                if not prompt:
                    self._send_json({"status": "error", "message": "prompt required"}, 400)
                    return
                ai = self.server.mcp_server.ai_assistant
                if ai and ai.available:
                    response = ai.ask(prompt, context=context)
                    self._send_json({"status": "ok", "response": response})
                else:
                    self._send_json({
                        "status": "error",
                        "message": "AI not configured. Set GEMINI_API_KEY.",
                    }, 503)
            except json.JSONDecodeError:
                self._send_json({"status": "error", "message": "Invalid JSON"}, 400)
        else:
            self._send_json({"status": "error", "message": "Not found"}, 404)


class MCPServer:
    DEFAULT_PORT = 7700

    def __init__(self, ai_assistant=None, port: int = DEFAULT_PORT):
        self.ai_assistant = ai_assistant
        self.port = port
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._context = {}

    def update_context(self, file: str = "", content: str = "", cursor=None):
        self._context = {
            "file": file,
            "content": content,
            "cursor": list(cursor) if cursor else [0, 0],
        }

    def get_context(self) -> dict:
        return dict(self._context)

    def start(self):
        if self._running:
            return
        try:
            self._server = HTTPServer(("127.0.0.1", self.port), MCPHandler)
            self._server.mcp_server = self
            self._running = True
            self._thread = threading.Thread(
                target=self._server.serve_forever,
                daemon=True,
            )
            self._thread.start()
        except OSError:
            self._running = False

    def stop(self):
        if self._server:
            self._server.shutdown()
            self._running = False

    @property
    def running(self) -> bool:
        return self._running

    @property
    def address(self) -> str:
        return f"http://127.0.0.1:{self.port}"
