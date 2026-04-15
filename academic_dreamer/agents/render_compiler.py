"""Render Compiler agent - Stage 2."""

from openai import OpenAI

from academic_dreamer.config.settings import TEXT_MODEL_NAME, OPENROUTER_API_KEY, PROMPTS_DIR
from academic_dreamer.models.schemas import RenderPrompt, VisualSchema


class RenderCompiler:
    """Stage 2 agent that compiles Visual Schema + Style into final render prompt."""

    RENDER_PROMPT_PATH = PROMPTS_DIR / "render_compile.md"

    def __init__(self) -> None:
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )
        self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        """Load the render compile prompt template."""
        if self.RENDER_PROMPT_PATH.exists():
            with open(self.RENDER_PROMPT_PATH) as f:
                self.prompt_template = f.read()
        else:
            self.prompt_template = self._get_default_template()

    def _get_default_template(self) -> str:
        """Default template if file not found."""
        return """**Style Reference & Execution Instructions:**

1.  **Art Style (Visio/Illustrator Aesthetic):**
    Generate a **professional academic architecture diagram** suitable for a top-tier computer science paper.
    * **Visuals:** Flat vector graphics, distinct geometric shapes, clean thin outlines, and soft pastel fills.
    * **Layout:** Strictly follow the spatial arrangement defined below.
    * **Vibe:** Technical, precise, clean white background.

2.  **CRITICAL TEXT CONSTRAINTS:**
    * **DO NOT render meta-labels:** Do not write words like "ZONE 1", "LAYOUT CONFIGURATION", "Input", "Output".
    * **ONLY render "Key Text Labels":** Only text inside double quotes listed under "Key Text Labels" should appear.

3.  **Visual Schema Execution:**
    Translate the following structural blueprint into the final image."""

    async def compile(
        self, visual_schema: VisualSchema, style_directive: str
    ) -> RenderPrompt:
        """Compile Visual Schema + Style into final render prompt.

        Args:
            visual_schema: The structured visual schema from Stage 1
            style_directive: The inferred style directive

        Returns:
            RenderPrompt ready for image generation
        """
        # Build the combined prompt
        schema_text = self._schema_to_text(visual_schema)

        response = self.client.chat.completions.create(
            model=TEXT_MODEL_NAME,
            messages=[
                {"role": "system", "content": self.prompt_template},
                {"role": "user", "content": f"Style: {style_directive}\n\nSchema:\n{schema_text}"},
            ],
            max_tokens=1500,
        )

        content = response.choices[0].message.content or ""

        # Extract key text labels from zones
        key_labels = []
        for zone in visual_schema.zones:
            key_labels.extend(zone.get("key_text_labels", []))

        return RenderPrompt(
            style_directives=style_directive,
            visual_schema=content,
            key_text_labels=key_labels,
        )

    def _schema_to_text(self, schema: VisualSchema) -> str:
        """Convert VisualSchema to text format."""
        lines = [
            "[LAYOUT CONFIGURATION]",
            f"* **Selected Layout**: {schema.layout_type}",
            f"* **Composition Logic**: {schema.composition_logic}",
            f"* **Color Palette**: {schema.color_palette}",
            "",
        ]

        for i, zone in enumerate(schema.zones, 1):
            lines.append(f"[ZONE {i}: {zone.get('label', 'Unknown')}]")
            lines.append(f"* **Container**: {zone.get('container', '')}")
            lines.append(f"* **Visual Structure**: {zone.get('visual_structure', '')}")
            labels = zone.get("key_text_labels", [])
            if labels:
                label_strs = ['"' + l + '"' for l in labels]
                lines.append("* **Key Text Labels**: " + " ".join(label_strs))
            lines.append("")

        if schema.connections:
            lines.append("[CONNECTIONS]")
            for conn in schema.connections:
                lines.append(f"* {conn}")

        return "\n".join(lines)
