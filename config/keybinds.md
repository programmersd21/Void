# Void — Keybinding & Command Reference

> **Version:** 0.3.0  
> **Authors:** Bailey Beber and Soumalya Das

---

## Mode Overview

Void is a **modal editor**. Every key means something different depending on which mode you are in. When in doubt, press `ESC` to return to Normal mode.

| Mode | How to Enter | How to Exit | What it Does |
|------|-------------|-------------|--------------|
| **Normal** | Press `ESC` from any mode | — (this is the base mode) | Navigate, delete, yank, search, run commands |
| **Insert** | `i`, `a`, `o`, `O` from Normal | **`ESC`** | Type text into the buffer |
| **Visual (char)** | `v` from Normal | `ESC` or `v` again | Select characters |
| **Visual (line)** | `V` from Normal | `ESC` or `V` again | Select whole lines |
| **Visual (block)** | `Ctrl+V` from Normal | `ESC` or `Ctrl+V` again | Select a rectangular block |
| **Command** | `:` from Normal | `Enter` (execute) or `ESC` (cancel) | Run editor commands |
| **Search** | `/` from Normal | `Enter` (search) or `ESC` (cancel) | Search and replace |

---

## Splash Screen

These bindings are active on the startup splash screen before any file is open.

| Key | Action |
|-----|--------|
| `1`–`8` | Open the corresponding recent file |
| `Enter` / `Space` / `ESC` | Open an empty buffer |
| `q` | Quit Void |

---

## Normal Mode

Normal mode is the default. You return here by pressing `ESC` from any other mode.

### Cursor Movement

| Key | Action |
|-----|--------|
| `h` | Move left one character |
| `l` | Move right one character |
| `j` | Move down one line |
| `k` | Move up one line |
| Arrow keys | Move in any direction (also wraps across lines) |
| `w` | Jump to start of next word |
| `b` | Jump to start of previous word |
| `0` | Move to start of line |
| `$` | Move to end of line |
| `^` | Move to first non-whitespace character |
| `gg` | Jump to first line of file |
| `G` | Jump to last line of file |
| `Ctrl+D` | Scroll down half a page (cursor moves with view) |
| `Ctrl+U` | Scroll up half a page (cursor moves with view) |

### Entering Insert Mode

| Key | Action |
|-----|--------|
| `i` | Insert at cursor |
| `a` | Insert after cursor (append) |
| `o` | Open new line below and enter Insert |
| `O` | Open new line above and enter Insert |

### Delete Operators

| Key | Action |
|-----|--------|
| `x` | Delete character under cursor |
| `dd` | Delete current line (yanked to clipboard) |
| `dw` | Delete from cursor to start of next word |
| `d$` | Delete from cursor to end of line |
| `d0` | Delete from cursor to start of line |
| `dG` | Delete from current line to end of file |
| `dgg` | Delete from current line to top of file |

### Yank and Paste

| Key | Action |
|-----|--------|
| `yy` | Yank (copy) current line to clipboard |
| `p` | Paste after current line |
| `P` | Paste before current line |

### Undo / Redo

| Key | Action |
|-----|--------|
| `u` | Undo last change |
| `Ctrl+R` | Redo last undone change |

### Visual Mode Entry

| Key | Action |
|-----|--------|
| `v` | Enter Visual (character) mode |
| `V` | Enter Visual (line) mode |
| `Ctrl+V` | Enter Visual (block) mode |

### Tab Navigation

| Key | Action |
|-----|--------|
| `gt` | Switch to next tab |
| `gT` | Switch to previous tab |

### Search Entry

| Key | Action |
|-----|--------|
| `/` | Open search prompt |

### Command Entry

| Key | Action |
|-----|--------|
| `:` | Open command bar |

---

## Insert Mode

> **To exit Insert mode and return to Normal mode: press `ESC`**

| Key | Action |
|-----|--------|
| `ESC` | Return to Normal mode |
| Arrow keys | Move cursor without leaving Insert mode |
| `Enter` | Split line at cursor; auto-indents new line |
| `Backspace` / `Ctrl+H` | Delete character before cursor; joins lines at column 0 |
| `Delete` / `Ctrl+D` | Delete character under cursor |
| `Tab` | Insert indentation (default: 4 spaces, configurable) |
| `(` `[` `{` `"` `'` | Auto-inserts matching closing character |
| Any printable character | Inserted at cursor position |

**Auto-indent behavior:**
- New lines inherit the indentation level of the line above.
- If the previous line ends with `:` (Python, etc.), an extra 4-space indent is added.

**Smart backspace:**
- If the cursor is at a position that is a multiple of the indent width and preceded only by spaces, backspace removes a full indent level at once.

---

## Visual Mode

Enter with `v` (char), `V` (line), or `Ctrl+V` (block) from Normal mode.

| Key | Action |
|-----|--------|
| `ESC` | Exit Visual, return to Normal |
| `v` | Toggle Visual (char); exit if already in char mode |
| `V` | Toggle Visual (line); exit if already in line mode |
| `Ctrl+V` | Toggle Visual (block); exit if already in block mode |
| `h j k l` | Extend selection |
| Arrow keys | Extend selection |
| `w` / `b` | Extend by word |
| `0` / `$` | Extend to line start / end |
| `^` | Extend to first non-blank |
| `G` | Extend to end of file |
| `Ctrl+D` / `Ctrl+U` | Extend half page down / up |
| `d` or `x` | Delete selection, return to Normal |
| `y` | Yank selection, return to Normal |
| `c` | Delete selection, enter Insert mode |
| `>` | Indent selection by one level |
| `<` | Unindent selection by one level |

---

## Search Mode

Open with `/` from Normal mode.

| Pattern | Action |
|---------|--------|
| `/query` | Search for all occurrences of `query` |
| `/find/replace/g` | Replace all occurrences of `find` with `replace` |
| `/find/replace/gc` | Replace with confirmation at each match |

| Key | Action |
|-----|--------|
| `Enter` | Execute search |
| `ESC` | Cancel, return to Normal |
| `n` | Jump to next match (from Normal mode) |
| `N` | Jump to previous match (from Normal mode) |
| `ESC` (in Normal) | Clear search highlights |

**Confirmation keys** (active during `/find/replace/gc`):

| Key | Action |
|-----|--------|
| `y` | Replace this match, advance to next |
| `n` | Skip this match, advance to next |
| `a` | Replace all remaining matches at once |
| `q` | Quit the replace operation |

---

## Command Mode

Open with `:` from Normal mode. Press `Enter` to execute, `ESC` to cancel.

### File Operations

| Command | Action |
|---------|--------|
| `:w` | Save current file |
| `:w filename` | Save as `filename` |
| `:saveas filename` | Save as `filename` (alias) |
| `:e file` | Open `file` (new tab, or switch if already open) |
| `:tabnew file` | Open `file` in a new tab |
| `:q` | Quit (prompts if unsaved changes) |
| `:q!` | Force quit without saving |
| `:quit` / `:exit` | Same as `:q` |
| `:quit!` / `:exit!` | Same as `:q!` |
| `:wq` | Save and quit |

### Tab Management

| Command | Action |
|---------|--------|
| `:tabn` / `:tabnext` | Switch to next tab |
| `:tabp` / `:tabprev` | Switch to previous tab |
| `:tabc` / `:tabclose` | Close current tab (prompts if unsaved) |

### Themes

| Command | Action |
|---------|--------|
| `:theme` | Open interactive theme picker |
| `:theme <key>` | Apply theme directly by its key |

**Dark theme keys:** `tokyo-night`, `dracula`, `nord`, `gruvbox`, `catppuccin`, `catppuccin-macchiato`, `catppuccin-frappe`, `solarized-dark`, `material`, `monokai`, `one-dark`, `cyberpunk`, `retro-terminal`, `nature`

**Light theme keys:** `tokyo-night-day`, `nord-light`, `gruvbox-light`, `catppuccin-latte`, `solarized-light`, `material-lighter`, `minimalist`, `one-light`, `github-light`, `papercolor-light`, `ayu-light`, `rose-pine-dawn`, `everforest-light`, `kanagawa-lotus`

Examples:
```
:theme gruvbox-light
:theme catppuccin-latte
:theme tokyo-night
```

### Settings & Config

| Command | Action |
|---------|--------|
| `:settings` | Open settings panel (toggle AI, MCP, animations; set API key) |
| `:config` | Open `~/.config/void/config.json` in a new tab |
| `:export file.vdtf` | Export current settings to a dotfile |
| `:import file.vdtf` | Import settings from a dotfile |

### AI & MCP

| Command | Action |
|---------|--------|
| `:ai` | Open AI assistant chat panel |
| `:ai --mcp=on` | Start MCP server on `http://127.0.0.1:7700` |
| `:ai --mcp=off` | Stop MCP server |
| `:explain` | AI explains the current file's code |
| `:refactor` | AI suggests refactoring improvements |
| `:debug` | AI helps debug the current file |
| `:docs` | AI generates docstrings for the current file |

### Terminal

| Command | Action |
|---------|--------|
| `:t` / `:terminal` | Toggle integrated terminal panel |

### Help

| Command | Action |
|---------|--------|
| `:h` / `:help` | Open full help/keybinding reference screen |

---

## Global Shortcuts

These work from any mode (handled at app level):

| Key | Action |
|-----|--------|
| `Ctrl+T` | Toggle integrated terminal panel |
| `Ctrl+F` | Toggle file finder panel |
| `Ctrl+S` | Save current file |
| `Ctrl+W` | Close current tab |

---

## Terminal Panel

Toggle with `Ctrl+T`. The terminal runs in a panel at the bottom of the editor.

| Key | Action |
|-----|--------|
| `Enter` | Execute the typed command |
| `ESC` | Close/hide the terminal panel |
| Any printable key | Type into the terminal input |

**Notes:**
- `cd <path>` is handled natively to change the working directory.
- All other commands run via the system shell.
- Subprocess timeout defaults to 30 seconds (configurable in `config.json`).

---

## File Finder Panel

Toggle with `Ctrl+F`. A side panel appears on the right for navigating the filesystem.

| Key | Action |
|-----|--------|
| `j` / `Down Arrow` | Move selection down |
| `k` / `Up Arrow` | Move selection up |
| `Enter` | Open selected file, or navigate into directory |
| `h` | Go up one directory level |
| `.` | Toggle visibility of hidden files (dotfiles) |
| `r` | Refresh file listing |
| `ESC` | Close the file finder, return focus to editor |

---

## Settings Panel (`:settings`)

The settings panel provides GUI toggles for common options:

| Option | Description |
|--------|-------------|
| **Theme** | Shows current theme key; use `:theme` to change |
| **Toggle AI** | Enable/disable the Gemini AI assistant |
| **Toggle MCP** | Start/stop the MCP HTTP server |
| **Toggle Animations** | Enable/disable UI animations |
| **Gemini API Key** | Paste key and click Save Key to persist |

---

## Quick Reference Card

```
NORMAL MODE                        INSERT MODE
─────────────────────────────────  ─────────────────────
h j k l .... move cursor           ESC ......... back to Normal  ← KEY
w / b ....... word forward/back    Enter ....... new line + indent
0  $  ^ ..... line start/end/nws   Backspace ... delete before
gg / G ...... file top/bottom      Tab ......... indent (4 spaces)
Ctrl+D/U .... half page ↓/↑        ([{"' ....... auto-close pair
                                   Any char .... insert at cursor
i ........... insert at cursor
a ........... insert after         VISUAL MODE
o / O ....... new line below/above ─────────────────────
                                   ESC ......... exit to Normal
x ........... delete char          hjkl/arrows . extend selection
dd .......... delete line          d / x ....... delete selection
dw d$ d0 .... delete with motion   y ........... yank selection
dG / dgg .... delete to end/top    c ........... change selection
yy .......... yank line            > / < ....... indent/unindent
p / P ....... paste after/before
u / Ctrl+R .. undo / redo          SEARCH (/)
                                   ─────────────────────
v / V / Ctrl+V  visual modes       /query ...... search
gt / gT ..... next/prev tab        /f/r/g ...... replace all
: ........... command mode         /f/r/gc ..... replace w/ confirm
/ ........... search               n / N ....... next/prev match
ESC ......... return to Normal     ESC ......... clear highlights

COMMAND MODE (:)                   PANELS
─────────────────────────────────  ─────────────────────
:w  :q  :q!  :wq                   Ctrl+T ...... terminal toggle
:e  :tabnew                        Ctrl+F ...... file finder
:tabn  :tabp  :tabc                Ctrl+S ...... save
:theme  :theme <key>               Ctrl+W ...... close tab
:settings  :config
:ai  :explain  :refactor
:debug  :docs
:export f.vdtf  :import f.vdtf
:h  :help
```
