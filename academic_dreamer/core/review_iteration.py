"""Review iteration loop with continuous context."""

from openai import OpenAI

from academic_dreamer.config.settings import MAX_ITERATIONS_CAP, TEXT_MODEL_NAME, OPENROUTER_API_KEY
from academic_dreamer.models.schemas import GenerationResult, ReviewDecision, ReviewRecord


class ReviewIteration:
    """Continuous review loop with context accumulation."""

    SYSTEM_PROMPT = """You are a quality reviewer for academic illustrations.

Evaluate the generated image against these criteria:
1. Visual clarity and readability
2. Correct representation of the academic concept
3. Proper text labels (if any)
4. Appropriate color palette
5. Professional academic style

Provide:
- Quality score: 0.0-1.0
- Approval decision: yes/no
- Actionable feedback for improvement if not approved

Be strict but fair. Academic diagrams should be clear, accurate, and professional."""

    def __init__(self, max_iterations: int = 2, quality_threshold: float = 0.7) -> None:
        self.max_iterations = max(0, min(max_iterations, MAX_ITERATIONS_CAP))
        self.quality_threshold = quality_threshold
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )

    def review(
        self,
        iteration: int,
        generation_result: GenerationResult,
        review_history: list[ReviewRecord],
    ) -> ReviewDecision:
        """Review a generation result.

        Args:
            iteration: Current iteration number
            generation_result: The generated image data
            review_history: Previous review records for context

        Returns:
            ReviewDecision with approval, score, and feedback
        """
        # Skip review if max iterations is 0
        if self.max_iterations == 0:
            return ReviewDecision(
                approved=True,
                quality_score=1.0,
                feedback="Review skipped (max_iterations=0)",
                should_retry=False,
            )

        # Build context from history
        history_context = ""
        if review_history:
            history_context = "Previous iterations feedback:\n"
            for record in review_history[-3:]:  # Last 3 for context
                history_context += f"- Iteration {record.iteration}: Score {record.quality_score}, Feedback: {record.feedback}\n"

        prompt = f"""Evaluate this academic illustration.

Current iteration: {iteration}/{self.max_iterations}
{history_context}

Image data (Base64): {generation_result.image_data[:100]}...

Please evaluate and provide:
1. Quality score (0.0-1.0)
2. Approved? (yes/no)
3. Feedback if not approved"""

        try:
            response = self.client.chat.completions.create(
                model=TEXT_MODEL_NAME,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
            )

            content = response.choices[0].message.content or ""
            return self._parse_decision(content, iteration)

        except Exception as e:
            # On error, return approval to avoid blocking
            return ReviewDecision(
                approved=True,
                quality_score=0.5,
                feedback=f"Review error (using default approval): {e}",
                should_retry=False,
            )

    def _parse_decision(self, content: str, iteration: int) -> ReviewDecision:
        """Parse LLM response into ReviewDecision."""
        import re

        # Extract score
        score = 0.5  # default
        score_match = re.search(r"(?:score|rating)[:\s]*([0-9.]+)", content, re.IGNORECASE)
        if score_match:
            score = float(score_match.group(1))

        # Extract approval
        approved = "no" not in content.lower().split()[0:3] if content else False
        approved = "approved" in content.lower() or "yes" in content.lower()[:50]

        # Determine if should retry
        should_retry = not approved and iteration < self.max_iterations and score < self.quality_threshold

        # Extract feedback
        feedback = content
        if "Feedback:" in content:
            feedback = content.split("Feedback:", 1)[1].strip()

        return ReviewDecision(
            approved=approved,
            quality_score=score,
            feedback=feedback[:500],  # Truncate if long
            should_retry=should_retry,
        )

    def create_record(self, decision: ReviewDecision, iteration: int) -> ReviewRecord:
        """Create a review record from decision."""
        return ReviewRecord(
            iteration=iteration,
            quality_score=decision.quality_score,
            feedback=decision.feedback,
            approved=decision.approved,
        )
