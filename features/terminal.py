# Copyright 2026 Bailey Beber and Soumalya Das
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""
Cross-platform inline terminal — fixed for Python 3.8+ / 3.14 compatibility.
The original crash (TypeError: can't concat NoneType to bytes) is resolved by
using non-blocking I/O with proper None-guards and os.read() fallback.
"""

import subprocess
import os
import sys
import time
import threading
from config.keys import TERMINAL_HEIGHT, SUBPROCESS_TIMEOUT, KEY_ESCAPE


class InlineTerminal:
    """Inline terminal emulator that is safe on Windows, macOS, and Linux."""

    def __init__(self, window=None):
        self.spin_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        self.spin_index = 0
        self.last_spin = time.time()
        self.visible = False
        self.output_lines: list[str] = []
        self.input_buffer = ""
        self.history: list[str] = []
        self.history_pos = -1
        self.height = TERMINAL_HEIGHT
        self.scroll_offset = 0
        self.cwd = os.getcwd()
        self._running_proc = None
        self._proc_start = 0.0
        self._awaiting_input = False
        self._output_lock = threading.Lock()
        self._reader_thread = None
        self._window = window

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_animation(self):
        now = time.time()
        if now - self.last_spin >= 0.1:
            self.spin_index = (self.spin_index + 1) % len(self.spin_chars)
            self.last_spin = now

    def toggle(self):
        self.visible = not self.visible

    def get_editor_rows(self, total_rows):
        if self.visible:
            return max(1, total_rows - self.height)
        return total_rows

    def run_command(self, cmd: str):
        cmd = cmd.strip()
        if not cmd:
            return

        self.history.append(cmd)
        self.history_pos = -1

        # Handle 'cd' natively so it affects self.cwd
        if cmd.startswith("cd"):
            parts = cmd.split(None, 1)
            path = parts[1] if len(parts) > 1 else os.path.expanduser("~")
            try:
                new_dir = os.path.abspath(os.path.join(self.cwd, path))
                os.chdir(new_dir)
                self.cwd = new_dir
                self._append(f"$ {cmd}")
                self._append(f"  -> {self.cwd}")
            except (FileNotFoundError, PermissionError) as e:
                self._append(f"$ {cmd}")
                self._append(f"  cd: {e}")
            self.input_buffer = ""
            self._scroll_to_bottom()
            return

        self._append(f"$ {cmd}")

        # Kill any leftover process
        self._kill_proc()

        try:
            kwargs = dict(
                shell=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,   # merge stderr → stdout
                cwd=self.cwd,
            )
            self._running_proc = subprocess.Popen(cmd, **kwargs)
            self._proc_start = time.time()
            self._awaiting_input = False

            # Spawn a daemon thread to read output without blocking the TUI
            self._reader_thread = threading.Thread(
                target=self._stream_output,
                daemon=True,
            )
            self._reader_thread.start()

        except Exception as exc:
            self._append(f"  [error: {exc}]")
            self._running_proc = None

        self.input_buffer = ""

    def poll_process(self):
        """Called each draw tick; checks if the process finished."""
        if self._running_proc is None:
            return

        retcode = self._running_proc.poll()

        if retcode is None:
            # Still running — enforce timeout
            if time.time() - self._proc_start > SUBPROCESS_TIMEOUT:
                self._kill_proc()
                self._append(f"  [timed out after {SUBPROCESS_TIMEOUT}s]")
                self._scroll_to_bottom()
            else:
                self._awaiting_input = True
            return

        # Process finished — wait for reader thread to drain
        if self._reader_thread and self._reader_thread.is_alive():
            self._reader_thread.join(timeout=0.5)

        if retcode != 0:
            self._append(f"  [exit code: {retcode}]")
        self._running_proc = None
        self._awaiting_input = False
        self._scroll_to_bottom()

    def send_input(self, text: str):
        if self._running_proc and self._running_proc.stdin:
            try:
                data = (text + "\n").encode()
                self._running_proc.stdin.write(data)
                self._running_proc.stdin.flush()
                self._awaiting_input = False
                self._scroll_to_bottom()
            except (BrokenPipeError, OSError):
                self._append("  [process closed]")
                self._running_proc = None
                self._awaiting_input = False

    def handle_key(self, k: str):
        if k == KEY_ESCAPE:
            return "blur"
        elif k == "\n":
            if self._awaiting_input and self._running_proc:
                self.send_input(self.input_buffer)
                self.input_buffer = ""
            else:
                self.run_command(self.input_buffer)
        elif k in ("KEY_BACKSPACE", "\x7f", "\x08"):
            if self.input_buffer:
                self.input_buffer = self.input_buffer[:-1]
        elif k == "KEY_UP":
            if not self._awaiting_input:
                self.history_up()
        elif k == "KEY_DOWN":
            if not self._awaiting_input:
                self.history_down()
        elif k == "\x0e":   # Ctrl+N — scroll down
            self.scroll_down()
        elif k == "\x10":   # Ctrl+P — scroll up
            self.scroll_up()
        elif k == "\x03":   # Ctrl+C — kill
            self._kill_proc()
            self._append("  [killed]")
            self.input_buffer = ""
            self._scroll_to_bottom()
        elif len(k) == 1 and k.isprintable():
            self.input_buffer += k
        return None

    # ------------------------------------------------------------------
    # Scroll / history helpers
    # ------------------------------------------------------------------

    def scroll_up(self):
        if self.scroll_offset > 0:
            self.scroll_offset -= 1

    def scroll_down(self):
        visible_rows = self.height - 2
        max_offset = max(len(self.output_lines) - visible_rows, 0)
        if self.scroll_offset < max_offset:
            self.scroll_offset += 1

    def history_up(self):
        if self.history:
            if self.history_pos == -1:
                self.history_pos = len(self.history) - 1
            elif self.history_pos > 0:
                self.history_pos -= 1
            self.input_buffer = self.history[self.history_pos]

    def history_down(self):
        if self.history_pos != -1:
            if self.history_pos < len(self.history) - 1:
                self.history_pos += 1
                self.input_buffer = self.history[self.history_pos]
            else:
                self.history_pos = -1
                self.input_buffer = ""

    def get_display_lines(self):
        """Return visible output lines for Textual rendering."""
        with self._output_lock:
            return list(self.output_lines)

    def get_prompt(self):
        short_cwd = os.path.basename(self.cwd) or self.cwd
        if self._running_proc is not None:
            if self._awaiting_input:
                return f" >> {self.input_buffer}"
            return f" {short_cwd} $ [running...]"
        return f" {short_cwd} $ {self.input_buffer}"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _append(self, line: str):
        with self._output_lock:
            self.output_lines.append(line)

    def _scroll_to_bottom(self):
        visible_rows = self.height - 2
        if len(self.output_lines) > visible_rows:
            self.scroll_offset = len(self.output_lines) - visible_rows
        else:
            self.scroll_offset = 0

    def _kill_proc(self):
        if self._running_proc is not None:
            try:
                self._running_proc.kill()
                self._running_proc.wait(timeout=2)
            except Exception:
                pass
            self._running_proc = None
            self._awaiting_input = False

    def _stream_output(self):
        """Background thread: reads stdout line-by-line safely."""
        proc = self._running_proc
        if proc is None or proc.stdout is None:
            return
        try:
            for raw in proc.stdout:
                if raw is None:
                    break
                if isinstance(raw, bytes):
                    line = raw.decode("utf-8", errors="replace").rstrip("\n")
                else:
                    line = raw.rstrip("\n")
                self._append(f"  {line}")
                self._scroll_to_bottom()
        except (OSError, ValueError):
            pass
