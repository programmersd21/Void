# Copyright 2026 Bailey Beber and Soumalya Das
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

"""
Void Editor — cross-platform terminal code editor
Authors: Bailey Beber and Soumalya Das  |  Version: 0.3.1

Theme system: themes inject CSS variables via get_css_variables() +
refresh_css() so every UI component updates instantly at runtime.
"""

import os, sys, json, time, random, argparse, threading

from textual.app import App, ComposeResult
from textual.widget import Widget
from textual.widgets import Static, Input, Button, Footer
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.binding import Binding
from textual.screen import Screen, ModalScreen
from textual import events
from textual.message import Message
from rich.text import Text
from rich.markup import escape

from config.settings import settings, save_config, CONFIG_PATH
from features.theme_engine import THEMES, DARK_THEMES, LIGHT_THEMES, get_theme, theme_css_variables
from features.terminal import InlineTerminal
from features.ai_assistant import AIAssistant
from features.mcp_server import MCPServer
from core.buffer import Buffer
from core.tab import Tab, TabManager
from core.editing import save_snapshot, undo, redo, auto_indent
from modes.vim_motions import (handle_vim_motion, reset_pending,
    motion_w, motion_b, motion_G, motion_gg, motion_caret)
from modes.search import search_state
from modes.visual import (visual_state, VisualState,
    visual_delete, visual_yank, visual_change, visual_indent)
from ui.syntax import tokenize_line, detect_language
from config.colors import (COLOR_KEYWORD, COLOR_STRING, COLOR_COMMENT,
    COLOR_NUMBER, COLOR_BUILTIN, COLOR_DECORATOR, COLOR_NORMAL,
    COLOR_DEFINITION, COLOR_FUNC_NAME, COLOR_MATCH_BOOL)

VERSION = "0.3.1"
AUTHORS = "Bailey Beber and Soumalya Das"
RECENT_FILES_PATH = os.path.expanduser("~/.void_recent_files.json")

TIPS = [
    "Use :h for help",
    "Press ESC to enter normal mode  •  i to insert",
    "Use :w to save  •  :q to quit  •  :wq to save & quit",
    "Use :exit or :quit to close the editor safely",
    "Use :ai to open the AI assistant",
    "Use :theme to browse themes  •  :theme name to set directly",
    "Use :settings to configure Void",
    "Use / to search  •  n/N for next/prev match",
    "Ctrl+T toggles the integrated terminal",
    "Ctrl+F opens the fuzzy file finder",
    "dd deletes a line  •  yy yanks  •  p pastes",
    "v for visual  •  V for visual-line  •  Ctrl+V for block",
    "Use :export config.vdtf to export your dotfile settings",
    "Use :ai --mcp=on to start the MCP server on port 7700",
    "gt / gT to cycle tabs",
    "u to undo  •  Ctrl+R to redo",
    "w/b to move word-by-word  •  gg/G for top/bottom",
    "Both dark and light themes available — try :theme",
]

LOGO_LINES = [
    "██╗   ██╗ ██████╗ ██╗██████╗ ",
    "██║   ██║██╔═══██╗██║██╔══██╗",
    "██║   ██║██║   ██║██║██║  ██║",
    "╚██╗ ██╔╝██║   ██║██║██║  ██║",
    " ╚████╔╝ ╚██████╔╝██║██████╔╝",
    "  ╚═══╝   ╚═════╝ ╚═╝╚═════╝ ",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_recent_files() -> list:
    try:
        with open(RECENT_FILES_PATH) as f:
            files = json.load(f)
        return [p for p in files if os.path.exists(p)][:settings.get("max_recent_display", 8)]
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def add_recent_file(fp: str):
    fp = os.path.abspath(fp)
    try:
        with open(RECENT_FILES_PATH) as f:
            files = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        files = []
    if fp in files:
        files.remove(fp)
    files.insert(0, fp)
    with open(RECENT_FILES_PATH, "w") as f:
        json.dump(files[:settings.get("max_recent_files", 20)], f)


def _color_to_rich(color_id: int, theme: dict) -> str:
    return {
        COLOR_KEYWORD:    theme.get("keyword_color",  "#ff79c6"),
        COLOR_STRING:     theme.get("string_color",   "#a6e22e"),
        COLOR_COMMENT:    theme.get("comment_color",  "#6272a4") + " italic",
        COLOR_NUMBER:     theme.get("number_color",   "#ae81ff"),
        COLOR_BUILTIN:    theme.get("function_color", "#66d9e8"),
        COLOR_DECORATOR:  theme.get("orange",         "#ffb86c"),
        COLOR_NORMAL:     theme.get("foreground",     "#f8f8f2"),
        COLOR_DEFINITION: theme.get("purple",         "#bd93f9") + " bold",
        COLOR_FUNC_NAME:  theme.get("function_color", "#66d9e8") + " bold",
        COLOR_MATCH_BOOL: theme.get("yellow",         "#f1fa8c") + " bold",
    }.get(color_id, theme.get("foreground", "#f8f8f2"))


# ── Cursor & Window ───────────────────────────────────────────────────────────

class Cursor:
    def __init__(self, row=0, col=0, col_hint=None):
        self.row = row
        self._col = col
        self._col_hint = col if col_hint is None else col_hint

    @property
    def col(self): return self._col

    @col.setter
    def col(self, col):
        self._col = col
        self._col_hint = col

    def up(self, buf):
        if self.row > 0:
            self.row -= 1; self._clamp_col(buf)

    def down(self, buf):
        if self.row < buf.bottom:
            self.row += 1; self._clamp_col(buf)

    def left(self, buf):
        if self.col > 0:
            self.col -= 1
        elif self.row > 0:
            self.row -= 1; self.col = len(buf[self.row])

    def right(self, buf):
        if self.col < len(buf[self.row]):
            self.col += 1
        elif self.row < buf.bottom:
            self.row += 1; self.col = 0

    def _clamp_col(self, buf):
        self._col = min(self._col_hint, len(buf[self.row]))


class Window:
    def __init__(self, n_rows, n_cols, row=0, col=0):
        self.n_rows = n_rows; self.n_cols = n_cols
        self.row = row;       self.col = col

    @property
    def bottom(self): return self.row + self.n_rows - 1

    def up(self, cursor):
        if cursor.row == self.row - 1 and self.row > 0:
            self.row -= 1

    def down(self, buf, cursor):
        if cursor.row == self.bottom + 1 and self.bottom < buf.bottom:
            self.row += 1

    def horizontal_scroll(self, cursor, margin=5, gutter=0):
        usable = self.n_cols - gutter
        if cursor.col - self.col >= usable - margin:
            self.col = cursor.col - usable + margin + 1
        elif cursor.col - self.col < margin and self.col > 0:
            self.col = max(cursor.col - margin, 0)

    def half_page_down(self, buf, cursor):
        a = self.n_rows // 2
        self.row = min(self.row + a, buf.bottom)
        cursor.row = min(cursor.row + a, buf.bottom)
        cursor._clamp_col(buf)

    def half_page_up(self, buf, cursor):
        a = self.n_rows // 2
        self.row = max(self.row - a, 0)
        cursor.row = max(cursor.row - a, 0)
        cursor._clamp_col(buf)

    def translate(self, cursor):
        return cursor.row - self.row, cursor.col - self.col


def _cur_right(win, buf, cur):
    cur.right(buf); win.down(buf, cur); win.horizontal_scroll(cur)

def _cur_left(win, buf, cur):
    cur.left(buf); win.up(cur); win.horizontal_scroll(cur)


# ── Screens ───────────────────────────────────────────────────────────────────

class SplashScreen(Screen):
    BINDINGS = [Binding("q", "do_quit", "Quit"), Binding("escape", "do_open", "Open")]

    def compose(self) -> ComposeResult:
        tip = random.choice(TIPS)
        recent = load_recent_files()
        with Container(id="splash-root"):
            yield Static("\n".join(LOGO_LINES), id="splash-logo")
            yield Static(f"[bold]v{VERSION}[/bold]  ·  [dim]{AUTHORS}[/dim]", id="splash-meta")
            yield Static(f"[italic dim]💡  {escape(tip)}[/italic dim]", id="splash-tip")
            yield Static("", id="splash-gap1")
            if recent:
                yield Static("[bold white]Recent Files[/bold white]", id="rf-hdr")
                for i, fp in enumerate(recent[:8]):
                    yield Static(
                        f"  [bold]{i+1}[/bold]  [cyan]{escape(os.path.basename(fp))}[/cyan]"
                        f"  [dim]{escape(os.path.dirname(fp))}[/dim]",
                        classes="rf-item")
            yield Static("", id="splash-gap2")
            yield Static(
                "[dim][bold]Enter[/bold] new file  ·  [bold]1–8[/bold] open recent  ·  [bold]q[/bold] quit[/dim]",
                id="splash-footer")

    def on_key(self, event: events.Key) -> None:
        k = event.key
        if k.isdigit() and k != "0":
            recent = load_recent_files()
            idx = int(k) - 1
            if idx < len(recent):
                self.app.open_file(recent[idx])
            self.app.pop_screen()
        elif k in ("enter", "space", "escape"):
            self.app.pop_screen()
        elif k == "q":
            self.app.exit()

    def action_do_quit(self): self.app.exit()
    def action_do_open(self): self.app.pop_screen()


class HelpScreen(ModalScreen):
    BINDINGS = [Binding("escape,q", "dismiss", "Close")]

    def compose(self) -> ComposeResult:
        with Container(id="help-root"):
            yield Static(HELP_TEXT, id="help-body")

    def on_key(self, event: events.Key) -> None:
        if event.key in ("escape", "q"):
            self.dismiss()


HELP_TEXT = """\
[bold cyan]Void  —  Keybinding Reference[/bold cyan]

[bold yellow]Modes[/bold yellow]
  [cyan]ESC[/cyan]          Normal mode        [cyan]i / a[/cyan]  Insert mode
  [cyan]v[/cyan]            Visual (char)      [cyan]V[/cyan]      Visual (line)
  [cyan]Ctrl+V[/cyan]       Visual (block)

[bold yellow]Navigation[/bold yellow]
  [cyan]h j k l[/cyan]  Arrows    [cyan]w / b[/cyan]  Word fwd/back
  [cyan]0  $  ^[/cyan]  Start / end / first non-blank
  [cyan]gg  G[/cyan]    Top / bottom       [cyan]Ctrl+D/U[/cyan]  Half page

[bold yellow]Editing[/bold yellow]
  [cyan]dd dw d$ d0 dG dgg[/cyan]  Delete  |  [cyan]yy p P[/cyan]  Yank / paste
  [cyan]x[/cyan]  Delete char      [cyan]o O[/cyan]  Open line below/above
  [cyan]u  Ctrl+R[/cyan]  Undo / redo

[bold yellow]Search[/bold yellow]
  [cyan]/query[/cyan]  Search   [cyan]n / N[/cyan]  Next / prev
  [cyan]/find/replace/g[/cyan]  Replace all   [cyan]/find/replace/gc[/cyan]  Confirm

[bold yellow]Visual Mode[/bold yellow]
  [cyan]d / y / c[/cyan]  Delete / yank / change
  [cyan]> / <[/cyan]  Indent / unindent

[bold yellow]Commands[/bold yellow]
  [cyan]:w[/cyan]           Save               [cyan]:w file[/cyan]  Save as
  [cyan]:q  :q![/cyan]      Quit / force quit  [cyan]:wq[/cyan]  Save & quit
  [cyan]:quit  :exit[/cyan] Same as :q         [cyan]:e file[/cyan]  Open file
  [cyan]:h[/cyan]           This help          [cyan]:settings[/cyan]  Settings
  [cyan]:theme[/cyan]       Pick theme         [cyan]:theme name[/cyan]  Set theme
  [cyan]:ai[/cyan]          AI assistant       [cyan]:ai --mcp=on/off[/cyan]  MCP
  [cyan]:explain :refactor :debug :docs[/cyan]  AI actions
  [cyan]:tabn :tabp :tabc[/cyan]  Tab nav
  [cyan]:export f.vdtf  :import f.vdtf[/cyan]  Dotfile config

[bold yellow]Panels[/bold yellow]
  [cyan]Ctrl+T[/cyan]  Terminal   [cyan]Ctrl+F[/cyan]  File finder
  [cyan]Ctrl+S[/cyan]  Save       [cyan]Ctrl+W[/cyan]  Close tab
  [cyan]gt / gT[/cyan]  Next / prev tab

[dim]ESC or q to close[/dim]"""


class SettingsScreen(ModalScreen):
    BINDINGS = [Binding("escape", "dismiss", "Close")]

    def compose(self) -> ComposeResult:
        cfg = settings
        ai_lbl  = "✓ Enabled"  if cfg.get("ai_enabled",  True)  else "✗ Disabled"
        mcp_lbl = "✓ Running"  if cfg.get("mcp_enabled", False) else "✗ Stopped"
        ani_lbl = "✓ On"       if cfg.get("animations",  True)  else "✗ Off"
        api_key = cfg.get("gemini_api_key", "")
        masked  = ("*" * min(len(api_key), 20)) if api_key else "[dim]not set[/dim]"
        with Container(id="settings-root"):
            yield Static("[bold cyan]⚙  Void Settings[/bold cyan]")
            yield Static(f"Theme:  [bold]{cfg.get('theme','tokyo-night')}[/bold]  [dim](use :theme)[/dim]")
            yield Static("")
            yield Static(f"AI Assistant:   {ai_lbl}")
            yield Button("Toggle AI",         id="btn-ai",   variant="primary")
            yield Static(f"MCP Server:     {mcp_lbl}")
            yield Button("Toggle MCP",        id="btn-mcp",  variant="primary")
            yield Static(f"Animations:     {ani_lbl}")
            yield Button("Toggle Animations", id="btn-anim", variant="primary")
            yield Static("")
            yield Static(f"Gemini API Key: {masked}")
            yield Input(placeholder="Paste key here…", id="input-apikey", password=True)
            yield Button("Save Key",           id="btn-key",  variant="success")
            yield Static("")
            yield Static(f"[dim]Config: {CONFIG_PATH}[/dim]")
            yield Static("[dim]ESC to close[/dim]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-ai":
            settings["ai_enabled"] = not settings.get("ai_enabled", True)
            save_config(settings)
            self.app.notify(f"AI {'enabled' if settings['ai_enabled'] else 'disabled'}")
            self.dismiss()
        elif bid == "btn-mcp":
            settings["mcp_enabled"] = not settings.get("mcp_enabled", False)
            save_config(settings)
            self.app.toggle_mcp()
            self.dismiss()
        elif bid == "btn-anim":
            settings["animations"] = not settings.get("animations", True)
            save_config(settings)
            self.dismiss()
        elif bid == "btn-key":
            key = self.query_one("#input-apikey", Input).value.strip()
            if key:
                settings["gemini_api_key"] = key
                save_config(settings)
                self.app.reload_ai()
                self.app.notify("API key saved!")
            self.dismiss()

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.dismiss()


class ThemeScreen(ModalScreen):
    """Theme picker — shows dark and light themes in separate scrollable groups."""
    BINDINGS = [Binding("escape", "dismiss", "Close")]

    def compose(self) -> ComposeResult:
        cur = settings.get("theme", "tokyo-night")
        with Container(id="theme-root"):
            yield Static("[bold cyan]🎨  Choose Theme[/bold cyan]")
            yield Static("[dim]↑ ↓ scroll  ·  Enter select  ·  ESC cancel[/dim]")
            yield Static("")
            with VerticalScroll(id="theme-scroll"):
                yield Static("[bold yellow]── Dark Themes ──[/bold yellow]")
                for key in DARK_THEMES:
                    th = THEMES[key]
                    marker = " ◄" if key == cur else ""
                    yield Button(f"{th['name']}{marker}", id=f"theme-{key}",
                                 variant="primary" if key == cur else "default")
                yield Static("")
                yield Static("[bold yellow]── Light Themes ──[/bold yellow]")
                for key in LIGHT_THEMES:
                    th = THEMES[key]
                    marker = " ◄" if key == cur else ""
                    yield Button(f"{th['name']}{marker}", id=f"theme-{key}",
                                 variant="primary" if key == cur else "default")
                yield Static("")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id or ""
        if bid.startswith("theme-"):
            k = bid[6:]
            if k in THEMES:
                self.app.apply_theme(k)
                self.app.notify(f"Theme: {THEMES[k]['name']}")
                self.dismiss()

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.dismiss()


class AIScreen(ModalScreen):
    BINDINGS = [Binding("escape", "dismiss", "Close")]

    def compose(self) -> ComposeResult:
        with Container(id="ai-root"):
            yield Static("[bold cyan]🤖  Void AI Assistant[/bold cyan]")
            yield Static("[dim]explain · refactor · debug · docs  or ask anything[/dim]")
            yield Static("", id="ai-out")
            yield Input(placeholder="Ask the AI…", id="ai-inp")
            yield Button("Send ↵", id="ai-send", variant="success")
            yield Static("[dim]ESC to close[/dim]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ai-send":
            self._send()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "ai-inp":
            self._send()

    def _send(self):
        inp = self.query_one("#ai-inp", Input)
        prompt = inp.value.strip()
        if not prompt:
            return
        inp.value = ""
        out = self.query_one("#ai-out", Static)
        out.update("[dim]Thinking…[/dim]")
        shortcuts = {
            "explain":  "Explain this code.",
            "refactor": "Suggest refactoring improvements.",
            "debug":    "Help debug this code.",
            "docs":     "Generate documentation/docstrings.",
        }
        prompt = shortcuts.get(prompt.lstrip(":").lower(), prompt)
        ai  = self.app.ai
        ctx = self.app.get_current_content()
        parts: list[str] = []

        def on_chunk(text, done=False):
            parts.append(text)
            full = "".join(parts)
            try:
                out.update(Text.from_markup(f"[white]{escape(full)}[/white]"))
            except Exception:
                out.update(full)

        if not ai.available:
            out.update("[red]AI not configured. Use :settings to add your Gemini API key.[/red]")
        else:
            ai.ask(prompt, context=ctx, callback=on_chunk)

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.dismiss()


class UnsavedDialog(ModalScreen):
    def __init__(self, filename: str):
        super().__init__()
        self.filename = filename

    def compose(self) -> ComposeResult:
        name = os.path.basename(self.filename)
        with Container(id="dialog-root"):
            yield Static(f"[bold yellow]Unsaved changes in [cyan]{escape(name)}[/cyan][/bold yellow]")
            yield Static("Save before closing?")
            with Horizontal(id="dialog-btns"):
                yield Button("Yes",    id="btn-yes",    variant="success")
                yield Button("No",     id="btn-no",     variant="error")
                yield Button("Cancel", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id)

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":    self.dismiss("btn-cancel")
        elif event.key == "y":       self.dismiss("btn-yes")
        elif event.key == "n":       self.dismiss("btn-no")


# ── Editor Widget ─────────────────────────────────────────────────────────────

class VoidEditorWidget(Widget, can_focus=True):
    """Main editing surface — preserves all original vim/search/visual logic."""

    DEFAULT_CSS = "VoidEditorWidget { width: 1fr; height: 1fr; }"

    def __init__(self, tab_manager: TabManager, **kwargs):
        super().__init__(**kwargs)
        self.tab_manager   = tab_manager
        self.cursor        = Cursor()
        self.window        = Window(40, 120)
        self.mode          = "normal"
        self._search_state = search_state
        self._visual_state = visual_state
        self._insert_snap  = False

    # ── public ───────────────────────────────────────────────────────────────

    @property
    def buffer(self) -> Buffer:
        t = self.tab_manager.active_tab
        return t.buffer if t else Buffer([""])

    @property
    def tab(self) -> Tab:
        return self.tab_manager.active_tab

    def load_file(self, filepath: str):
        try:
            with open(filepath, encoding="utf-8", errors="replace") as f:
                lines = f.read().splitlines()
        except FileNotFoundError:
            lines = [""]
        buf = Buffer(lines if lines else [""])
        new_tab = Tab(filepath, buf)
        self.tab_manager.add_tab(new_tab)
        self.cursor = Cursor()
        self._search_state.reset()
        self._visual_state.reset()
        reset_pending()
        self.refresh()
        add_recent_file(filepath)

    def get_content(self) -> str:
        return "\n".join(self.buffer.lines)

    def switch_tab(self, direction: str):
        if self.tab:
            self.tab.save_cursor(self.cursor, self.window)
        if direction == "next":
            self.tab_manager.next_tab()
        elif direction == "prev":
            self.tab_manager.prev_tab()
        if self.tab:
            self.tab.restore_cursor(self.cursor, self.window)
        self._search_state.reset()
        self._visual_state.reset()
        reset_pending()
        self.refresh()
        self.post_message(self.ModeChanged(self.mode))

    # ── render ────────────────────────────────────────────────────────────────

    def render(self) -> Text:
        size = self.size
        h = max(size.height, 1)
        w = max(size.width,  1)
        self.window.n_rows = h
        self.window.n_cols = w

        buf   = self.buffer
        theme = get_theme(settings.get("theme", "tokyo-night"))
        ln_w  = len(str(len(buf))) + 2

        # sync scroll
        if self.cursor.row < self.window.row:
            self.window.row = self.cursor.row
        elif self.cursor.row >= self.window.row + h:
            self.window.row = self.cursor.row - h + 1
        self.window.row = max(0, self.window.row)

        lang   = detect_language(self.tab.filename) if self.tab else None
        result = Text(no_wrap=True, overflow="fold")

        bg_col   = theme["background"]
        sel_col  = theme["selection"]
        blue_col = theme["blue"]

        for screen_row in range(h):
            buf_row = self.window.row + screen_row
            if buf_row >= len(buf):
                result.append(" " * w + "\n", style=f"on {bg_col}")
                continue

            line           = buf[buf_row]
            is_cursor_line = (buf_row == self.cursor.row)
            code_w         = w - ln_w

            # line number
            ln_str = f"{buf_row + 1:>{ln_w - 1}} "
            result.append(ln_str, style="bold white" if is_cursor_line else "dim")

            display_line = line[self.window.col:self.window.col + code_w]

            # visual selection columns for this row
            vs = self._visual_state
            vc = None
            if vs.active:
                r = vs.get_range(self.cursor)
                if vs.mode == "char":
                    sr, sc, er, ec = r
                    if sr <= buf_row <= er:
                        if sr == er:       vc = (sc, ec)
                        elif buf_row == sr: vc = (sc, len(line) - 1)
                        elif buf_row == er: vc = (0, ec)
                        else:              vc = (0, len(line) - 1)
                elif vs.mode == "line":
                    sr, _, er, _ = r
                    if sr <= buf_row <= er:
                        vc = (0, max(len(line) - 1, 0))
                elif vs.mode == "block":
                    top, left, bot, right = r
                    if top <= buf_row <= bot:
                        vc = (left, min(right, len(line) - 1))

            # cursor-line background
            if is_cursor_line and not vc:
                bg_style = f"on {sel_col}"
            else:
                bg_style = ""

            tokens   = tokenize_line(display_line, lang) if lang else [(display_line, 8)]
            col_idx  = self.window.col
            rendered = 0

            for text_chunk, color_id in tokens:
                if rendered >= code_w:
                    break
                chunk = text_chunk[:code_w - rendered]
                base  = _color_to_rich(color_id, theme)

                for ci, ch in enumerate(chunk):
                    abs_col = col_idx + ci
                    if vc and vc[0] <= abs_col <= vc[1]:
                        result.append(ch, style=f"bold on {blue_col}")
                    elif is_cursor_line and not vc and abs_col == self.cursor.col and self.mode != "insert":
                        result.append(ch, style="reverse bold")
                    elif is_cursor_line and bg_style:
                        result.append(ch, style=f"{base} {bg_style}")
                    else:
                        result.append(ch, style=base)

                col_idx  += len(chunk)
                rendered += len(chunk)

            # insert-mode cursor block
            if is_cursor_line and self.mode == "insert":
                cur_screen = self.cursor.col - self.window.col
                if 0 <= cur_screen < code_w:
                    pass  # cursor shown by terminal

            # pad
            pad = code_w - rendered
            if pad > 0:
                result.append(" " * pad, style=bg_style if bg_style else "")
            result.append("\n")

        return result

    # ── key dispatch ──────────────────────────────────────────────────────────

    def on_key(self, event: events.Key) -> None:
        event.stop()
        key  = event.key
        char = event.character

        if self.mode == "normal":
            self._normal_key(key, char)
        elif self.mode == "insert":
            self._insert_key(key, char)
        elif self.mode in ("visual", "visual-line", "visual-block"):
            self._visual_key(key, char)

        if self.tab:
            self.tab.modified = self.tab.modified  # preserve existing flag

        self.refresh()
        self.post_message(self.ModeChanged(self.mode))

    # ── normal mode ───────────────────────────────────────────────────────────

    def _normal_key(self, key: str, char):
        buf = self.buffer; cur = self.cursor; win = self.window; tab = self.tab

        if key == "escape":
            self._search_state.reset()
            self._visual_state.reset()
            reset_pending()
            return

        if key == "colon" or char == ":":
            self.post_message(self.EnterCommand())
            return

        if char == "/":
            self.post_message(self.EnterSearch())
            return

        ss = self._search_state
        if ss.confirming and char in ("y", "n", "a", "q"):
            self._handle_search_confirm(char)
            return

        if key == "up":    cur.up(buf);   win.up(cur);         win.horizontal_scroll(cur); return
        if key == "down":  cur.down(buf); win.down(buf, cur);  win.horizontal_scroll(cur); return
        if key == "left":  _cur_left(win, buf, cur);  return
        if key == "right": _cur_right(win, buf, cur); return
        if key == "home":  cur.col = 0;  return
        if key == "end":   cur.col = len(buf[cur.row]); return

        if char == "i": self._enter_insert(); return
        if char == "a": _cur_right(win, buf, cur); self._enter_insert(); return
        if char == "v": self._visual_state.start("char", cur);  self.mode = "visual"; return
        if char == "V": self._visual_state.start("line", cur);  self.mode = "visual-line"; return
        if key == "ctrl+v": self._visual_state.start("block", cur); self.mode = "visual-block"; return

        if char:
            result, mode_change = handle_vim_motion(char, buf, cur, win, tab)
            if result == "tab_next":   self.switch_tab("next")
            elif result == "tab_prev": self.switch_tab("prev")
            elif result:
                if tab: tab.modified = True
            if mode_change and mode_change == "insert":
                self._enter_insert()

    def _handle_search_confirm(self, char: str):
        ss = self._search_state; buf = self.buffer; tab = self.tab
        if char == "y":
            row, col = ss.matches[ss.match_index]
            buf.lines[row] = buf.lines[row][:col] + ss.replacement + buf.lines[row][col + len(ss.query):]
            if tab: tab.modified = True
            ss.find_all(buf, ss.query)
            if not ss.matches:
                ss.reset()
            else:
                ss.confirming  = True
                ss.match_index = min(ss.match_index, len(ss.matches) - 1)
                ss._jump_to_match(self.cursor, self.window, buf)
        elif char == "n":
            if len(ss.matches) <= 1:
                ss.reset()
            else:
                ss.match_index = (ss.match_index + 1) % len(ss.matches)
                ss._jump_to_match(self.cursor, self.window, buf)
        elif char == "a":
            ss.replace_all(buf, ss.replacement)
            if tab: tab.modified = True
        elif char == "q":
            ss.reset()

    # ── insert mode ───────────────────────────────────────────────────────────

    def _insert_key(self, key: str, char):
        buf = self.buffer; cur = self.cursor; win = self.window; tab = self.tab

        if key == "escape":
            self.mode = "normal"; self._insert_snap = False; return

        if key == "up":    cur.up(buf);   win.up(cur);         win.horizontal_scroll(cur); return
        if key == "down":  cur.down(buf); win.down(buf, cur);  win.horizontal_scroll(cur); return
        if key == "left":  _cur_left(win, buf, cur);  return
        if key == "right": _cur_right(win, buf, cur); return
        if key == "home":  cur.col = 0;  return
        if key == "end":   cur.col = len(buf[cur.row]); return

        if key == "enter":
            if not self._insert_snap:
                save_snapshot(buf, cur, tab); self._insert_snap = True
            if settings.get("auto_indent", True):
                auto_indent(buf, cur, win)
            else:
                buf.split(cur); cur.row += 1; cur.col = 0; win.down(buf, cur)
            if tab: tab.modified = True
            return

        if key in ("backspace", "ctrl+h"):
            if (cur.row, cur.col) > (0, 0):
                if not self._insert_snap:
                    save_snapshot(buf, cur, tab); self._insert_snap = True
                from config.keys import INDENT_WIDTH
                text_before = buf[cur.row][:cur.col]
                if text_before and text_before.isspace() and len(text_before) >= INDENT_WIDTH:
                    remove = len(text_before) % INDENT_WIDTH or INDENT_WIDTH
                    for _ in range(remove):
                        _cur_left(win, buf, cur); buf.delete(cur)
                else:
                    _cur_left(win, buf, cur); buf.delete(cur)
                if tab: tab.modified = True
            return

        if key in ("delete", "ctrl+d"):
            if not self._insert_snap:
                save_snapshot(buf, cur, tab); self._insert_snap = True
            buf.delete(cur)
            if tab: tab.modified = True
            return

        if key == "tab":
            if not self._insert_snap:
                save_snapshot(buf, cur, tab); self._insert_snap = True
            from config.keys import INDENT_STR
            buf.insert(cur, INDENT_STR)
            for _ in INDENT_STR: _cur_right(win, buf, cur)
            if tab: tab.modified = True
            return

        if char and settings.get("auto_pair", True) and char in "([{\"'":
            if not self._insert_snap:
                save_snapshot(buf, cur, tab); self._insert_snap = True
            pairs = {"(": ")", "[": "]", "{": "}", '"': '"', "'": "'"}
            buf.insert(cur, char + pairs[char])
            _cur_right(win, buf, cur)
            if tab: tab.modified = True
            return

        if char is not None and len(char) >= 1:
            if not self._insert_snap:
                save_snapshot(buf, cur, tab); self._insert_snap = True
            buf.insert(cur, char)
            for _ in char: _cur_right(win, buf, cur)
            if tab: tab.modified = True

    # ── visual mode ───────────────────────────────────────────────────────────

    def _visual_key(self, key: str, char):
        buf = self.buffer; cur = self.cursor; win = self.window; tab = self.tab; vs = self._visual_state

        if key == "escape":       vs.reset(); self.mode = "normal"; return
        if key == "up":           cur.up(buf);   win.up(cur)
        elif key == "down":       cur.down(buf); win.down(buf, cur)
        elif key == "left":       _cur_left(win, buf, cur)
        elif key == "right":      _cur_right(win, buf, cur)
        elif char == "h" and cur.col > 0:             cur.col -= 1
        elif char == "l" and cur.col < len(buf[cur.row]): cur.col += 1
        elif char == "j":         cur.down(buf); win.down(buf, cur)
        elif char == "k":         cur.up(buf);   win.up(cur)
        elif char == "w":         motion_w(buf, cur, win)
        elif char == "b":         motion_b(buf, cur, win)
        elif char == "0":         cur.col = 0
        elif char == "$":         cur.col = max(len(buf[cur.row]) - 1, 0)
        elif char == "^":         motion_caret(buf, cur, win)
        elif char == "G":         motion_G(buf, cur, win)
        elif key == "ctrl+d":     win.half_page_down(buf, cur)
        elif key == "ctrl+u":     win.half_page_up(buf, cur)
        elif char in ("d", "x"):
            visual_delete(buf, cur, win, vs, tab)
            self.mode = "normal"
            if tab: tab.modified = True
        elif char == "y":
            visual_yank(buf, cur, vs); self.mode = "normal"
        elif char == "c":
            visual_change(buf, cur, win, vs, tab)
            self.mode = "insert"; self._insert_snap = False
            if tab: tab.modified = True
        elif char == ">":
            visual_indent(buf, cur, vs, direction=1,  tab=tab)
            self.mode = "normal"
            if tab: tab.modified = True
        elif char == "<":
            visual_indent(buf, cur, vs, direction=-1, tab=tab)
            self.mode = "normal"
            if tab: tab.modified = True
        elif char == "v":
            if vs.mode == "char": vs.reset(); self.mode = "normal"
            else: vs.mode = "char"; self.mode = "visual"
        elif char == "V":
            if vs.mode == "line": vs.reset(); self.mode = "normal"
            else: vs.mode = "line"; self.mode = "visual-line"
        elif key == "ctrl+v":
            if vs.mode == "block": vs.reset(); self.mode = "normal"
            else: vs.mode = "block"; self.mode = "visual-block"

        win.horizontal_scroll(cur)

    def _enter_insert(self):
        self.mode = "insert"; self._insert_snap = False

    # ── messages ─────────────────────────────────────────────────────────────

    class ModeChanged(Message):
        def __init__(self, mode: str):
            super().__init__()
            self.mode = mode

    class EnterCommand(Message):
        def __init__(self):
            super().__init__()

    class EnterSearch(Message):
        def __init__(self):
            super().__init__()


# ── File Finder Widget ────────────────────────────────────────────────────────

class FileFinderWidget(Widget):
    DEFAULT_CSS = "FileFinderWidget { width: 30; height: 1fr; border-left: solid $void-border; }"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cwd         = os.getcwd()
        self.files: list = []
        self.selected    = 0
        self.scroll_off  = 0
        self.show_hidden = False
        self._refresh()

    def _refresh(self):
        try:
            entries = os.listdir(self.cwd)
        except PermissionError:
            entries = []
        if not self.show_hidden:
            entries = [e for e in entries if not e.startswith(".")]
        dirs  = sorted(e for e in entries if os.path.isdir(os.path.join(self.cwd, e)))
        files = sorted(e for e in entries if os.path.isfile(os.path.join(self.cwd, e)))
        self.files    = ["../"] + [d + "/" for d in dirs] + files
        self.selected = 0
        self.scroll_off = 0

    def render(self) -> Text:
        h = self.size.height
        w = self.size.width
        t = Text()
        short = os.path.basename(self.cwd) or self.cwd
        t.append(f" Files — {short}/\n", style="bold cyan")
        t.append("─" * w + "\n", style="dim")
        visible = h - 3
        if self.selected >= self.scroll_off + visible:
            self.scroll_off = self.selected - visible + 1
        if self.selected < self.scroll_off:
            self.scroll_off = self.selected
        for i, entry in enumerate(self.files[self.scroll_off:self.scroll_off + visible]):
            idx  = self.scroll_off + i
            disp = entry[:w - 2]
            if idx == self.selected:
                t.append(f" {disp}\n", style="reverse bold")
            elif entry.endswith("/"):
                t.append(f" {disp}\n", style="bold blue")
            else:
                t.append(f" {disp}\n")
        return t

    def on_key(self, event: events.Key) -> None:
        event.stop()
        k = event.key; char = event.character
        if k == "escape":
            self.post_message(self.Blur())
        elif k == "down" or char == "j":
            if self.selected < len(self.files) - 1:
                self.selected += 1
            self.refresh()
        elif k == "up" or char == "k":
            if self.selected > 0:
                self.selected -= 1
            self.refresh()
        elif k == "enter":
            self._select()
        elif char == "h":
            self.cwd = os.path.dirname(self.cwd); self._refresh(); self.refresh()
        elif char == ".":
            self.show_hidden = not self.show_hidden; self._refresh(); self.refresh()
        elif char == "r":
            self._refresh(); self.refresh()

    def _select(self):
        if not self.files: return
        entry = self.files[self.selected]
        if entry == "../":
            self.cwd = os.path.dirname(self.cwd); self._refresh(); self.refresh()
        elif entry.endswith("/"):
            self.cwd = os.path.join(self.cwd, entry.rstrip("/")); self._refresh(); self.refresh()
        else:
            self.post_message(self.FileSelected(os.path.join(self.cwd, entry)))

    class Blur(Message):
        def __init__(self): super().__init__()

    class FileSelected(Message):
        def __init__(self, path: str):
            super().__init__()
            self.path = path


# ── HUD Widget ────────────────────────────────────────────────────────────────

class HUDWidget(Static):
    def __init__(self, **kwargs):
        super().__init__("", **kwargs)
        self._start = time.time()

    def update_hud(self, mode: str, filename: str):
        ext = os.path.splitext(filename)[1][1:] if os.path.splitext(filename)[1] else "txt"
        clk = time.strftime("%H:%M")
        elapsed = int(time.time() - self._start)
        if elapsed < 60:       ela = f"{elapsed}s"
        elif elapsed < 3600:   ela = f"{elapsed // 60}m"
        else:                  ela = f"{elapsed // 3600}h{(elapsed % 3600) // 60}m"

        styles = {
            "normal":       ("NORMAL",  "bold black on blue"),
            "insert":       ("INSERT",  "bold black on green"),
            "visual":       ("VISUAL",  "bold black on magenta"),
            "visual-line":  ("V-LINE",  "bold black on magenta"),
            "visual-block": ("V-BLOCK", "bold black on cyan"),
            "command":      ("COMMAND", "bold black on yellow"),
        }
        label, style = styles.get(mode, (mode.upper(), "bold"))
        t = Text()
        t.append(f" {label} ", style=style)
        t.append(f" .{ext} │ {clk} │ {ela} ", style="dim")
        self.update(t)

    def reset_timer(self): self._start = time.time()


# ── Terminal Widget ───────────────────────────────────────────────────────────

class TerminalWidget(Widget):
    DEFAULT_CSS = "TerminalWidget { height: 12; border-top: solid $void-border; }"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._term = InlineTerminal()

    def compose(self) -> ComposeResult:
        yield Static(id="term-out")
        yield Input(placeholder="$ ", id="term-inp")

    def on_mount(self):
        self._refresh_output()
        self.set_interval(0.15, self._poll_and_refresh)

    def _poll_and_refresh(self):
        self._term.poll_process()
        self._refresh_output()

    def _refresh_output(self):
        try:
            out   = self.query_one("#term-out", Static)
            lines = self._term.get_display_lines()
            text  = "\n".join(lines[-25:])
            out.update(f"[dim]{escape(text)}[/dim]")
        except Exception:
            pass

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "term-inp":
            cmd = event.value
            event.input.value = ""
            self._term.run_command(cmd)
            self._refresh_output()

    class Blur(Message):
        def __init__(self): super().__init__()


# ── Main App ──────────────────────────────────────────────────────────────────

class VoidApp(App):
    """
    Void — modern cross-platform terminal code editor.
    Authors: Bailey Beber and Soumalya Das

    Theme system: overrides get_css_variables() to inject $void-* CSS
    variables, then calls refresh_css() to update every widget instantly.
    """

    # ── CSS uses $void-* variables — injected dynamically per theme ──────────
    CSS = """
    Screen {
        background: $void-bg;
        color: $void-fg;
    }
    /* ── splash ── */
    #splash-root    { align: center middle; width: 100%; height: 100%; padding: 2 4; }
    #splash-logo    { color: $void-accent; text-style: bold; content-align: center middle; width: 100%; }
    #splash-meta    { content-align: center middle; width: 100%; }
    #splash-tip     { content-align: center middle; width: 100%; color: $void-comment; }
    #rf-hdr         { content-align: center middle; width: 100%; color: $void-fg; }
    .rf-item        { content-align: center middle; width: 100%; }
    #splash-footer  { content-align: center middle; width: 100%; color: $void-comment; }

    /* ── layout ── */
    #tab-bar      { height: 1; background: $void-bg-alt; dock: top; }
    #editor-row   { height: 1fr; }
    #status-bar   { height: 1; background: $void-bg-alt; color: $void-status-fg; dock: bottom; }
    #search-bar   { height: 1; background: $void-bg-alt; dock: bottom; display: none; }
    #cmd-bar      { height: 1; background: $void-bg-alt; dock: bottom; display: none; }
    #search-input, #cmd-input { height: 1; border: none; background: $void-bg-alt; color: $void-fg; }
    HUDWidget     { dock: top; width: auto; align-horizontal: right; background: transparent; }

    /* ── terminal ── */
    TerminalWidget { background: $void-bg-alt; }
    #term-out      { height: 10; padding: 0 1; color: $void-fg; }
    #term-inp      { height: 1; border: none; background: $void-bg-alt; color: $void-fg;
                     border-top: solid $void-border; }

    /* ── file finder ── */
    FileFinderWidget { background: $void-bg-alt; }

    /* ── modals ── */
    #help-root, #settings-root, #ai-root, #dialog-root {
        background: $void-bg-alt;
        border: solid $void-accent;
        padding: 2 4;
        width: 72;
        height: auto;
        align: center middle;
        max-height: 90%;
    }
    #theme-root {
        background: $void-bg-alt;
        border: solid $void-accent;
        padding: 1 2;
        width: 52;
        height: auto;
        max-height: 92%;
        align: center middle;
    }
    #theme-scroll {
        height: 38;
        overflow-y: auto;
        width: 1fr;
    }
    #ai-out       { height: 18; border: solid $void-border; padding: 1; overflow-y: scroll; }
    #dialog-btns  { margin-top: 1; align: center middle; }
    Button        { margin: 0 1; }
    """

    TITLE = f"Void {VERSION} — {AUTHORS}"
    BINDINGS = [
        Binding("ctrl+t", "toggle_terminal", "Terminal", show=True),
        Binding("ctrl+f", "toggle_finder",   "Files",    show=True),
        Binding("ctrl+s", "save_file",       "Save",     show=False),
        Binding("ctrl+w", "close_tab",       "Close",    show=False),
    ]

    # ── Theme variable injection ──────────────────────────────────────────────

    def get_css_variables(self) -> dict[str, str]:
        """
        Override Textual's CSS variable system to inject $void-* theme colors.
        Called by Textual automatically and also by apply_theme() via refresh_css().
        """
        base = super().get_css_variables()
        theme_key = settings.get("theme", "tokyo-night")
        theme = get_theme(theme_key)
        base.update(theme_css_variables(theme))
        return base

    def apply_theme(self, theme_key: str) -> None:
        """
        Switch theme at runtime:
        1. Persist to config.
        2. Refresh CSS — Textual re-evaluates all $void-* variables immediately.
        3. Refresh all widgets so Rich Text renders re-read the new theme.
        """
        settings["theme"] = theme_key
        save_config(settings)
        self.refresh_css(animate=False)
        # Also force-refresh widgets that use Rich Text rendering
        try:
            self.query_one("#editor", VoidEditorWidget).refresh()
            self.query_one("#finder", FileFinderWidget).refresh()
        except Exception:
            pass
        self._update_ui()

    # ── init ─────────────────────────────────────────────────────────────────

    def __init__(self, initial_file: str = None):
        super().__init__()
        self._initial_file = initial_file
        self._tab_manager  = TabManager()
        self._mode         = "normal"
        self._show_term    = False
        self._show_finder  = False

        empty_buf = Buffer([""])
        self._tab_manager.add_tab(Tab("[new]", empty_buf))

        self.ai   = AIAssistant(settings)
        self._mcp = MCPServer(ai_assistant=self.ai)
        if settings.get("mcp_enabled", False):
            self._mcp.start()

    # ── compose ───────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Static("", id="tab-bar")
        yield HUDWidget(id="hud")
        with Horizontal(id="editor-row"):
            yield VoidEditorWidget(self._tab_manager, id="editor")
            yield FileFinderWidget(id="finder")
        yield TerminalWidget(id="terminal")
        yield Static("", id="status-bar")
        yield Container(Input(placeholder="/", id="search-input"), id="search-bar")
        yield Container(Input(placeholder=":", id="cmd-input"),    id="cmd-bar")

    def on_mount(self) -> None:
        if self._initial_file:
            self.open_file(self._initial_file)
        self.query_one("#terminal").display = False
        self.query_one("#finder").display   = False
        self.query_one("#editor").focus()
        self._update_ui()
        if not self._initial_file:
            self.push_screen(SplashScreen())

    # ── public ────────────────────────────────────────────────────────────────

    def open_file(self, filepath: str):
        editor = self.query_one("#editor", VoidEditorWidget)
        idx = self._tab_manager.find_tab(filepath)
        if idx != -1:
            self._tab_manager.go_to_tab(idx)
        else:
            editor.load_file(filepath)
        self._update_ui()

    def get_current_content(self) -> str:
        return self.query_one("#editor", VoidEditorWidget).get_content()

    def reload_ai(self):
        self.ai.reload(settings)
        self._mcp.ai_assistant = self.ai

    def toggle_mcp(self):
        if settings.get("mcp_enabled", False):
            if not self._mcp.running:
                self._mcp.start()
                msg = f"MCP started — {self._mcp.address}" if self._mcp.running else "MCP failed to start"
                severity = "information" if self._mcp.running else "error"
                self.notify(msg, severity=severity)
        else:
            self._mcp.stop()
            self.notify("MCP stopped")
        self._update_ui()

    # ── UI sync ───────────────────────────────────────────────────────────────

    def _update_ui(self):
        try:
            editor = self.query_one("#editor", VoidEditorWidget)
            tab    = self._tab_manager.active_tab

            # tab bar
            parts = []
            for i, t in enumerate(self._tab_manager.tabs):
                name = os.path.basename(t.filename) or "[new]"
                mod  = "●" if t.modified else ""
                if i == self._tab_manager.active_index:
                    parts.append(f"[bold cyan] {mod}{name} [/bold cyan]")
                else:
                    parts.append(f"[dim] {mod}{name} [/dim]")
            self.query_one("#tab-bar", Static).update("  " + "  │  ".join(parts))

            # status bar
            mode   = editor.mode
            fname  = tab.filename if tab else "[new]"
            mod    = tab.modified if tab else False
            r, c   = editor.cursor.row + 1, editor.cursor.col + 1
            tname  = settings.get("theme", "tokyo-night")
            mcp_s  = " [cyan]MCP[/cyan]" if self._mcp.running else ""

            mode_styles = {
                "normal":       "[bold green] NORMAL [/bold green]",
                "insert":       "[bold blue] INSERT [/bold blue]",
                "visual":       "[bold yellow] VISUAL [/bold yellow]",
                "visual-line":  "[bold yellow] V-LINE [/bold yellow]",
                "visual-block": "[bold yellow] V-BLOCK[/bold yellow]",
                "command":      "[bold magenta] COMMAND[/bold magenta]",
            }
            ms = mode_styles.get(mode, f"[bold] {mode.upper()} [/bold]")
            mm = "[yellow]●[/yellow] " if mod else ""
            self.query_one("#status-bar", Static).update(
                f"{ms}  {mm}[white]{escape(os.path.basename(fname))}[/white]{mcp_s}"
                f"  [dim]{r}:{c}[/dim]  [dim]{tname}[/dim]"
            )
            self.query_one("#hud", HUDWidget).update_hud(mode, fname)
        except Exception:
            pass

    # ── message handlers ──────────────────────────────────────────────────────

    def on_void_editor_widget_mode_changed(self, msg: VoidEditorWidget.ModeChanged) -> None:
        self._mode = msg.mode
        self._update_ui()

    def on_void_editor_widget_enter_command(self, _) -> None:
        self._open_cmd_bar()

    def on_void_editor_widget_enter_search(self, _) -> None:
        self._open_search_bar()

    def on_file_finder_widget_file_selected(self, msg: FileFinderWidget.FileSelected) -> None:
        self.open_file(msg.path)
        self.action_toggle_finder()

    def on_file_finder_widget_blur(self, _) -> None:
        if self._show_finder:
            self.action_toggle_finder()

    # ── command / search bars ─────────────────────────────────────────────────

    def _open_cmd_bar(self):
        bar = self.query_one("#cmd-bar")
        bar.display = True
        inp = self.query_one("#cmd-input", Input)
        inp.value = ""
        inp.focus()

    def _close_cmd_bar(self):
        self.query_one("#cmd-bar").display = False
        self.query_one("#editor").focus()

    def _open_search_bar(self):
        bar = self.query_one("#search-bar")
        bar.display = True
        inp = self.query_one("#search-input", Input)
        inp.value = ""
        inp.focus()

    def _close_search_bar(self):
        self.query_one("#search-bar").display = False
        self.query_one("#editor").focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "cmd-input":
            cmd = event.value.strip()
            self._close_cmd_bar()
            if cmd:
                self._execute_command(cmd)
        elif event.input.id == "search-input":
            query = event.value.strip()
            self._close_search_bar()
            if query:
                self._execute_search(query)

    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            try:
                if self.query_one("#cmd-bar").display:
                    self._close_cmd_bar(); return
                if self.query_one("#search-bar").display:
                    self._close_search_bar(); return
            except Exception:
                pass

    def _execute_search(self, query: str):
        editor = self.query_one("#editor", VoidEditorWidget)
        buf    = editor.buffer
        ss     = editor._search_state
        parts  = query.split("/")
        if len(parts) == 3 and parts[2] in ("g", "gc"):
            find_text, replace_text, flag = parts
            save_snapshot(buf, editor.cursor, editor.tab)
            ss.find_all(buf, find_text)
            if ss.matches:
                if flag == "gc":
                    ss.replacement = replace_text
                    ss.confirming  = True
                    ss.match_index = 0
                    ss._jump_to_match(editor.cursor, editor.window, buf)
                else:
                    ss.replace_all(buf, replace_text)
                    if editor.tab: editor.tab.modified = True
        else:
            ss.find_all(buf, query)
            ss.next_match(editor.cursor, editor.window, buf)
        editor.refresh()
        self._update_ui()
        self.notify(ss.match_info() if ss.matches else "No matches", timeout=2,
                    severity="information" if ss.matches else "warning")

    # ── command execution ─────────────────────────────────────────────────────

    def _execute_command(self, cmd: str):
        c = cmd.strip().lstrip(":")

        # ── help ──
        if c in ("h", "help"):
            self.push_screen(HelpScreen())

        # ── settings ──
        elif c == "settings":
            self.push_screen(SettingsScreen())

        # ── theme ──
        elif c == "theme":
            self.push_screen(ThemeScreen())
        elif c.startswith("theme "):
            k = c[6:].strip()
            if k in THEMES:
                self.apply_theme(k)
                self.notify(f"Theme: {THEMES[k]['name']}")
            else:
                self.notify(f"Unknown theme: {k}", severity="warning")

        # ── quit — :q :q! :quit :exit ──
        elif c in ("q", "quit", "exit"):
            self._cmd_quit()
        elif c in ("q!", "quit!", "exit!"):
            self.exit()

        # ── save ──
        elif c == "w":
            self._cmd_save()
        elif c == "wq":
            if self._cmd_save(): self.exit()
        elif c.startswith("w "):
            self._cmd_save(c[2:].strip())
        elif c.startswith("saveas "):
            self._cmd_save(c[7:].strip())

        # ── AI ──
        elif c == "ai" or c.startswith("ai "):
            parts = c.split()
            if "--mcp=on"  in parts:
                settings["mcp_enabled"] = True;  save_config(settings); self.toggle_mcp()
            elif "--mcp=off" in parts:
                settings["mcp_enabled"] = False; save_config(settings); self.toggle_mcp()
            else:
                self.push_screen(AIScreen())
        elif c in ("explain", "refactor", "debug", "docs"):
            self.push_screen(AIScreen())

        # ── file ops ──
        elif c.startswith("e "):
            fp = c[2:].strip()
            if fp: self.open_file(fp)
        elif c.startswith("tabnew "):
            fp = c[7:].strip()
            if fp: self.open_file(fp)

        # ── tab navigation ──
        elif c in ("tabn", "tabnext"):
            self.query_one("#editor", VoidEditorWidget).switch_tab("next"); self._update_ui()
        elif c in ("tabp", "tabprev"):
            self.query_one("#editor", VoidEditorWidget).switch_tab("prev"); self._update_ui()
        elif c in ("tabc", "tabclose"):
            self.action_close_tab()

        # ── config ──
        elif c == "config":
            from config.settings import create_default_config
            create_default_config(); self.open_file(CONFIG_PATH)

        # ── dotfile ──
        elif c.startswith("export "):
            self._cmd_export(c[7:].strip())
        elif c.startswith("import "):
            self._cmd_import(c[7:].strip())

        # ── terminal ──
        elif c in ("t", "terminal"):
            self.action_toggle_terminal()

        else:
            self.notify(f"Unknown command: :{cmd}", severity="warning")

    def _cmd_quit(self):
        tab = self._tab_manager.active_tab
        if tab and tab.modified:
            def handle(result):
                if result == "btn-yes":
                    self._cmd_save(); self.exit()
                elif result == "btn-no":
                    self.exit()
            self.push_screen(UnsavedDialog(tab.filename), handle)
        else:
            self.exit()

    def _cmd_save(self, filename: str = None) -> bool:
        editor = self.query_one("#editor", VoidEditorWidget)
        tab    = self._tab_manager.active_tab
        if not tab: return False
        target = filename or tab.filename
        if target in ("[new]", ""):
            self.notify("No filename. Use :w filename", severity="warning"); return False
        content = editor.get_content()
        if settings.get("trailing_newline", True) and not content.endswith("\n"):
            content += "\n"
        try:
            with open(target, "w", encoding="utf-8") as f:
                f.write(content)
            tab.filename = target; tab.modified = False
            self.notify(f"Saved: {os.path.basename(target)}")
            add_recent_file(target); self._update_ui()
            return True
        except OSError as e:
            self.notify(f"Save failed: {e}", severity="error"); return False

    def _cmd_export(self, filename: str):
        if not filename: filename = "settings.vdtf"
        cfg = {k: settings[k] for k in
               ("theme","ai_enabled","mcp_enabled","animations","gemini_api_key") if k in settings}
        try:
            with open(filename, "w") as f: json.dump(cfg, f, indent=2)
            self.notify(f"Exported: {filename}")
        except OSError as e:
            self.notify(f"Export failed: {e}", severity="error")

    def _cmd_import(self, filename: str):
        try:
            with open(filename) as f: cfg = json.load(f)
            settings.update(cfg); save_config(settings)
            if "theme" in cfg:
                self.apply_theme(cfg["theme"])
            self.notify(f"Imported: {filename}")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.notify(f"Import failed: {e}", severity="error")

    # ── actions ───────────────────────────────────────────────────────────────

    def action_toggle_terminal(self):
        self._show_term = not self._show_term
        term = self.query_one("#terminal")
        term.display = self._show_term
        if self._show_term:
            self.query_one("#terminal").query_one("#term-inp", Input).focus()
        else:
            self.query_one("#editor").focus()

    def action_toggle_finder(self):
        self._show_finder = not self._show_finder
        finder = self.query_one("#finder")
        finder.display = self._show_finder
        if self._show_finder:
            finder.focus()
        else:
            self.query_one("#editor").focus()

    def action_save_file(self):
        self._cmd_save()

    def action_close_tab(self):
        tm = self._tab_manager
        if len(tm.tabs) <= 1:
            self._cmd_quit(); return
        tab = tm.active_tab
        if tab and tab.modified:
            def handle(result):
                if result == "btn-yes": self._cmd_save()
                if result != "btn-cancel": tm.close_tab(); self._update_ui()
            self.push_screen(UnsavedDialog(tab.filename), handle)
        else:
            tm.close_tab(); self._update_ui()
        self.query_one("#editor").refresh()


# ── Entry point ───────────────────────────────────────────────────────────────

def main_entry():
    parser = argparse.ArgumentParser(
        description=f"Void {VERSION} — cross-platform terminal code editor",
        epilog=f"Authors: {AUTHORS}",
    )
    parser.add_argument("filename", nargs="?", default=None)
    args = parser.parse_args()
    from config.settings import create_default_config
    create_default_config()
    VoidApp(initial_file=args.filename).run()


if __name__ == "__main__":
    main_entry()
    