#!/usr/bin/env python3
"""
API Example: Using AcademicDreamer in a Python workflow

This example shows how to import and use AcademicDreamer in a Python script.
"""

import asyncio
from academic_dreamer import generate_academic_illustration


async def main():
    """Generate an academic illustration using the Python API."""

    result = await generate_academic_illustration(
        idea="A novel transformer architecture for image segmentation",
        style="CVPR 2024",
        target_type="architecture_diagram",
        max_iterations=2,
        output_formats=["png"],
    )

    print("Generation complete!")
    print(f"Output paths: {result['output_paths']}")
    print(f"Iterations: {result['iteration']}")
    print(f"Quality score: {result['quality_score']}")
    print(f"Approved: {result['approved']}")

    return result


# Or use directly with more control:
async def advanced_example():
    """Direct usage with full control over the orchestrator."""

    from academic_dreamer import UserInput, Control
    from academic_dreamer.core import Orchestrator

    user_input = UserInput(
        idea="A diffusion model for text-to-image generation with classifier-free guidance",
        style="ICLR 2025",
        target_type="architecture_diagram",
        control=Control(
            max_iterations=3,
            output_formats=["png", "pdf"],
            quality_threshold=0.8,
        ),
    )

    orchestrator = Orchestrator(user_input, output_dir="./output")
    result = await orchestrator.run()

    print(f"Generated: {result['output_paths']}")
    return result


if __name__ == "__main__":
    # Run the basic example
    result = asyncio.run(main())

    # Or run the advanced example
    # result = asyncio.run(advanced_example())
