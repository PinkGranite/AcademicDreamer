"""Generation pipeline with nanobanana invocation and PDF export."""

import base64
import time
from pathlib import Path

from openai import OpenAI

from academic_dreamer.config.settings import DEFAULT_MAX_RETRIES, IMAGE_MODEL_NAME, OPENROUTER_API_KEY, RETRY_DELAY
from academic_dreamer.models.schemas import GenerationResult, TokenUsage
from academic_dreamer.core.usage_tracker import UsageTracker


class GenerationPipeline:
    """Handles image generation via OpenRouter API with retry logic."""

    def __init__(self, max_retries: int = DEFAULT_MAX_RETRIES, usage_tracker: UsageTracker | None = None) -> None:
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )
        self.max_retries = max_retries
        self.usage_tracker = usage_tracker

    def generate(self, prompt: str) -> GenerationResult:
        """Generate image from prompt with retry logic.

        Args:
            prompt: The final render prompt

        Returns:
            GenerationResult with Base64 PNG data
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=IMAGE_MODEL_NAME,
                    messages=[{"role": "user", "content": prompt}],
                    extra_body={"modalities": ["image", "text"]},
                )

                message = response.choices[0].message

                # Track token usage if available
                token_usage = None
                if hasattr(response, "usage") and response.usage:
                    usage = response.usage
                    token_usage = TokenUsage(
                        prompt_tokens=usage.prompt_tokens or 0,
                        completion_tokens=usage.completion_tokens or 0,
                        total_tokens=usage.total_tokens or 0,
                    )
                    if self.usage_tracker:
                        self.usage_tracker.add_from_response(response, IMAGE_MODEL_NAME)

                # Extract image from response
                if hasattr(message, "images") and message.images:
                    image_data = message.images[0]["image_url"]["url"]
                    return GenerationResult(
                        image_data=image_data,
                        generation_metadata={
                            "attempt": attempt + 1,
                            "model": IMAGE_MODEL_NAME,
                        },
                        token_usage=token_usage,
                    )

                # Fallback: check for base64 in content
                if hasattr(message, "content") and message.content:
                    # Try to extract base64 image from content
                    import re
                    b64_match = re.search(r"data:image/[^;]+;base64,([A-Za-z0-9+/=]+)", message.content)
                    if b64_match:
                        return GenerationResult(
                            image_data=f"data:image/png;base64,{b64_match.group(1)}",
                            generation_metadata={
                                "attempt": attempt + 1,
                                "model": IMAGE_MODEL_NAME,
                            },
                            token_usage=token_usage,
                        )

            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))  # Exponential backoff

        # All retries failed
        raise RuntimeError(f"Image generation failed after {self.max_retries} attempts: {last_error}")

    @staticmethod
    def save_png(image_data: str, output_path: Path) -> Path:
        """Save Base64 image data to PNG file.

        Args:
            image_data: Base64 encoded image (data URL or raw)
            output_path: Destination path

        Returns:
            Path to saved file
        """
        # Extract base64 content
        if "base64," in image_data:
            b64_content = image_data.split("base64,", 1)[1]
        else:
            b64_content = image_data

        # Decode and save
        png_data = base64.b64decode(b64_content)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(png_data)

        return output_path

    @staticmethod
    def convert_to_pdf(png_path: Path, output_path: Path) -> Path:
        """Convert PNG to PDF.

        Args:
            png_path: Source PNG file
            output_path: Destination PDF path

        Returns:
            Path to saved PDF
        """
        from PIL import Image

        img = Image.open(png_path)
        # Convert to RGB if necessary
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PDF", resolution=300)

        return output_path
