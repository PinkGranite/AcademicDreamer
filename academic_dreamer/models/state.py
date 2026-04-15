"""LangGraph state definition for AcademicDreamer."""

from typing import Annotated

from langgraph.graph import add_messages

from academic_dreamer.models.schemas import ReviewDecision, ReviewRecord, VisualSchema


class AcademicDreamerState(dict):
    """State managed by LangGraph orchestrator."""

    # Input
    idea: str
    style_raw: str

    # Classified
    target_type: str | None = None
    style_inferred: str | None = None

    # Stage outputs
    visual_schema: VisualSchema | None = None
    render_prompt: str | None = None

    # Generation
    image_data: str | None = None  # Base64 PNG

    # Review
    iteration: int = 0
    review_history: list[ReviewRecord] = []
    review_decision: ReviewDecision | None = None

    # Final output
    output_paths: dict[str, str] = {}  # {"png": "/path/xxx.png", "pdf": "/path/xxx.pdf"}

    # Error tracking
    error: str | None = None


# Message type for LangGraph
Messages = Annotated[list, add_messages]
