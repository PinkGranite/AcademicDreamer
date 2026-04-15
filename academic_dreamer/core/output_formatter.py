"""Output formatter for PNG and PDF export."""

from pathlib import Path

from academic_dreamer.models.schemas import GenerationResult


class OutputFormatter:
    """Handles final output formatting and file writing."""

    def __init__(self, output_dir: Path | None = None) -> None:
        self.output_dir = output_dir or Path.cwd() / "output"

    def format(
        self,
        result: GenerationResult,
        filename: str,
        formats: list[str],
    ) -> dict[str, Path]:
        """Format and save generation result.

        Args:
            result: The generation result with image data
            filename: Base filename without extension
            formats: List of formats to output (png, pdf)

        Returns:
            Dict mapping format to output path
        """
        from academic_dreamer.core.generation_pipeline import GenerationPipeline

        self.output_dir.mkdir(parents=True, exist_ok=True)
        output_paths: dict[str, Path] = {}

        # Always save PNG
        png_path = self.output_dir / f"{filename}.png"
        GenerationPipeline.save_png(result.image_data, png_path)
        output_paths["png"] = png_path

        # Convert to PDF if requested
        if "pdf" in formats:
            pdf_path = self.output_dir / f"{filename}.pdf"
            GenerationPipeline.convert_to_pdf(png_path, pdf_path)
            output_paths["pdf"] = pdf_path

        return output_paths
