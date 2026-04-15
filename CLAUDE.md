# AcademicDreamer

## Project Overview

Multi-agent orchestration system for generating academic illustrations using LangGraph. Transforms paper concepts into professional diagrams through two-stage prompt compilation.

## Architecture

```
User Input → Target Classifier → Style Inference
                                    ↓
                          Visual Architect (Stage 1)
                                    ↓
                          Render Compiler (Stage 2)
                                    ↓
                          Generation Pipeline
                                    ↓
                          Review Iteration (Continuous)
                                    ↓
                               PNG + PDF Output
```

## Key Files

| File | Purpose |
|------|---------|
| `academic_dreamer/core/orchestrator.py` | LangGraph state machine, main workflow |
| `academic_dreamer/core/generation_pipeline.py` | Image generation via OpenRouter API |
| `academic_dreamer/core/review_iteration.py` | Continuous review loop with context |
| `academic_dreamer/agents/visual_architect.py` | Stage 1: Schema from paper content |
| `academic_dreamer/agents/render_compiler.py` | Stage 2: Final render prompt |
| `academic_dreamer/agents/style_inference.py` | LLM-based venue/style inference |
| `academic_dreamer/models/schemas.py` | Pydantic models for all data contracts |
| `academic_dreamer/models/state.py` | LangGraph state definition |

## Data Flow

1. **Input**: `UserInput` (idea, style, target_type, control)
2. **Classify**: `TargetClassifier` → target_type
3. **Infer Style**: `StyleInferenceEngine` → style_directive
4. **Stage 1**: `VisualArchitect` → `VisualSchema`
5. **Stage 2**: `RenderCompiler` → final_prompt
6. **Generate**: `GenerationPipeline` → Base64 PNG
7. **Review**: `ReviewIteration` (loop until approved or max_iterations)
8. **Output**: `OutputFormatter` → PNG/PDF files

## Configuration

- `academic_dreamer/config/settings.py` - Environment vars, API config
- `academic_dreamer/config/defaults.yaml` - Default values
- `.env.example` - API key template

## Control Arguments

```python
@dataclass
class Control:
    max_iterations: int = 2  # 0 = skip review
    output_formats: list = ["png"]
    quality_threshold: float = 0.7
```

## Dependencies

- **LangGraph**: Stateful multi-agent orchestration
- **OpenAI**: API client for OpenRouter
- **Pillow**: PNG → PDF conversion

## Important Notes

1. **API Key**: Set `OPENROUTER_API_KEY` in `.env`
2. **Review Loop**: Controlled by `max_iterations`, uses LangGraph checkpointing for context
3. **Style Fallback**: Unknown venues → LLM inference → generic academic style (with warning)
4. **Max Iterations Cap**: Hard limit of 5 regardless of config
