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

    def __init__(
        self,
        model_name: Optional[str] = None,
        embedding_model: Optional[str] = None,
        api_key: Optional[str] = None,
        api_base_url: Optional[str] = None,
    ):
        """
        Initialize RAGAs evaluation service.

        Args:
            model_name: Model name for RAGAs evaluator LLM (OpenAI-compatible).
                       If None, reads from CCOP_RAGAS_EVALUATOR_MODEL setting.
            embedding_model: HuggingFace embedding model for semantic similarity.
                       If None, reads from CCOP_RAGAS_EMBEDDING_MODEL setting.
            api_key: API key for LLM provider (OpenAI-compatible).
                    If None, reads from CCOP_RAGAS_API_KEY setting.
            api_base_url: Base URL for LLM provider API (OpenAI-compatible).
                         If None, reads from CCOP_RAGAS_API_BASE_URL setting.
        """
        from infrastructure.config.settings import get_settings
        settings = get_settings()
        self._model_name = model_name or settings.ragas_evaluator_model
        self._embedding_model_name = embedding_model or settings.ragas_embedding_model
        self._api_key = api_key or settings.ragas_api_key
        self._api_base_url = api_base_url or settings.ragas_api_base_url
        self._evaluator_llm = None  # Lazy init
        self._evaluator_embeddings = None  # Lazy init

    def _get_evaluator_llm(self):
        """Lazy initialization of RAGAs evaluator LLM via llm_factory (OpenAI-compatible)."""
        if self._evaluator_llm is None:
            try:
                from openai import OpenAI
                from ragas.llms import llm_factory

                client = OpenAI(
                    api_key=self._api_key,
                    base_url=self._api_base_url,
                )
                self._evaluator_llm = llm_factory(
                    self._model_name,
                    provider="openai",
                    client=client,
                    max_tokens=8192,
                )
                logger.info(f"Initialized RAGAs evaluator with {self._model_name} via {self._api_base_url}")
            except Exception as e:
                logger.error(f"Failed to initialize RAGAs evaluator LLM: {e}")
                raise
        return self._evaluator_llm

    def _get_evaluator_embeddings(self):
        """Lazy initialization of RAGAs evaluator embeddings (LangChain-compatible)."""
        if self._evaluator_embeddings is None:
            try:
                from langchain_community.embeddings import HuggingFaceEmbeddings

                self._evaluator_embeddings = HuggingFaceEmbeddings(
                    model_name=self._embedding_model_name,
                )
                logger.info(f"Initialized RAGAs embeddings with {self._embedding_model_name}")
            except Exception as e:
                logger.error(f"Failed to initialize RAGAs embeddings: {e}")
                raise
        return self._evaluator_embeddings

    @staticmethod
    def _clamp_score(value) -> float:
        """Clamp a score to [0.0, 1.0]. RAGAs can return values slightly out of range."""
        if value is None:
            return 0.0
        return min(1.0, max(0.0, float(value)))

    def _extract_scores(self, result) -> dict:
        """Extract scores dictionary from RAGAs evaluate() result."""
        scores_dict = result
        if hasattr(result, 'scores'):
            scores = result.scores
            if hasattr(scores, 'to_dict'):
                scores_dict = scores.to_dict("records")[0]
            elif isinstance(scores, list) and len(scores) > 0:
                scores_dict = scores[0]
            else:
                scores_dict = dict(result)
        return scores_dict

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

        Runs two separate evaluations:
        1. Base metrics (all responses): factual_recall, answer_relevancy, semantic_similarity
        2. Context metrics (RAG only): context_faithfulness, context_precision, context_recall

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

            is_rag = retrieved_contexts is not None and len(retrieved_contexts) > 0

            from ragas import EvaluationDataset, SingleTurnSample, evaluate
            from ragas.metrics import (
                _AnswerRelevancy,
                _ContextPrecision,
                _ContextRecall,
                _Faithfulness,
                FactualCorrectness,
                SemanticSimilarity,
            )

            evaluator_llm = self._get_evaluator_llm()
            evaluator_embeddings = self._get_evaluator_embeddings()

            metric_scores = []

            # --- Evaluation 1: Base metrics (factual_recall, answer_relevancy, semantic_similarity) ---
            base_sample = SingleTurnSample(
                user_input=question,
                response=response,
                reference=reference_text,
            )
            base_dataset = EvaluationDataset(samples=[base_sample])
            logger.info("Running RAGAs base metrics (factual_recall, answer_relevancy, semantic_similarity)")
            base_result = evaluate(
                dataset=base_dataset,
                metrics=[
                    FactualCorrectness(llm=evaluator_llm, mode="recall"),
                    _AnswerRelevancy(),
                    SemanticSimilarity(),
                ],
                llm=evaluator_llm,
                embeddings=evaluator_embeddings,
            )
            base_scores = self._extract_scores(base_result)

            # Map FactualCorrectness(recall) to factual_recall
            factual_recall_score = None
            for key, value in base_scores.items():
                key_lower = key.lower()
                if "factual" in key_lower and "recall" in key_lower:
                    factual_recall_score = value
                elif key == "factual_correctness":
                    # Fallback: single FactualCorrectness metric in recall mode
                    factual_recall_score = value

            # Add factual_recall
            if factual_recall_score is not None:
                metric_scores.append(RagasMetricScore(
                    name="factual_recall",
                    score=self._clamp_score(factual_recall_score),
                    applicable=True,
                ))
            else:
                metric_scores.append(RagasMetricScore(
                    name="factual_recall", score=0.0, applicable=False,
                ))

            # Add answer_relevancy
            if "answer_relevancy" in base_scores:
                score = base_scores["answer_relevancy"]
                metric_scores.append(RagasMetricScore(
                    name="answer_relevancy",
                    score=self._clamp_score(score),
                    applicable=True,
                ))
            else:
                metric_scores.append(RagasMetricScore(
                    name="answer_relevancy", score=0.0, applicable=False,
                ))

            # Add semantic_similarity
            if "semantic_similarity" in base_scores:
                score = base_scores["semantic_similarity"]
                metric_scores.append(RagasMetricScore(
                    name="semantic_similarity",
                    score=self._clamp_score(score),
                    applicable=True,
                ))
            else:
                metric_scores.append(RagasMetricScore(
                    name="semantic_similarity", score=0.0, applicable=False,
                ))

            # --- Evaluation 2: Context metrics (RAG only) ---
            if is_rag:
                context_sample = SingleTurnSample(
                    user_input=question,
                    response=response,
                    reference=reference_text,
                    retrieved_contexts=retrieved_contexts,
                )
                context_dataset = EvaluationDataset(samples=[context_sample])
                logger.info("Running RAGAs context metrics (faithfulness, precision, recall)")
                context_result = evaluate(
                    dataset=context_dataset,
                    metrics=[_Faithfulness(), _ContextPrecision(), _ContextRecall()],
                    llm=evaluator_llm,
                    embeddings=evaluator_embeddings,
                )
                context_scores = self._extract_scores(context_result)

                # Map faithfulness -> context_faithfulness
                cf_score = context_scores.get("faithfulness")
                metric_scores.append(RagasMetricScore(
                    name="context_faithfulness",
                    score=self._clamp_score(cf_score),
                    applicable=True,
                ))

                for ragas_name in ["context_precision", "context_recall"]:
                    score = context_scores.get(ragas_name)
                    metric_scores.append(RagasMetricScore(
                        name=ragas_name,
                        score=self._clamp_score(score),
                        applicable=True,
                    ))
            else:
                # Non-RAG: context metrics not applicable
                metric_scores.append(RagasMetricScore(
                    name="context_faithfulness", score=0.0, applicable=False,
                ))
                metric_scores.append(RagasMetricScore(
                    name="context_precision", score=0.0, applicable=False,
                ))
                metric_scores.append(RagasMetricScore(
                    name="context_recall", score=0.0, applicable=False,
                ))

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
