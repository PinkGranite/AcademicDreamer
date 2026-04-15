"""Data schemas for AcademicDreamer."""

from typing import Literal

from pydantic import BaseModel, Field


class Control(BaseModel):
    """Control arguments for the generation pipeline."""

    max_iterations: int = Field(default=2, ge=0, le=5, description="Max review iterations (0=skip review)")
    output_formats: list[Literal["png", "pdf"]] = Field(default_factory=lambda: ["png"])
    quality_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class UserInput(BaseModel):
    """User input schema for AcademicDreamer."""

    idea: str = Field(description="Academic concept/paper content")
    style: str = Field(description="Venue (CVPR, ICLR) or free-form style description")
    target_type: str | None = Field(
        default=None,
        description="infograph/architecture_diagram/flowchart/timeline, auto-detected if null",
    )
    control: Control = Field(default_factory=Control)


class VisualSchema(BaseModel):
    """Output from Visual Architect agent (Stage 1)."""

    layout_type: str = Field(description="Selected layout: Linear/Cyclic/Hierarchical/Parallel/Central")
    composition_logic: str = Field(description="How zones are arranged")
    color_palette: str = Field(description="Color scheme")
    zones: list[dict] = Field(description="List of zone definitions with containers, visuals, labels")
    connections: list[str] = Field(description="Connection descriptions")


class RenderPrompt(BaseModel):
    """Output from Render Compiler agent (Stage 2)."""

    style_directives: str = Field(description="Style execution instructions")
    visual_schema: str = Field(description="Visual schema to render")
    key_text_labels: list[str] = Field(description="Only text labels to render in image")


class TokenUsage(BaseModel):
    """Token usage tracking for API calls."""

    prompt_tokens: int = Field(default=0, description="Tokens in the prompt")
    completion_tokens: int = Field(default=0, description="Tokens in the completion")
    total_tokens: int = Field(default=0, description="Total tokens used")
    cost: float | None = Field(default=None, description="Estimated cost in USD")

    def __add__(self, other: "TokenUsage") -> "TokenUsage":
        """Add two TokenUsage objects together."""
        return TokenUsage(
            prompt_tokens=self.prompt_tokens + other.prompt_tokens,
            completion_tokens=self.completion_tokens + other.completion_tokens,
            total_tokens=self.total_tokens + other.total_tokens,
            cost=(self.cost or 0) + (other.cost or 0),
        )


class GenerationResult(BaseModel):
    """Result from image generation."""

    image_data: str = Field(description="Base64 encoded PNG data")
    quality_score: float | None = Field(default=None, description="Optional quality score")
    generation_metadata: dict = Field(default_factory=dict)
    token_usage: TokenUsage | None = Field(default=None, description="Token usage for this generation")


class ReviewRecord(BaseModel):
    """Record of a single review iteration."""

    iteration: int
    quality_score: float
    feedback: str
    approved: bool


class ReviewDecision(BaseModel):
    """Decision from review iteration."""

    approved: bool = Field(description="Whether to accept the current generation")
    quality_score: float = Field(description="Quality score 0.0-1.0")
    feedback: str = Field(description="Actionable feedback for improvement")
    should_retry: bool = Field(description="Whether another iteration is warranted")
