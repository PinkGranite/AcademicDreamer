"""LangGraph orchestrator for AcademicDreamer."""

from pathlib import Path
from typing import Any

from langgraph.graph import END, START, StateGraph

from academic_dreamer.agents.render_compiler import RenderCompiler
from academic_dreamer.agents.style_inference import StyleInferenceEngine
from academic_dreamer.agents.visual_architect import VisualArchitect
from academic_dreamer.core.generation_pipeline import GenerationPipeline
from academic_dreamer.core.output_formatter import OutputFormatter
from academic_dreamer.core.review_iteration import ReviewIteration
from academic_dreamer.core.target_classifier import TargetClassifier
from academic_dreamer.core.usage_tracker import UsageTracker, get_usage_tracker
from academic_dreamer.models.schemas import Control, GenerationResult, UserInput
from academic_dreamer.models.state import AcademicDreamerState


class Orchestrator:
    """Main orchestrator for the AcademicDreamer multi-agent system."""

    def __init__(
        self,
        user_input: UserInput,
        output_dir: Path | None = None,
        usage_tracker: UsageTracker | None = None,
    ) -> None:
        self.user_input = user_input
        self.control = user_input.control or Control()
        self.output_dir = output_dir
        self.usage_tracker = usage_tracker or get_usage_tracker()

        # Initialize agents
        self.style_engine = StyleInferenceEngine()
        self.visual_architect = VisualArchitect()
        self.render_compiler = RenderCompiler()
        self.target_classifier = TargetClassifier()
        self.generation_pipeline = GenerationPipeline(usage_tracker=self.usage_tracker)
        self.review_iteration = ReviewIteration(
            max_iterations=self.control.max_iterations,
            quality_threshold=self.control.quality_threshold,
        )
        self.output_formatter = OutputFormatter(output_dir)

        # Build graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine."""
        graph = StateGraph(AcademicDreamerState)

        # Add nodes
        graph.add_node("classify_target", self._classify_target)
        graph.add_node("infer_style", self._infer_style)
        graph.add_node("generate_schema", self._generate_schema)
        graph.add_node("compile_render", self._compile_render)
        graph.add_node("generate_image", self._generate_image)
        graph.add_node("review_image", self._review_image)
        graph.add_node("format_output", self._format_output)

        # Define edges
        graph.add_edge(START, "classify_target")
        graph.add_edge("classify_target", "infer_style")
        graph.add_edge("infer_style", "generate_schema")
        graph.add_edge("generate_schema", "compile_render")
        graph.add_edge("compile_render", "generate_image")
        graph.add_edge("generate_image", "review_image")

        # Conditional edge for review loop
        def should_retry(state: AcademicDreamerState) -> str:
            if state.get("review_decision") and state["review_decision"].should_retry:
                return "generate_image"  # Loop back
            return "format_output"  # Exit loop

        graph.add_conditional_edges("review_image", should_retry)

        graph.add_edge("format_output", END)

        return graph.compile()

    async def _classify_target(self, state: dict[str, Any]) -> dict[str, Any]:
        """Classify target type if not specified."""
        if state.get("target_type") and state["target_type"] != "auto":
            return {"target_type": state["target_type"]}

        target = self.target_classifier.classify(state["idea"])
        return {"target_type": target}

    async def _infer_style(self, state: dict[str, Any]) -> dict[str, Any]:
        """Infer style from input."""
        style_directive, was_fallback = self.style_engine.infer(state["style_raw"])

        warning = None
        if was_fallback:
            warning = "Style inference: Unknown venue, using generic academic style"

        return {
            "style_inferred": style_directive,
            "error": warning,
        }

    async def _generate_schema(self, state: dict[str, Any]) -> dict[str, Any]:
        """Generate visual schema (Stage 1)."""
        schema = await self.visual_architect.generate_schema(
            idea=state["idea"],
            target_type=state.get("target_type"),
        )
        return {"visual_schema": schema}

    async def _compile_render(self, state: dict[str, Any]) -> dict[str, Any]:
        """Compile render prompt (Stage 2)."""
        render_prompt = await self.render_compiler.compile(
            visual_schema=state["visual_schema"],
            style_directive=state.get("style_inferred", ""),
        )
        return {"render_prompt": render_prompt.visual_schema}

    async def _generate_image(self, state: dict[str, Any]) -> dict[str, Any]:
        """Generate image via pipeline."""
        result = self.generation_pipeline.generate(state.get("render_prompt", ""))
        return {"image_data": result.image_data}

    async def _review_image(self, state: dict[str, Any]) -> dict[str, Any]:
        """Review generated image."""
        iteration = state.get("iteration", 0) + 1
        review_history = state.get("review_history", [])

        # Create GenerationResult from state
        gen_result = GenerationResult(image_data=state["image_data"])

        decision = self.review_iteration.review(
            iteration=iteration,
            generation_result=gen_result,
            review_history=review_history,
        )

        record = self.review_iteration.create_record(decision, iteration)

        return {
            "iteration": iteration,
            "review_decision": decision,
            "review_history": review_history + [record],
        }

    async def _format_output(self, state: dict[str, Any]) -> dict[str, Any]:
        """Format and save output."""
        gen_result = GenerationResult(image_data=state["image_data"])

        # Generate filename from idea
        filename = self._sanitize_filename(state["idea"][:50])

        output_paths = self.output_formatter.format(
            result=gen_result,
            filename=filename,
            formats=self.control.output_formats,
        )

        return {"output_paths": output_paths}

    def _sanitize_filename(self, text: str) -> str:
        """Sanitize text for filename."""
        import re
        # Remove special chars, keep alphanumeric and spaces
        sanitized = re.sub(r"[^\w\s-]", "", text)
        # Replace spaces with underscores
        sanitized = re.sub(r"\s+", "_", sanitized)
        return sanitized[:50]

    async def run(self) -> dict[str, Any]:
        """Run the orchestration pipeline."""
        initial_state: AcademicDreamerState = {
            "idea": self.user_input.idea,
            "style_raw": self.user_input.style,
            "target_type": self.user_input.target_type,
        }

        # Run the graph
        result = await self.graph.ainvoke(initial_state)

        return result
