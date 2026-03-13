# Copyright 2026 Bailey Beber and Soumalya Das
#
# Licensed under the Apache License, Version 2.0 (the "License")

from config.settings import settings

# Control key codes
KEY_ESCAPE = "\x1b"
KEY_CTRL_D = "\x04"
KEY_CTRL_F = "\x06"
KEY_CTRL_R = "\x12"
KEY_CTRL_T = "\x14"
KEY_CTRL_U = "\x15"
KEY_CTRL_V = "\x16"
KEY_CTRL_N = "\x0e"
KEY_CTRL_P = "\x10"
KEY_ENTER = "\n"
KEY_BACKSPACE_CODES = ("KEY_BACKSPACE", "\x7f", "\x08")
KEY_DELETE_CODES = ("KEY_DC", KEY_CTRL_D)

# Editor defaults from config
INDENT_WIDTH = settings.get("indent_width", 4)
INDENT_STR = " " * INDENT_WIDTH
MAX_UNDO = settings.get("max_undo", 100)
TERMINAL_HEIGHT = settings.get("terminal_height", 10)
FILE_FINDER_WIDTH = settings.get("file_finder_width", 30)
SUBPROCESS_TIMEOUT = settings.get("subprocess_timeout", 30)
SCROLL_MARGIN = settings.get("scroll_margin", 5)
TAB_WIDTH = settings.get("tab_width", 4)

# Placeholder filenames
NEW_FILE_NAME = "[new]"
