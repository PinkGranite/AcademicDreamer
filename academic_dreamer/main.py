"""Main API entry point for AcademicDreamer."""

from pathlib import Path
from typing import TYPE_CHECKING

from academic_dreamer.core.orchestrator import Orchestrator
from academic_dreamer.core.usage_tracker import UsageTracker
from academic_dreamer.models.schemas import Control, UserInput

if TYPE_CHECKING:
    from academic_dreamer.core.usage_tracker import TokenUsage


async def generate_academic_illustration(
    idea: str,
    style: str,
    target_type: str | None = None,
    *,
    max_iterations: int = 2,
    output_formats: list[str] | None = None,
    quality_threshold: float = 0.7,
    output_dir: Path | None = None,
    track_usage: bool = False,
) -> dict:
    """Generate academic illustration.

    Args:
        idea: Academic concept/paper content
        style: Venue (CVPR, ICLR) or free-form style description
        target_type: Optional diagram type (auto-detected if None)
        max_iterations: Max review iterations (0=skip review)
        output_formats: Output formats (default: ["png"])
        quality_threshold: Quality gate for review (0.0-1.0)
        output_dir: Output directory (default: ./output)
        track_usage: Whether to track token usage

    Returns:
        Dict with output_paths and metadata. If track_usage=True, includes 'usage' key.
    """
    usage_tracker = UsageTracker() if track_usage else None

    user_input = UserInput(
        idea=idea,
        style=style,
        target_type=target_type,
        control=Control(
            max_iterations=max_iterations,
            output_formats=output_formats or ["png"],
            quality_threshold=quality_threshold,
        ),
    )

    orchestrator = Orchestrator(user_input, output_dir, usage_tracker)
    result = await orchestrator.run()

    response = {
        "output_paths": result.get("output_paths", {}),
        "iteration": result.get("iteration", 0),
        "quality_score": getattr(result.get("review_decision"), "quality_score", None),
        "approved": getattr(result.get("review_decision"), "approved", False),
        "error": result.get("error"),
    }

    if track_usage and usage_tracker:
        response["usage"] = usage_tracker.get_summary()

    return response


def get_usage_from_tracker(tracker: UsageTracker) -> "TokenUsage":
    """Get total token usage from a tracker.

    Args:
        tracker: UsageTracker instance

    Returns:
        TokenUsage with totals
    """
    return tracker.get_total()
