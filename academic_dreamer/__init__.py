"""AcademicDreamer - Multi-agent academic illustration system."""

from academic_dreamer.main import generate_academic_illustration
from academic_dreamer.models.schemas import (
    Control,
    GenerationResult,
    RenderPrompt,
    ReviewDecision,
    ReviewRecord,
    UserInput,
    VisualSchema,
)

__version__ = "0.1.0"

__all__ = [
    "generate_academic_illustration",
    "UserInput",
    "Control",
    "VisualSchema",
    "RenderPrompt",
    "GenerationResult",
    "ReviewRecord",
    "ReviewDecision",
]
