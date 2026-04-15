"""Visual Architect agent - Stage 1."""

from openai import OpenAI

from academic_dreamer.config.settings import TEXT_MODEL_NAME, OPENROUTER_API_KEY, PROMPTS_DIR
from academic_dreamer.models.schemas import VisualSchema


class VisualArchitect:
    """Stage 1 agent that generates Visual Schema from academic concept."""

    LAYOUT_PROMPT_PATH = PROMPTS_DIR / "visual_schema.md"

    def __init__(self) -> None:
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )
        self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        """Load the visual schema prompt template."""
        if self.LAYOUT_PROMPT_PATH.exists():
            with open(self.LAYOUT_PROMPT_PATH) as f:
                self.prompt_template = f.read()
        else:
            # Fallback to inline template
            self.prompt_template = self._get_default_template()

    def _get_default_template(self) -> str:
        """Default template if file not found."""
        return """# Role
You are a Visual Architect for CVPR/NeurIPS papers. Transform abstract paper logic into structured geometric visual instructions.

# Task
Analyze the provided academic concept and output a VISUAL SCHEMA.

# Output Format
---BEGIN PROMPT---

[Style & Meta-Instructions]
High-fidelity scientific schematic, technical vector illustration, clean white background.

[LAYOUT CONFIGURATION]
* **Selected Layout**: [Linear/Cyclic/Hierarchical/Parallel/Central]
* **Composition Logic**: [Zone arrangement description]
* **Color Palette**: [Professional colors]

[ZONE 1: LOCATION - LABEL]
* **Container**: [Shape description]
* **Visual Structure**: [Visual elements]
* **Key Text Labels**: ["Label1"]

... (add zones as needed)

[CONNECTIONS]
1. [Connection description]

---END PROMPT---"""

    async def generate_schema(self, idea: str, target_type: str | None = None) -> VisualSchema:
        """Generate Visual Schema from academic idea.

        Args:
            idea: The academic concept/paper content
            target_type: Optional target diagram type

        Returns:
            VisualSchema with layout and zone definitions
        """
        user_message = idea
        if target_type:
            user_message = f"Target type: {target_type}\n\n{idea}"

        response = self.client.chat.completions.create(
            model=TEXT_MODEL_NAME,
            messages=[
                {"role": "system", "content": self.prompt_template},
                {"role": "user", "content": user_message},
            ],
            max_tokens=2000,
        )

        content = response.choices[0].message.content or ""
        return self._parse_schema(content)

    def _parse_schema(self, raw_output: str) -> VisualSchema:
        """Parse raw LLM output into VisualSchema model."""
        # Extract sections from ---BEGIN PROMPT--- ... ---END PROMPT---
        start = raw_output.find("---BEGIN PROMPT---")
        end = raw_output.find("---END PROMPT---")

        if start != -1 and end != -1:
            prompt_content = raw_output[start + 17 : end].strip()
        else:
            prompt_content = raw_output

        # Parse layout type
        layout_type = "Linear Pipeline"  # default
        if "Cyclic" in prompt_content or "Iterative" in prompt_content:
            layout_type = "Cyclic/Iterative"
        elif "Hierarchical" in prompt_content or "Stack" in prompt_content:
            layout_type = "Hierarchical Stack"
        elif "Parallel" in prompt_content or "Dual" in prompt_content:
            layout_type = "Parallel/Dual-Stream"
        elif "Central" in prompt_content or "Hub" in prompt_content:
            layout_type = "Central Hub"

        # Extract zones (simplified parsing)
        zones = []
        zone_sections = prompt_content.split("[ZONE")
        for section in zone_sections[1:]:
            zone = self._parse_zone(section)
            if zone:
                zones.append(zone)

        # Extract connections
        connections = []
        if "CONNECTIONS" in prompt_content:
            conn_start = prompt_content.find("[CONNECTIONS]")
            if conn_start != -1:
                conn_section = prompt_content[conn_start:].split("\n")[1:6]
                for line in conn_section:
                    if line.strip() and line[0].isdigit():
                        connections.append(line.split(".", 1)[1].strip())

        # Extract color palette
        color_palette = "Professional Pastel (Azure Blue, Slate Grey, Coral Orange, Mint Green)"
        if "Color Palette" in prompt_content:
            for line in prompt_content.split("\n"):
                if "Color Palette" in line:
                    color_palette = line.split(":", 1)[1].strip()
                    break

        return VisualSchema(
            layout_type=layout_type,
            composition_logic="Generated from Visual Architect",
            color_palette=color_palette,
            zones=zones,
            connections=connections,
        )

    def _parse_zone(self, section: str) -> dict | None:
        """Parse a single zone section."""
        lines = section.split("\n")
        if not lines:
            return None

        # First line has zone name
        name_part = lines[0].split(":", 1)
        if len(name_part) < 2:
            return None

        zone: dict[str, str] = {
            "label": name_part[1].strip().rstrip("]"),
            "container": "",
            "visual_structure": "",
            "key_text_labels": [],
        }

        # Parse container, structure, labels
        current_key = None
        for line in lines[1:]:
            line = line.strip()
            if line.startswith("**Container**"):
                current_key = "container"
                zone["container"] = line.split("**Container**")[1].strip().lstrip(":").strip()
            elif line.startswith("**Visual Structure**"):
                current_key = "visual_structure"
                zone["visual_structure"] = line.split("**Visual Structure**")[1].strip().lstrip(":").strip()
            elif line.startswith("**Key Text Labels**"):
                current_key = "key_text_labels"
                # Parse quoted labels
                import re
                labels = re.findall(r'"([^"]+)"', line)
                zone["key_text_labels"] = labels
            elif current_key == "container" and line:
                zone["container"] += " " + line
            elif current_key == "visual_structure" and line:
                zone["visual_structure"] += " " + line

        return zone if zone.get("label") else None
