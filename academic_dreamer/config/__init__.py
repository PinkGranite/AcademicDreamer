"""Config package."""

from academic_dreamer.config.settings import CONFIG, get_fallback_venue_prompt, get_venue_prompt, load_config

__all__ = ["load_config", "get_venue_prompt", "get_fallback_venue_prompt", "CONFIG"]
