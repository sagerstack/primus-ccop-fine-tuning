"""
Per-result Rich Panel renderer.

Used by both `evaluate run` (one panel per test case) and `query ask` (one panel
for the single ad-hoc query). Centralising this keeps the two CLI surfaces in
sync and avoids drift when output format evolves.

Inputs are passed as plain primitives / dicts so callers can construct them
from any source (eval DTO, query response, lab eval JSON, etc.). All metric
fields are Optional — sections are gracefully skipped when the value is None.

Mode flags:
- show_judge: include LLM Judge subsection (False for `query ask` since there's
  no expected_label to score against)
- show_gt_comparisons: include GT-dependent RAGAs metrics (context_recall,
  factual_recall, semantic_similarity). False for `query ask`.
- verbose_io: include System Prompt / User Prompt / detailed retrieved contexts
  / token counts.
"""
from __future__ import annotations
from typing import Any, Mapping, Optional, Sequence

from rich.panel import Panel


_MAX_SYSTEM_PROMPT_PREVIEW = 600
_MAX_USER_PROMPT_PREVIEW = 1200
_MAX_CONTEXT_TEXT_PREVIEW = 200
_MAX_RETRIEVED_CITATIONS_INLINE = 5


def build_per_result_panel(
    *,
    title: str,
    border_style: str = "cyan",
    question: str,
    response: str,
    # Pipeline / mode metadata
    evaluation_mode: Optional[str] = None,    # "hybrid" | "llm-only" | "rag-only"
    chunk_count: Optional[int] = None,
    retrieved_citations: Optional[Sequence[str]] = None,
    # Verbose I/O details (only rendered when verbose_io=True)
    system_prompt: Optional[str] = None,
    user_prompt: Optional[str] = None,
    retrieved_contexts_detailed: Optional[Sequence[Mapping[str, Any]]] = None,
    # Token/timing
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: int = 0,
    tokens_used_legacy: int = 0,        # fallback when fine-grained counts absent
    latency_ms: int = 0,
    # RAGAs metrics — pass each independently so callers don't have to
    # speak the lab metric vocabulary
    ragas_context_recall: Optional[float] = None,        # GT-dependent
    ragas_context_precision: Optional[float] = None,     # may be GT-free with LLM judge
    ragas_context_faithfulness: Optional[float] = None,  # GT-free
    ragas_factual_recall: Optional[float] = None,        # GT-dependent
    ragas_answer_relevancy: Optional[float] = None,      # GT-free
    ragas_semantic_similarity: Optional[float] = None,   # GT-dependent
    ragas_error: Optional[str] = None,
    ragas_is_rag_response: Optional[bool] = None,
    # LLM Judge — rubric mode (per-dimension scores) OR universal mode
    judge_dimensions: Optional[Sequence[Mapping[str, Any]]] = None,
    # Each dim: {name: str, value: float (0-1), weight: float, raw_score: int (0-3, optional)}
    judge_overall: Optional[float] = None,
    judge_error: bool = False,
    universal_judge_overall: Optional[float] = None,
    reasoning_criteria_met: Optional[Mapping[str, Optional[bool]]] = None,
    hallucination_detected: Optional[bool] = None,
    unsupported_count: Optional[int] = None,
    contradicted_count: Optional[int] = None,
    claims_count: Optional[int] = None,
    # Mode flags
    show_judge: bool = True,
    show_gt_comparisons: bool = True,
    verbose_io: bool = False,
) -> Panel:
    """Build a Rich Panel for a single per-result block.

    Returns a fully composed Panel ready to console.print(...).
    """
    lines: list[str] = []

    # 1. Question
    lines.append(f"[bold]Question:[/bold]\n  {question}")

    # 2. Verbose I/O block
    if verbose_io:
        if system_prompt is not None:
            sp = (
                system_prompt[:_MAX_SYSTEM_PROMPT_PREVIEW] + " ..."
                if len(system_prompt) > _MAX_SYSTEM_PROMPT_PREVIEW
                else system_prompt
            )
            lines.append(f"\n[bold]System Prompt:[/bold]\n  {sp}")
        else:
            lines.append("\n[bold]System Prompt:[/bold] (none)")

        if user_prompt is not None:
            up = (
                user_prompt[:_MAX_USER_PROMPT_PREVIEW] + " ..."
                if len(user_prompt) > _MAX_USER_PROMPT_PREVIEW
                else user_prompt
            )
            lines.append(f"\n[bold]User Prompt (with RAG context):[/bold]\n  {up}")
        else:
            lines.append("\n[bold]User Prompt (with RAG context):[/bold] (none)")

        if retrieved_contexts_detailed:
            lines.append("\n[bold]Retrieved Contexts (detailed):[/bold]")
            for ctx in retrieved_contexts_detailed:
                citation_id = ctx.get("citation_id", "?")
                section = ctx.get("section", "")
                clause = ctx.get("clause", "")
                score = ctx.get("score", "")
                text_preview = str(ctx.get("text", ""))[:_MAX_CONTEXT_TEXT_PREVIEW]
                meta = f"{citation_id}"
                if section:
                    meta += f" | {section}"
                if clause:
                    meta += f" | clause: {clause}"
                if score:
                    meta += f" | score: {score}"
                lines.append(f"  [{meta}]")
                lines.append(f"    {text_preview}...")

        lines.append(
            f"\n[bold]Tokens:[/bold] prompt={prompt_tokens} "
            f"completion={completion_tokens} total={total_tokens}"
        )

    # 3. Retrieved Citations (compact list, hybrid mode only)
    if evaluation_mode == "hybrid" and retrieved_citations:
        lines.append("\n[bold]Retrieved Citations:[/bold]")
        for i, cid in enumerate(retrieved_citations[:_MAX_RETRIEVED_CITATIONS_INLINE], 1):
            lines.append(f"  [{i}] {cid}")
        if len(retrieved_citations) > _MAX_RETRIEVED_CITATIONS_INLINE:
            lines.append(f"  ... ({len(retrieved_citations)} total)")

    # 4. Response
    if total_tokens > 0:
        token_str = f"prompt={prompt_tokens} completion={completion_tokens} total={total_tokens}"
    elif tokens_used_legacy > 0:
        token_str = f"{tokens_used_legacy} tokens"
    else:
        token_str = ""
    suffix = f"({token_str}, {latency_ms}ms)" if token_str else f"({latency_ms}ms)"
    lines.append(f"\n[bold]Response[/bold] {suffix}:\n  {response}")

    # 5. DIAGNOSTIC GROUPS in pipeline order

    # 5a. Retrieval Quality
    rq_metrics: list[tuple[str, float]] = []
    if show_gt_comparisons and ragas_context_recall is not None:
        rq_metrics.append(("RAGAs: context_recall", ragas_context_recall))
    if ragas_context_precision is not None:
        rq_metrics.append(("RAGAs: context_precision", ragas_context_precision))

    if (
        rq_metrics
        or evaluation_mode == "llm-only"
        or (ragas_error and (show_gt_comparisons or evaluation_mode == "hybrid"))
    ):
        lines.append("\n[bold yellow]─── Retrieval Quality ───[/bold yellow]")
        if evaluation_mode == "llm-only":
            lines.append("[dim]N/A (llm-only mode)[/dim]")
        elif rq_metrics:
            for name, score in rq_metrics:
                lines.append(f"[bold]{name}:[/bold] {score:.2f}")
        elif ragas_error:
            lines.append(f"[bold]RAGAs context metrics:[/bold] [yellow]⚠ {ragas_error}[/yellow]")
        else:
            lines.append("[dim]No context metrics available[/dim]")

    # 5b. Model-RAG Grounding (context_faithfulness — GT-free)
    if (
        ragas_context_faithfulness is not None
        or evaluation_mode == "llm-only"
        or ragas_error
    ):
        lines.append("\n[bold magenta]─── Model-RAG Grounding ───[/bold magenta]")
        if evaluation_mode == "llm-only":
            lines.append("[dim]N/A (llm-only mode)[/dim]")
        elif ragas_context_faithfulness is not None:
            lines.append(
                f"[bold]RAGAs: context_faithfulness:[/bold] {ragas_context_faithfulness:.2f}"
            )
        elif ragas_error:
            lines.append(
                f"[bold]RAGAs context_faithfulness:[/bold] [yellow]⚠ {ragas_error}[/yellow]"
            )

    # 5c. Model Response Quality (Judge + answer-side RAGAs)
    rq3: list[str] = []
    if show_judge:
        if universal_judge_overall is not None:
            rq3.append("[bold]LLM Judge (Universal):[/bold]")
            rq3.append(f"  Overall Score: {universal_judge_overall:.2f}")
            if reasoning_criteria_met:
                rq3.append("\n  [bold]Reasoning Criteria:[/bold]")
                for criterion, met in reasoning_criteria_met.items():
                    if met is None:
                        status = "[dim]N/A[/dim]"
                    elif met:
                        status = "[green]YES[/green]"
                    else:
                        status = "[red]NO[/red]"
                    rq3.append(
                        f"    {criterion.replace('_', ' ').title()}: {status}"
                    )
            if hallucination_detected is not None:
                halluc_status = (
                    "[red]YES[/red]" if hallucination_detected else "[green]NO[/green]"
                )
                claim_info = ""
                if unsupported_count is not None and contradicted_count is not None:
                    claim_info = (
                        f" ({claims_count or 0} claims: "
                        f"{unsupported_count} unsupported, "
                        f"{contradicted_count} contradicted)"
                    )
                rq3.append(f"  [bold]Hallucination:[/bold] {halluc_status}{claim_info}")
        elif judge_dimensions:
            rq3.append("[bold]LLM Judge:[/bold]")
            for d in judge_dimensions:
                name = d.get("name", "?")
                # Hide sentinel metrics (leading underscore = metadata, not a score)
                if name.startswith("_"):
                    continue
                weight = d.get("weight", 0.0)
                raw_score = d.get("raw_score")
                if raw_score is None:
                    val = d.get("value", 0.0)
                    raw_score = round(val * 3)
                rq3.append(f"  {name:<30s} {raw_score}/3  (weight: {weight:.2f})")
        if judge_error:
            rq3.append("[bold]LLM Judge:[/bold] [yellow]⚠ Judge Error[/yellow]")

    answer_metrics: list[tuple[str, float]] = []
    if show_gt_comparisons and ragas_factual_recall is not None:
        answer_metrics.append(("RAGAs: factual_recall", ragas_factual_recall))
    if ragas_answer_relevancy is not None:
        answer_metrics.append(("RAGAs: answer_relevancy", ragas_answer_relevancy))
    if show_gt_comparisons and ragas_semantic_similarity is not None:
        answer_metrics.append(("RAGAs: semantic_similarity", ragas_semantic_similarity))
    for name, score in answer_metrics:
        rq3.append(f"[bold]{name}:[/bold] {score:.2f}")

    if rq3:
        lines.append("\n[bold cyan]─── Model Response Quality ───[/bold cyan]")
        lines.extend(rq3)

    # 6. RAG response detection note + RAG context summary
    if ragas_is_rag_response:
        lines.append("\n[dim]RAG response detected — context metrics evaluated[/dim]")

    if evaluation_mode and chunk_count is not None:
        if chunk_count > 0 and retrieved_citations:
            chunk_display = ", ".join(retrieved_citations[:_MAX_RETRIEVED_CITATIONS_INLINE])
            if len(retrieved_citations) > _MAX_RETRIEVED_CITATIONS_INLINE:
                chunk_display += f", ... ({len(retrieved_citations)} total)"
            lines.append(
                f"\n[bold]RAG Context:[/bold] {chunk_count} chunks ({chunk_display})"
            )
        elif evaluation_mode == "hybrid":
            lines.append("\n[bold]RAG Context:[/bold] No chunks retrieved")

    return Panel("\n".join(lines), title=title, border_style=border_style)
