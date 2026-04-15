"""Style inference engine using LLM."""

from openai import OpenAI

from academic_dreamer.config.settings import TEXT_MODEL_NAME, OPENROUTER_API_KEY, get_fallback_venue_prompt, get_venue_prompt


class StyleInferenceEngine:
    """LLM-based style inference for academic venues."""

    SYSTEM_PROMPT = """You are a style inference engine for academic illustrations.

Given a style string (venue name or free-form description), you must:
1. Match to known venue prompts if available (CVPR, ICLR, NeurIPS, Nature, etc.)
2. For unknown venues, infer appropriate style from the description
3. Output ONLY a style directive string for the Render Compiler

Known venues:
- CVPR: Professional, clean, minimal, high-contrast
- ICLR: Artistic, colorful, expressive, poster-friendly
- NeurIPS: Technical, detailed, academic
- Nature: Scientific, data-rich, journal quality

Output format: A single paragraph describing the exact style to use.
Do not include quotes or markdown formatting in your output."""

    def __init__(self) -> None:
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )

    def infer(self, style_input: str) -> tuple[str, bool]:
        """Infer style from input string.

        Returns:
            tuple[str, bool]: (style_directive, was_fallback)
        """
        # Try direct venue match first
        venue_prompt = get_venue_prompt(style_input)
        if venue_prompt:
            return venue_prompt, False

        # Try LLM inference for unknown venues
        try:
            response = self.client.chat.completions.create(
                model=TEXT_MODEL_NAME,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": f"Infer style for: {style_input}"},
                ],
                max_tokens=500,
            )
            inferred = response.choices[0].message.content or ""
            if inferred.strip():
                return inferred.strip(), False
        except Exception:
            pass

        # Fallback to generic academic style
        return get_fallback_venue_prompt(), True
