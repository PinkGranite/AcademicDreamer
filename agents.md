# AcademicDreamer - Multi-Agent System

## Agent Roles

### Stage 1: Visual Architect

**File**: `academic_dreamer/agents/visual_architect.py`

**Purpose**: Transforms abstract academic concept into structured Visual Schema

**Inputs**:
- `idea`: Academic concept/paper content
- `target_type`: Optional diagram type

**Outputs**: `VisualSchema` with:
- `layout_type`: Selected layout strategy
- `composition_logic`: Zone arrangement
- `color_palette`: Color scheme
- `zones`: List of zone definitions
- `connections`: Connection descriptions

**Prompt Template**: `academic_dreamer/prompts/visual_schema.md`

---

### Stage 2: Render Compiler

**File**: `academic_dreamer/agents/render_compiler.py`

**Purpose**: Fuses Visual Schema + Style Directive into final render prompt

**Inputs**:
- `visual_schema`: Structured schema from Stage 1
- `style_directive`: Inferred or specified style

**Outputs**: `RenderPrompt` with:
- `style_directives`: Style execution instructions
- `visual_schema`: Visual schema text
- `key_text_labels`: Only labels to render

**Prompt Template**: `academic_dreamer/prompts/render_compile.md`

---

### Style Inference Engine

**File**: `academic_dreamer/agents/style_inference.py`

**Purpose**: LLM-based style inference for venues

**Behavior**:
1. Check venue directory for known venues (CVPR, ICLR, NeurIPS, Nature)
2. If unknown → LLM inference
3. If inference fails → fallback to generic academic style + warning

**Venues**: `academic_dreamer/prompts/venues/`

---

## Support Agents

### Target Classifier

**File**: `academic_dreamer/core/target_classifier.py`

**Purpose**: Auto-detect diagram type from idea

**Types**: `infograph`, `architecture_diagram`, `flowchart`, `timeline`, `data_visualization`

---

### Review Iteration

**File**: `academic_dreamer/core/review_iteration.py`

**Purpose**: Continuous quality review with context accumulation

**Inputs**:
- Current generation (Base64 image)
- Review history (previous iterations)

**Outputs**: `ReviewDecision` with:
- `approved`: Boolean
- `quality_score`: 0.0-1.0
- `feedback`: Actionable feedback
- `should_retry`: Whether to loop

---

## Orchestration

**File**: `academic_dreamer/core/orchestrator.py`

**Framework**: LangGraph

**State**: `AcademicDreamerState`
- Maintains context across all agents
- Enables review loop with checkpointing
- Coordinates data flow between agents

---

## Message Passing

All agents use OpenAI-compatible API via LangChain/OpenRouter:

```python
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)
```
