# Void — A Modern Cross-Platform Terminal Code Editor

> **Authors:** Bailey Beber and Soumalya Das  
> **Version:** 0.3.0

![Void Editor](assets/BLACKVOID.gif)

Void is a keyboard-driven, modal terminal code editor built in Python. It combines Vim-style editing with a modern Textual TUI, AI assistance via Google Gemini, a built-in terminal emulator, syntax highlighting, multi-tab support, and a rich theme system with both dark and light variants — all running natively on Windows, macOS, and Linux.

---

## ✨ Features

| Feature | Description |
|---|---|
| **Cross-platform TUI** | Built with [Textual](https://textual.textualize.io/) — works on Windows, macOS, Linux |
| **Modal editing** | Full Vim-style INSERT / NORMAL / VISUAL / V-LINE / V-BLOCK modes |
| **Vim motions** | hjkl, w/b, gg/G, dd/yy/p, dw/d$/d0, visual select, undo/redo |
| **Search & replace** | `/query`, `n`/`N`, `/find/replace/g`, `/find/replace/gc` (confirm each) |
| **Syntax highlighting** | Python, C, C++, Rust, JavaScript/TypeScript and more |
| **Multi-tab editing** | `gt`/`gT`, `:tabn`, `:tabp`, `:tabc`, per-tab cursor/scroll state |
| **File finder** | `Ctrl+F` side-panel file browser with directory navigation |
| **Inline terminal** | `Ctrl+T` integrated terminal emulator, cross-platform safe subprocess |
| **AI assistant** | Google Gemini powered: explain, refactor, debug, docs |
| **MCP server** | Local HTTP server at `http://127.0.0.1:7700` for external tool integration |
| **Theme engine** | 28 themes across 10 families — 14 dark + 14 light, scrollable picker, switches instantly at runtime |
| **HUD overlay** | Floating mode/filetype/clock/elapsed indicator |
| **Bracket matching** | Auto-detects matching `()[]{}` and quote pairs |
| **Auto-pair** | Automatically closes brackets and quotes in insert mode |
| **Auto-indent** | Smart indentation on Enter, including Python `:` blocks |
| **Startup dashboard** | Logo splash screen with random tips and recent files |
| **Dotfile system** | `.vdtf` config export/import for sharing setups |
| **Persistent config** | `~/.config/void/config.json`, auto-created on first launch |

---

## 🖥 Supported Platforms

| Platform | Status |
|---|---|
| **Linux** | ✅ Fully supported |
| **macOS** | ✅ Fully supported |
| **Windows** | ✅ Fully supported (no curses required) |

Requires **Python 3.8+** (tested through Python 3.14).

---

## 📦 Installation

### Quick start

```bash
git clone https://github.com/cryybash/Void
cd Void
pip install -r requirements.txt
python void.py
```

### Install as a package (optional)

```bash
pip install -e .
void          # run from anywhere
```

### Dependencies

```
textual>=0.47.0
rich>=13.7.0
google-genai>=0.3.0
```

---

## 🚀 Usage

```bash
# Open editor (shows splash screen)
python void.py

# Open a specific file directly
python void.py myfile.py

# If installed as a package
void myfile.py
```

---

## 🎮 Mode Overview

Void is a modal editor. Understanding which mode you are in is essential.

| Mode | How to enter | How to exit |
|---|---|---|
| **Normal** | Press `ESC` from any mode | — (this is the base mode) |
| **Insert** | Press `i` or `a` or `o`/`O` in Normal | Press `ESC` |
| **Visual** | Press `v` (char), `V` (line), `Ctrl+V` (block) | Press `ESC` |
| **Command** | Press `:` in Normal mode | Press `Enter` (run) or `ESC` (cancel) |
| **Search** | Press `/` in Normal mode | Press `Enter` (search) or `ESC` (cancel) |

> **Quick tip:** If you are ever lost, press `ESC` to return to Normal mode, then `:h` to open the help screen.

---

## 🎮 Keybinding Reference

### Navigation (Normal mode)

| Key | Action |
|---|---|
| `h j k l` | Left / down / up / right |
| `w` / `b` | Next / prev word |
| `0` / `$` / `^` | Start / end / first non-blank of line |
| `gg` / `G` | Top / bottom of file |
| `Ctrl+D` / `Ctrl+U` | Half page down / up |
| `gt` / `gT` | Next / prev tab |
| Arrow keys | Move cursor (works in Normal and Insert) |

### Editing (Normal mode)

| Key | Action |
|---|---|
| `i` | Enter Insert mode at cursor |
| `a` | Enter Insert mode after cursor |
| `o` / `O` | Open new line below / above and enter Insert |
| `x` | Delete character under cursor |
| `dd` | Delete current line |
| `dw` `d$` `d0` `dG` `dgg` | Delete with motion |
| `yy` | Yank (copy) current line |
| `p` / `P` | Paste after / before cursor |
| `u` / `Ctrl+R` | Undo / redo |

### Insert Mode

| Key | Action |
|---|---|
| **`ESC`** | **Return to Normal mode** |
| Arrow keys | Move cursor |
| `Enter` | New line with auto-indent |
| `Backspace` | Delete character before cursor |
| `Delete` / `Ctrl+D` | Delete character under cursor |
| `Tab` | Insert indentation (4 spaces by default) |
| `(`, `[`, `{`, `"`, `'` | Auto-inserts closing pair |
| Any printable character | Inserted at cursor |

### Visual Mode

| Key | Action |
|---|---|
| `ESC` | Return to Normal mode |
| `h j k l` / arrows | Extend selection |
| `w` / `b` | Extend by word |
| `d` or `x` | Delete selection |
| `y` | Yank selection |
| `c` | Change selection (delete and enter Insert) |
| `>` / `<` | Indent / unindent selection |

### Search

| Key | Action |
|---|---|
| `/query` | Search for `query` |
| `n` / `N` | Next / prev match |
| `/find/replace/g` | Replace all occurrences |
| `/find/replace/gc` | Replace with confirmation at each match |
| `ESC` | Clear highlights and exit search |

**Confirmation keys** (during `/gc` replace):

| Key | Action |
|---|---|
| `y` | Replace this match, go to next |
| `n` | Skip this match, go to next |
| `a` | Replace all remaining matches |
| `q` | Quit the replace operation |

### Commands (`:cmd`)

| Command | Action |
|---|---|
| `:h` or `:help` | Open help screen |
| `:w` | Save current file |
| `:w filename` | Save as filename |
| `:saveas filename` | Save as filename |
| `:q` | Quit (warns if unsaved changes) |
| `:q!` | Force quit without saving |
| `:wq` | Save and quit |
| `:e file` | Open file (new tab or switch if open) |
| `:tabnew file` | Open file in new tab |
| `:tabn` / `:tabnext` | Next tab |
| `:tabp` / `:tabprev` | Previous tab |
| `:tabc` / `:tabclose` | Close current tab |
| `:settings` | Open settings panel |
| `:theme` | Open theme picker |
| `:theme name` | Set theme directly by key (e.g. `:theme gruvbox-light`) |
| `:ai` | Open AI assistant panel |
| `:ai --mcp=on` | Start MCP server |
| `:ai --mcp=off` | Stop MCP server |
| `:explain` | AI: explain current file |
| `:refactor` | AI: refactoring suggestions |
| `:debug` | AI: debugging help |
| `:docs` | AI: generate docstrings |
| `:config` | Open `config.json` in a new tab |
| `:export file.vdtf` | Export settings to dotfile |
| `:import file.vdtf` | Import settings from dotfile |
| `:t` or `:terminal` | Toggle integrated terminal |

### Global Shortcuts

| Key | Action |
|---|---|
| `Ctrl+T` | Toggle integrated terminal |
| `Ctrl+F` | Toggle file finder panel |
| `Ctrl+S` | Save current file |
| `Ctrl+W` | Close current tab |

---

## ⚙️ Configuration

Void stores its configuration at:

```
~/.config/void/config.json
```

This file is created automatically on first launch with all defaults. You can edit it directly or use `:config` from inside Void to open it in a tab.

```json
{
  "author": "Bailey Beber and Soumalya Das",
  "theme": "tokyo-night",
  "ai_enabled": true,
  "mcp_enabled": false,
  "gemini_api_key": "",
  "animations": true,
  "indent_width": 4,
  "tab_width": 4,
  "auto_indent": true,
  "auto_pair": true,
  "trailing_newline": true,
  "show_line_numbers": true,
  "show_indent_guides": true,
  "show_hud": true,
  "scroll_margin": 5,
  "terminal_height": 10,
  "subprocess_timeout": 30,
  "max_undo": 100,
  "max_recent_files": 20,
  "max_recent_display": 8
}
```

---

## 🤖 AI Setup (Gemini)

Void's AI assistant uses the Google Gemini API for code explanation, refactoring, debugging, and documentation generation.

### Setup

**Option 1 — Environment variable:**
```bash
export GEMINI_API_KEY=your_key_here
python void.py
```

**Option 2 — Via settings panel:**
1. Open Void
2. Type `:settings`
3. Paste your API key in the "Gemini API Key" field
4. Click "Save Key"

### Usage

```
:ai          → Open AI chat panel
:explain     → Explain the current file
:refactor    → Refactoring suggestions
:debug       → Debugging help
:docs        → Generate docstrings
```

---

## 🌐 MCP Server

Void includes a **Model Context Protocol** server that exposes editor context to external tools.

### Start / Stop

```
:ai --mcp=on    → start server on http://127.0.0.1:7700
:ai --mcp=off   → stop server
```

### Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/status` | Server info and status |
| `GET` | `/context` | Current file, content, cursor position |
| `POST` | `/prompt` | Send a prompt, receive AI response |

### Example request

```bash
curl -X POST http://127.0.0.1:7700/prompt \
  -H "Content-Type: application/json" \
  -d '{"prompt": "explain this function", "context": "def foo(): pass"}'
```

---

## 🎨 Themes

Use `:theme` to open the interactive theme picker, or `:theme <key>` to set a theme directly.  
The selected theme is saved to `config.json` and automatically restored on next launch.

Theme switching is instant — no restart required.
The picker panel is fully scrollable so all 28 themes are always reachable.

### Dark Themes (14)

| Key | Name |
|---|---|
| `tokyo-night` | Tokyo Night |
| `dracula` | Dracula |
| `nord` | Nord |
| `gruvbox` | Gruvbox Dark |
| `catppuccin` | Catppuccin Mocha |
| `catppuccin-macchiato` | Catppuccin Macchiato |
| `catppuccin-frappe` | Catppuccin Frappe |
| `solarized-dark` | Solarized Dark |
| `material` | Material Ocean |
| `monokai` | Monokai |
| `one-dark` | One Dark |
| `cyberpunk` | Cyberpunk |
| `retro-terminal` | Retro Terminal |
| `nature` | Nature |

### Light Themes (14)

| Key | Name |
|---|---|
| `tokyo-night-day` | Tokyo Night Day |
| `nord-light` | Nord Light |
| `gruvbox-light` | Gruvbox Light |
| `catppuccin-latte` | Catppuccin Latte |
| `solarized-light` | Solarized Light |
| `material-lighter` | Material Lighter |
| `minimalist` | Minimalist Light |
| `one-light` | One Light |
| `github-light` | GitHub Light |
| `papercolor-light` | PaperColor Light |
| `ayu-light` | Ayu Light |
| `rose-pine-dawn` | Rosé Pine Dawn |
| `everforest-light` | Everforest Light |
| `kanagawa-lotus` | Kanagawa Lotus |

### Examples

```
:theme gruvbox-light       → Gruvbox Light
:theme catppuccin-latte    → Catppuccin Latte
:theme tokyo-night         → Tokyo Night (dark)
:theme solarized-light     → Solarized Light
```

---

## 📄 Dotfile Export / Import (`.vdtf`)

Void supports a custom dotfile format for sharing or backing up configurations:

```bash
# Export current settings from inside Void
:export myconfig.vdtf

# Import settings
:import myconfig.vdtf
```

Exported `.vdtf` files are standard JSON:

```json
{
  "theme": "gruvbox-light",
  "ai_enabled": true,
  "mcp_enabled": false,
  "animations": true,
  "gemini_api_key": ""
}
```

---

## 📁 Project Structure

```
void.py                   Main entry point + Textual App class
config/
  settings.py             JSON config loader/saver (~/.config/void/config.json)
  keys.py                 Key constants and config-derived editor defaults
  colors.py               Syntax color ID constants
  keybinds.md             Full keybinding reference (this file's companion)
core/
  buffer.py               Text buffer (line list + insert/delete primitives)
  editing.py              Undo/redo snapshots, auto-indent logic
  tab.py                  Tab and TabManager (per-tab cursor/scroll state)
features/
  theme_engine.py         21-theme engine: THEMES dict, DARK_THEMES/LIGHT_THEMES
                          lists, get_theme(), theme_css_variables() — powers
                          runtime CSS variable injection via Textual's
                          get_css_variables() + refresh_css() mechanism
  terminal.py             Cross-platform inline terminal (background thread I/O)
  ai_assistant.py         Google Gemini AI integration (streaming callbacks)
  mcp_server.py           MCP HTTP server on port 7700
  file_finder.py          Textual file browser widget
modes/
  vim_motions.py          All vim motions and operators (w/b/gg/G/dd/yy/etc.)
  search.py               Search/replace state machine
  visual.py               Visual mode operations (delete/yank/change/indent)
  keybinds.py             Key dispatch reference (legacy)
ui/
  syntax.py               Language-aware syntax tokenizer
  display.py              Drawing helpers
  aesthetics.py           HUD widget logic
  splash.py               Splash screen helpers
assets/                   Logo PNGs and animated GIF
requirements.txt          pip dependencies
pyproject.toml            Package metadata and entry point
```

---

## 🐛 Changelog

### v0.3.0 — Theme System Overhaul

- **Fixed:** Theme switching via `:theme` command and the settings panel now works correctly. Previously, `DARK_THEMES`, `LIGHT_THEMES`, and `theme_css_variables()` were imported by `void.py` but did not exist in `theme_engine.py`, causing an `ImportError` on startup.
- **Fixed:** CSS variable names corrected from `$background`/`$foreground` to `$void-bg`/`$void-fg` etc., matching the `$void-*` variables used in `VoidApp.CSS`. This was the core reason themes appeared to switch (config saved) but the UI never updated visually.
- **Fixed:** Theme changes now call `refresh_css(animate=False)` which triggers Textual to re-call `get_css_variables()` and propagate new `$void-*` values to every widget instantly — no restart needed.
- **Fixed:** Selected theme is persisted to `~/.config/void/config.json` and auto-applied on next launch.
- **Added:** 7 light theme variants: Tokyo Night Day, Nord Light, Gruvbox Light, Catppuccin Latte, Solarized Light, Material Lighter, Minimalist Light.
- **Added:** 3 additional Catppuccin variants: Macchiato, Frappe (dark), Latte (light).
- **Added:** Material Ocean (replaces generic "Material" — more accurate palette).
- **Added:** `DARK_THEMES` and `LIGHT_THEMES` lists (auto-derived from `"dark"` flag on each theme dict).
- **Added:** `accent` key on every theme, used by `$void-accent` for logos, borders, and highlights.
- **Added:** `theme_css_variables(theme)` function returning the `dict[str, str]` that Textual's CSS variable system requires.
- **Added:** `ThemeScreen` picker separates themes into "Dark Themes" and "Light Themes" sections with a `VerticalScroll` inner container (`#theme-scroll`) so all 21 themes are fully reachable regardless of terminal height. Previously the panel used `height: auto; max-height: 90%` with no overflow/scroll, silently clipping the light themes off-screen.
- **Fixed:** `#theme-root` now has its own CSS rule (split from the shared `#help-root, #settings-root, …` rule) with correct dimensions for the compact theme picker layout.

### v0.3.0 — Textual Migration & Bug Fixes

- **Fixed:** Terminal crash (`TypeError: can't concat NoneType to bytes`) — background thread subprocess reader with proper `None` guards.
- **Fixed:** `KEY_RESIZE` inserting characters — resolved by migrating from `curses.getkey()` to Textual's event system.
- **Fixed:** UTF-8 encoding corruption — Textual's `event.character` provides proper Unicode strings, never raw bytes.
- **Fixed:** Blocking subprocess reads — fixed with non-blocking background thread I/O.
- **Added:** Full Textual TUI replacing curses backend.
- **Added:** AI assistant (Google Gemini), MCP server, multi-tab support.

---

## 🖼 Screenshots

*Editor with Tokyo Night theme, syntax highlighting, and HUD:*
![Void Screenshot](assets/VOID1.png)

---

## 📜 License

Apache License 2.0 — see [LICENSE.txt](LICENSE.txt)

---

## 👥 Authors

**Bailey Beber** and **Soumalya Das**

Repository: [https://github.com/cryybash/Void](https://github.com/cryybash/Void)
