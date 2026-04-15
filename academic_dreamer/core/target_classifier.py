"""Target classifier for automatic target type detection."""

from openai import OpenAI

from academic_dreamer.config.settings import TEXT_MODEL_NAME, OPENROUTER_API_KEY

TARGET_TYPES = ["infograph", "architecture_diagram", "flowchart", "timeline", "data_visualization"]


class TargetClassifier:
    """Classifies user idea into appropriate target type."""

    SYSTEM_PROMPT = """You are a classifier that determines the appropriate diagram type for academic illustrations.

Available target types:
- infograph: Data-rich informational diagrams with statistics, metrics, comparisons
- architecture_diagram: System/component architecture, model structures, pipeline designs
- flowchart: Process flows, decision trees, algorithmic steps
- timeline: Chronological sequences, evolutionary paths, historical developments
- data_visualization: Charts, graphs, plots, statistical visualizations

Output ONLY the target type name. No explanation, no markdown."""


    def __init__(self) -> None:
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )

    def classify(self, idea: str) -> str:
        """Classify idea into target type.

        Args:
            idea: The user's academic concept

        Returns:
            Target type string
        """
        # First try keyword matching (fast path)
        idea_lower = idea.lower()

        # Architecture keywords
        arch_keywords = ["architecture", "model", "framework", "system", "module", "component", "network"]
        if any(kw in idea_lower for kw in arch_keywords):
            return "architecture_diagram"

        # Flowchart keywords
        flow_keywords = ["process", "pipeline", "step", "stage", "phase", "workflow", "algorithm"]
        if any(kw in idea_lower for kw in flow_keywords):
            return "flowchart"

        # Timeline keywords
        time_keywords = ["evolution", "history", "timeline", "chronological", "development over", "progress"]
        if any(kw in idea_lower for kw in time_keywords):
            return "timeline"

        # Infograph keywords
        info_keywords = ["statistics", "metrics", "comparison", "performance", "results", "data"]
        if any(kw in idea_lower for kw in info_keywords):
            return "infograph"

        # Fallback to LLM classification
        try:
            response = self.client.chat.completions.create(
                model=TEXT_MODEL_NAME,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": idea},
                ],
                max_tokens=20,
            )
            result = response.choices[0].message.content or ""
            result = result.strip().lower()

            # Validate result
            for target in TARGET_TYPES:
                if target.replace("_", " ") in result or target in result:
                    return target

        except Exception:
            pass

        # Default fallback
        return "architecture_diagram"
