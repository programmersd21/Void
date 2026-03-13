# Copyright 2026 Bailey Beber and Soumalya Das
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.

import os
import json

CONFIG_DIR = os.path.expanduser("~/.config/void")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

DEFAULTS = {
    # Editor behavior
    "indent_width": 4,
    "max_undo": 100,
    "terminal_height": 10,
    "file_finder_width": 30,
    "subprocess_timeout": 30,
    "show_indent_guides": True,
    "show_hud": True,
    "splash_animation": True,
    "scroll_margin": 5,
    "show_line_numbers": True,
    "tab_width": 4,
    "max_recent_files": 20,
    "max_recent_display": 8,
    "auto_indent": True,
    "auto_pair": True,
    "trailing_newline": True,
    # New features
    "author": "Bailey Beber and Soumalya Das",
    "theme": "tokyo-night",
    "ai_enabled": True,
    "mcp_enabled": False,
    "gemini_api_key": "",
    "animations": True,
}


def load_config():
    config = dict(DEFAULTS)
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH) as f:
                user = json.load(f)
            config.update(user)
        except (json.JSONDecodeError, OSError):
            pass
    else:
        save_config(config)
    return config


def save_config(config):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)


def create_default_config():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if not os.path.exists(CONFIG_PATH):
        save_config(dict(DEFAULTS))


settings = load_config()
