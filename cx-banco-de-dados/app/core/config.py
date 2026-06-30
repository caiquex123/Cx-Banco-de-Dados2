from ..config import get_settings

settings = get_settings()

# This is a placeholder - the actual config module already exists at app/config.py
# This file is kept for backwards compatibility

def get_settings_wrapper():
    return settings
