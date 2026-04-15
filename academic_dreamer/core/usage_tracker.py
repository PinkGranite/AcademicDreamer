"""Token usage tracking for API calls."""

from dataclasses import dataclass, field

from academic_dreamer.models.schemas import TokenUsage


# OpenRouter pricing per 1M tokens (approximate, update as needed)
# gemini-3.1-flash-preview: $0.075/M input, $0.15/M output
# gemini-3.1-flash-image-preview: $0.075/M input, $0.15/M output
OPENROUTER_PRICING: dict[str, tuple[float, float]] = {
    "gemini-3.1-flash-preview": (0.075, 0.15),  # (input_cost, output_cost) per 1M tokens
    "gemini-3.1-flash-image-preview": (0.075, 0.15),
    "google/gemini-3.1-flash-preview": (0.075, 0.15),
    "google/gemini-3.1-flash-image-preview": (0.075, 0.15),
    "google/gemini-3.1-flash-image-preview-20260226": (0.075, 0.15),
}


@dataclass
class UsageTracker:
    """Tracks token usage across multiple API calls.

    Usage:
        tracker = UsageTracker()
        tracker.add_usage(prompt_tokens=100, completion_tokens=50)
        tracker.add_usage(prompt_tokens=200, completion_tokens=100)

        usage = tracker.get_total()
        print(f"Total: {usage.total_tokens} tokens, ${usage.cost:.4f}")
    """

    _totals: dict = field(default_factory=lambda: {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "cost": 0.0,
    })
    _calls: list[dict] = field(default_factory=list)

    def add_usage(
        self,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int | None = None,
        model: str | None = None,
        cost: float | None = None,
    ) -> None:
        """Add usage from a single API call.

        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            total_tokens: Total tokens (calculated if not provided)
            model: Model name for cost calculation
            cost: Explicit cost (calculated from model pricing if not provided)
        """
        if total_tokens is None:
            total_tokens = prompt_tokens + completion_tokens

        if cost is None and model:
            cost = self._calculate_cost(model, prompt_tokens, completion_tokens)

        self._totals["prompt_tokens"] += prompt_tokens
        self._totals["completion_tokens"] += completion_tokens
        self._totals["total_tokens"] += total_tokens
        self._totals["cost"] += cost or 0.0

        self._calls.append({
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "model": model,
            "cost": cost,
        })

    def add_from_response(self, response, model: str | None = None) -> None:
        """Add usage directly from OpenAI API response object.

        Args:
            response: OpenAI API response with usage attribute
            model: Optional model name for cost calculation
        """
        if hasattr(response, "usage") and response.usage:
            usage = response.usage
            self.add_usage(
                prompt_tokens=usage.prompt_tokens or 0,
                completion_tokens=usage.completion_tokens or 0,
                total_tokens=usage.total_tokens or None,
                model=model or getattr(response, "model", None),
            )

    def _calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost based on model pricing."""
        # Normalize model name
        model_lower = model.lower()

        # Find matching pricing
        for model_pattern, (input_cost, output_cost) in OPENROUTER_PRICING.items():
            if model_pattern in model_lower:
                cost = (prompt_tokens * input_cost / 1_000_000) + \
                       (completion_tokens * output_cost / 1_000_000)
                return cost

        # Default pricing if model not found (conservative estimate)
        input_cost, output_cost = 0.075, 0.15
        cost = (prompt_tokens * input_cost / 1_000_000) + \
               (completion_tokens * output_cost / 1_000_000)
        return cost

    def get_total(self) -> TokenUsage:
        """Get total usage across all calls."""
        return TokenUsage(
            prompt_tokens=self._totals["prompt_tokens"],
            completion_tokens=self._totals["completion_tokens"],
            total_tokens=self._totals["total_tokens"],
            cost=self._totals["cost"],
        )

    def get_calls(self) -> list[dict]:
        """Get list of individual API calls."""
        return list(self._calls)

    def get_summary(self) -> dict:
        """Get a summary dict of usage."""
        total = self.get_total()
        return {
            "total_tokens": total.total_tokens,
            "prompt_tokens": total.prompt_tokens,
            "completion_tokens": total.completion_tokens,
            "total_cost_usd": total.cost,
            "num_api_calls": len(self._calls),
        }

    def reset(self) -> None:
        """Reset all counters."""
        self._totals = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "cost": 0.0,
        }
        self._calls = []


# Global singleton for tracking usage across the application
_global_tracker: UsageTracker | None = None


def get_usage_tracker() -> UsageTracker:
    """Get the global UsageTracker singleton."""
    global _global_tracker
    if _global_tracker is None:
        _global_tracker = UsageTracker()
    return _global_tracker


def reset_usage_tracker() -> None:
    """Reset the global tracker."""
    global _global_tracker
    if _global_tracker is not None:
        _global_tracker.reset()
