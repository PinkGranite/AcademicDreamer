"""Configuration management for AcademicDreamer."""

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

load_dotenv()

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent

# API Configuration
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
# Text model for agents (schema, style, compilation) - use image model since it supports text too
TEXT_MODEL_NAME = os.environ.get("TEXT_MODEL_NAME", "google/gemini-3.1-flash-image-preview")
# Image model for final generation
IMAGE_MODEL_NAME = os.environ.get("IMAGE_MODEL_NAME", "google/gemini-3.1-flash-image-preview")

# Generation defaults
DEFAULT_MAX_RETRIES = 3
RETRY_DELAY = 2.0

# Review defaults
DEFAULT_ITERATIONS = 2
DEFAULT_THRESHOLD = 0.7
MAX_ITERATIONS_CAP = 5

# Output defaults
DEFAULT_OUTPUT_FORMATS = ["png"]
PDF_DPI = 300

# Paths
CONFIG_PATH = PROJECT_ROOT / "config" / "defaults.yaml"
PROMPTS_DIR = PROJECT_ROOT / "academic_dreamer" / "prompts"
VENUES_DIR = PROMPTS_DIR / "venues"


def load_config() -> dict[str, Any]:
    """Load configuration from YAML file."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f) or {}
    return {}


def get_venue_prompt(venue: str) -> str | None:
    """Get venue-specific prompt if available."""
    venue_file = VENUES_DIR / f"{venue.lower().replace(' ', '_')}.md"
    if venue_file.exists():
        with open(venue_file) as f:
            return f.read()

    # Try exact match
    for file in VENUES_DIR.glob("*.md"):
        if file.stem.lower() == venue.lower():
            with open(file) as f:
                return f.read()
    return None


def get_fallback_venue_prompt() -> str:
    """Get fallback template for unknown venues."""
    template_path = VENUES_DIR / "_template.md"
    if template_path.exists():
        with open(template_path) as f:
            return f.read()
    return "Professional academic illustration style"


# Load config on module import
CONFIG = load_config()
