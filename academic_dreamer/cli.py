"""CLI interface for AcademicDreamer."""

import asyncio
import json
import sys
from pathlib import Path

import click

from academic_dreamer.core.orchestrator import Orchestrator
from academic_dreamer.core.usage_tracker import UsageTracker, reset_usage_tracker
from academic_dreamer.models.schemas import Control, UserInput


@click.command()
@click.option("--input", "-i", "input_file", type=click.Path(exists=True), required=True, help="Input JSON file")
@click.option("--output-dir", "-o", type=click.Path(), help="Output directory")
@click.option("--max-iterations", type=int, help="Override max iterations")
@click.option("--output-formats", type=str, help="Comma-separated formats (png,pdf)")
@click.option("--quality-threshold", type=float, help="Override quality threshold")
@click.option("--track-usage", is_flag=True, default=False, help="Track and display token usage")
def main(
    input_file: str,
    output_dir: str | None,
    max_iterations: int | None,
    output_formats: str | None,
    quality_threshold: float | None,
    track_usage: bool,
) -> None:
    """AcademicDreamer - Multi-agent academic illustration generator."""

    # Reset usage tracker if tracking
    if track_usage:
        reset_usage_tracker()

    # Load input
    with open(input_file) as f:
        data = json.load(f)

    # Override control args if provided
    control = Control()
    if max_iterations is not None:
        control.max_iterations = max_iterations
    if output_formats is not None:
        control.output_formats = [fmt.strip() for fmt in output_formats.split(",")]
    if quality_threshold is not None:
        control.quality_threshold = quality_threshold

    # Create user input
    user_input = UserInput(
        idea=data["idea"],
        style=data["style"],
        target_type=data.get("target_type"),
        control=control,
    )

    # Create output dir
    output_path = Path(output_dir) if output_dir else None

    # Create usage tracker if tracking
    usage_tracker = UsageTracker() if track_usage else None

    # Run orchestration
    orchestrator = Orchestrator(user_input, output_path, usage_tracker)

    try:
        result = asyncio.run(orchestrator.run())

        # Print output paths
        output_paths = result.get("output_paths", {})
        if output_paths:
            click.echo("Generated files:")
            for fmt, path in output_paths.items():
                click.echo(f"  {fmt}: {path}")

        # Print usage if tracking
        if track_usage and usage_tracker:
            summary = usage_tracker.get_summary()
            click.echo("\nToken Usage:")
            click.echo(f"  API calls: {summary['num_api_calls']}")
            click.echo(f"  Prompt tokens: {summary['prompt_tokens']:,}")
            click.echo(f"  Completion tokens: {summary['completion_tokens']:,}")
            click.echo(f"  Total tokens: {summary['total_tokens']:,}")
            if summary["total_cost_usd"] is not None:
                click.echo(f"  Estimated cost: ${summary['total_cost_usd']:.6f}")

        if result.get("error"):
            click.echo(f"Warning: {result['error']}", err=True)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
