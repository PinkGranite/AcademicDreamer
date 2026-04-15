#!/bin/bash
# CLI Example: Using AcademicDreamer from command line

# Basic usage
python -m academic_dreamer.cli --input examples/request.json

# With overrides
python -m academic_dreamer.cli --input examples/request.json --max-iterations 3 --output-formats png,pdf

# Specify output directory
python -m academic_dreamer.cli --input examples/request.json --output-dir ./output
