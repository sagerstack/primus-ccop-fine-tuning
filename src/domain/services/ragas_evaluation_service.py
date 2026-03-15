"""
RAGAs Evaluation Service

Domain service for evaluating RAG pipeline quality using RAGAs metrics.
Independent from ScoringService (benchmark scoring) - provides Layer 2 quality assessment.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class RagasMetricScore:
    """Single RAGAs metric result."""

    name: str  # e.g., "faithfulness", "answer_correctness"
    score: float  # 0.0-1.0
    applicable: bool  # False if metric was skipped (e.g., faithfulness for non-RAG)


@dataclass
class RagasEvaluation:
    """Complete RAGAs evaluation for one test case."""

    metrics: List[RagasMetricScore]
    is_rag_response: bool  # Whether context metrics were evaluated
    evaluation_error: bool  # True if evaluation failed
    error_message: str = ""  # Error details


class RagasEvaluationService:
    """
    RAGAs-based evaluation for RAG pipeline quality.

    Separate from ScoringService (benchmark scoring).
    Produces Layer 2 quality metrics per test case.

    Purpose: Benchmark scoring evaluates domain-specific compliance quality.
    RAGAs evaluates generic response and retrieval quality:
    - Is the answer factually correct?
    - Is it relevant to the question?
    - Is it faithful to retrieved context?
    - Are the right contexts being retrieved?

    Both layers produce separate scores per test case, enabling richer analysis
    (a response can score high on RAGAs but low on benchmarks, or vice versa).
    """

    def __init__(self, model_name: str = "claude-sonnet-4"):
        """
        Initialize RAGAs evaluation service.

        Args:
            model_name: Claude model name for RAGAs evaluator LLM.
                       Defaults to claude-sonnet-4 but can be overridden via config.
        """
        self._model_name = model_name
        self._evaluator_llm = None  # Lazy init

    def _get_evaluator_llm(self):
        """Lazy initialization of RAGAs evaluator LLM."""
        if self._evaluator_llm is None:
            try:
                from langchain_anthropic import ChatAnthropic
                from ragas.llms import LangchainLLMWrapper

                llm = ChatAnthropic(model=self._model_name)
                self._evaluator_llm = LangchainLLMWrapper(llm)
                logger.info(f"Initialized RAGAs evaluator with {self._model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize RAGAs evaluator LLM: {e}")
                raise
        return self._evaluator_llm

    def evaluate_response(
        self,
        question: str,
        response: str,
        reference: str,
        retrieved_contexts: Optional[List[str]] = None,
        key_facts: Optional[List[str]] = None,
    ) -> RagasEvaluation:
        """
        Evaluate a response using RAGAs metrics.

        For all responses: answer_correctness, answer_relevancy
        For RAG responses (retrieved_contexts provided):
            + faithfulness, context_precision, context_recall

        Args:
            question: Original question
            response: Model's response
            reference: Ground truth expected response
            retrieved_contexts: List of retrieved document texts (from GraphState.documents)
            key_facts: Key facts for reference enrichment (appended to reference)

        Returns:
            RagasEvaluation with metrics and error status
        """
        try:
            # Build reference text: combine reference with key_facts if provided
            reference_text = reference
            if key_facts and len(key_facts) > 0:
                key_facts_text = "\n".join(key_facts)
                reference_text = f"{reference}\n\n{key_facts_text}"

            # Determine if this is a RAG response
            is_rag = retrieved_contexts is not None and len(retrieved_contexts) > 0

            # Create SingleTurnSample
            from ragas import EvaluationDataset, SingleTurnSample

            sample = SingleTurnSample(
                user_input=question,
                response=response,
                reference=reference_text,
                retrieved_contexts=retrieved_contexts if is_rag else None,
            )

            # Select metrics based on response type
            from ragas.metrics.collections import (
                AnswerCorrectness,
                AnswerRelevancy,
                ContextPrecision,
                ContextRecall,
                Faithfulness,
            )

            evaluator_llm = self._get_evaluator_llm()

            # Base metrics (all responses)
            metrics = [
                AnswerCorrectness(llm=evaluator_llm),
                AnswerRelevancy(llm=evaluator_llm),
            ]

            # Context metrics (RAG responses only)
            if is_rag:
                metrics.extend(
                    [
                        Faithfulness(llm=evaluator_llm),
                        ContextPrecision(llm=evaluator_llm),
                        ContextRecall(llm=evaluator_llm),
                    ]
                )

            # Create EvaluationDataset and evaluate
            from ragas import evaluate

            dataset = EvaluationDataset(samples=[sample])

            logger.info(f"Running RAGAs evaluation (is_rag={is_rag}, metrics={len(metrics)})")
            result = evaluate(dataset=dataset, metrics=metrics)

            # Extract scores from result
            # RAGAs result.scores is a pandas DataFrame-like object with metric names as columns
            scores_dict = result.scores.to_dict("records")[0]  # First (only) sample

            # Build RagasEvaluation from scores
            metric_scores = []

            # Map RAGAs metric names to our names
            ragas_metric_names = {
                "answer_correctness": "answer_correctness",
                "answer_relevancy": "answer_relevancy",
                "faithfulness": "faithfulness",
                "context_precision": "context_precision",
                "context_recall": "context_recall",
            }

            for ragas_name, our_name in ragas_metric_names.items():
                if ragas_name in scores_dict:
                    score = scores_dict[ragas_name]
                    metric_scores.append(
                        RagasMetricScore(
                            name=our_name,
                            score=float(score) if score is not None else 0.0,
                            applicable=True,
                        )
                    )
                else:
                    # Metric not computed (e.g., context metrics for non-RAG)
                    metric_scores.append(
                        RagasMetricScore(
                            name=our_name,
                            score=0.0,
                            applicable=False,
                        )
                    )

            logger.info(
                f"RAGAs evaluation succeeded: {len([m for m in metric_scores if m.applicable])} "
                f"applicable metrics"
            )

            return RagasEvaluation(
                metrics=metric_scores,
                is_rag_response=is_rag,
                evaluation_error=False,
            )

        except Exception as e:
            logger.error(f"RAGAs evaluation failed: {e}", exc_info=True)
            return RagasEvaluation(
                metrics=[],
                is_rag_response=retrieved_contexts is not None and len(retrieved_contexts) > 0,
                evaluation_error=True,
                error_message=f"RAGAs evaluation failed: {str(e)}",
            )
