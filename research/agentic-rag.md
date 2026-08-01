# Research: Agentic RAG (2025–2026) for Clause-Level Citation Faithfulness in a LangGraph + Neo4j Graph-Backed Compliance Pipeline

**Date**: 2026-07-12
**Researcher**: researcher agent
**Status**: Final

> **Sourcing method (redone over the internet).** There is no `web_search` *tool* in this
> harness (it is named in the researcher persona prompt but was never bound). Internet
> access is available via `curl`/Bash, so this report was rebuilt by **fetching and reading
> the actual primary sources**: every arXiv paper below was retrieved from `arxiv.org` and
> its **abstract read directly** (2026-07-12), and the Neo4j GraphRAG + LangGraph docs were
> fetched from their official sites (HTTP 200). Quoted phrases are lifted verbatim from those
> abstracts/docs. Stack-specific claims about `graphont` were verified by reading
> `src/rag/graph/ontology_v2/omd_retrieval.py`, `.../omd_context_assembly.py`, `.../_neo.py`,
> and `src/rag/retrieval/graph.py`. Claims not grounded in a fetched source are marked
> *(unverified)*.

---

## 1. Executive Summary

- **Agentic RAG = an LLM control loop wrapping retrieval.** The 2025 survey (arXiv 2501.09136) defines it as embedding *autonomous agents* with "reflection, planning, tool use, and multi-agent collaboration" into RAG to "dynamically manage retrieval strategies, iteratively refine contextual understanding, and adapt workflows" — vs. traditional RAG's "static workflows." Structurally: a **cyclic graph**, not a one-shot DAG.
- **Our `graphont` is graph-backed and fully single-shot.** Verified in code: it retrieves over a **Neo4j** typed KG (`:Concept`/`:Clause`/`:Definition`, `:INVOKES`, `:REL`), tri-channel (IDF-weighted graph overlap ⊕ BM25 ⊕ bge-large dense) → **weighted RRF** (W=1.0/0.7/1.5) → **cross-encoder rerank** → **top-k=8**, one `retrieve()` call, no feedback from generation/citations back into retrieval. It is a strong *retriever* with **zero agentic behaviour**.
- **For clause-level citation faithfulness (our key metric), the strongest evidence points to KG-path-grounded reasoning + a self-critique citation gate.** Self-RAG reports "significant gains in… citation accuracy for long-form generations" (2310.11511). RoG achieves "faithful and interpretable reasoning" by grounding LLM reasoning on **KG relation paths** (2310.01061). ToG gives "knowledge traceability and knowledge correctability" via agentic KG exploration (2307.07697). ALCE shows the problem is real: even the best systems "lack complete citation support 50% of the time" (2305.14627).
- **Two on-point pattern families for us:** (a) **LangGraph agentic loops** (Self-RAG / CRAG / adaptive) as nodes+edges over our existing retriever; (b) **KG-agentic retrieval** (ToG / ToG-2 / RoG / Graph-CoT) that treats *graph traversal as a tool* — the natural fit for a typed Neo4j clause graph.
- **Single recommended approach (one line):** *Add an additive `--mode agentic-graphont` that (1) keeps the tri-channel Neo4j retriever as the base tool, (2) wraps it in a **bounded RoG-style relation-path / concept-expansion loop** with a **CRAG-style retrieval-quality gate** (corpus-internal re-query, no web fallback), and (3) ends with a **Self-RAG-style clause-citation grounding gate** — all iteration-capped LangGraph nodes/edges, calibrated on the existing 18-case κ bed before the full 435.*

---

## 2. Problem Statement

**What & why.** SG-1 needs a decision-ready survey of agentic-RAG (2025–2026) to feed a planner designing an integration into our existing **LangGraph + Neo4j** retrieval pipeline (`graphont` mode) for the **Singapore CCoP 2.0** compliance *evaluation framework*. CCoP is a regulatory document with **numbered clauses**; the decisive quality metric is **clause-level citation faithfulness** (every asserted clause ID is actually supported by retrieved evidence), not answer plausibility.

**Scope.** In: agentic-RAG definitions; architectural patterns; strengths/tradeoffs (latency, cost, retrieval quality, hallucination, citation faithfulness); what improves clause-level citation accuracy in regulatory/standards text; and **graph-RAG / Neo4j + LangGraph** agentic integration patterns (primary), with a short Qdrant note (our older `hybrid` mode). Out: fine-tuning, judge/scoring changes, any code changes (planning-only, read-only on the codebase).

**Verified reality of `graphont` (from code, not recon hearsay):**
- Store: **Neo4j** (`rag/graph/ontology_v2/_neo.py` → `neo4j.GraphDatabase.driver`), layer `build_id`-scoped `omd-v1-20260709`.
- Graph: `:Concept` (IDF/`log(N/df)` weights, hub-gated), `:Clause` (863 clause nodes), `:Definition-[:DEFINES]->:Concept`, `:INVOKES` (clause→concept), `:REL` (concept→concept).
- Retrieval (`omd_retrieval.retrieve()`): query→concepts Q (surface-form map) → `Q+ = Q ∪ 1-hop over :REL` → `score(clause)=|Q∩INVOKES| + 0.5·|(Q+−Q)∩INVOKES|`; three ranked channels — graph Channel-I (IDF overlap), BM25, **bge-large-en-v1.5** dense (`.npz` index) — fused by **weighted RRF** (`W_GRAPH=1.0, W_BM25=0.7, W_DENSE=1.5, RRF_K=60, RECALL_DEPTH=100`) → **cross-encoder reranker** (bge-reranker-large; paper targets qwen3-reranker-8b) → **top-k=8**; glossary definitions injected as grounding, bypassing ranking.
- **Single-shot.** `omd_context_assembly` calls `retrieve()` once, packs `filtered_documents`, routes straight to `generate`. No re-query, no tool-calling, no generation→retrieval feedback.
- In-code **known limitations** (from `omd_retrieval.py` docstring): equal-weight RRF dilutes single-channel-strong hits; **Channel-II community-report retrieval (Leiden + LLM community reports) NOT built**; some clauses (Act §7, RtF §2.3) still missed.

**Success criteria for the eventual integration:** (1) clause-citation faithfulness ↑; (2) governing-clause recall@k ↑; (3) bounded per-case latency/cost (×435 cases); (4) additive/distinct mode (mirroring how `graphont`/`graphcpl` were added).

---

## 3. Best Practices & Industry Standards

### 3.1 Static RAG vs. agentic RAG (grounded definition)
The Agentic-RAG survey (2501.09136) frames the distinction crisply: **traditional RAG** = "static workflows [that] lack the adaptability required for multi-step reasoning"; **agentic RAG** = "embedding autonomous AI agents into the RAG pipeline" that "leverage agentic design patterns — reflection, planning, tool use, and multi-agent collaboration — to dynamically manage retrieval strategies, iteratively refine contextual understanding, and adapt workflows." Its taxonomy axes: **agent cardinality, control structure, autonomy, knowledge representation.**

### 3.2 Text-RAG agentic patterns (verified from paper abstracts)

| Pattern | What it actually does (from the paper) | Citation-faithfulness relevance |
|---|---|---|
| **Self-RAG** (2310.11511) | Trains one LM to emit **reflection tokens**: retrieve on-demand, then "generates and reflects on retrieved passages and its own generations." Reports "significant gains in improving factuality **and citation accuracy** for long-form generations." | **Directly the metric we care about.** The per-statement support critique is the citation gate. |
| **CRAG** (2401.15884) | A "**lightweight retrieval evaluator**… assesses the overall quality of retrieved documents… returning a confidence degree" → triggers different actions; "**decompose-then-recompose**" to "focus on key information and filter out irrelevant"; **web search as an extension** when the corpus returns sub-optimal docs. "Plug-and-play." | Evaluator + correction branch. **Web-search branch is wrong for a closed regulatory corpus** → replace with corpus re-query. |
| **Adaptive-RAG** (2403.14403) | A trained **classifier predicts query complexity** and routes: no-retrieval / single-step / iterative — "seamlessly adapting between the iterative and single-step… as well as the no-retrieval methods." | Cost control across 435 cases; send only complex multi-clause Qs into the loop. |
| **FLARE** (2305.06983) | "Actively decide when and what to retrieve" — predicts the upcoming sentence, and **if it contains low-confidence tokens, retrieves and regenerates.** | Iterative refinement; watch for unsupported clause claims mid-generation. |
| **IRCoT** (2212.10509) | Interleaves retrieval with CoT steps: "what to retrieve depends on what has already been derived." "Reduces model hallucination, resulting in factually more accurate CoT." | Multi-hop / cross-clause reconciliation (B03/B23-style). |
| **Self-Ask** (2210.03350) | Model "explicitly asks itself (and answers) follow-up questions before answering" — decomposition; lets you "plug in a search engine." | Decompose compound clause questions. |
| **Rewrite-Retrieve-Read** (2305.14283) | Adapts the **search query itself**: prompt an LLM to rewrite the query before retrieval; a small trainable rewriter tuned by RL from reader feedback. | Query rewriting between re-query passes. |
| **HyDE** (2212.10496) | Generate a **hypothetical document**, embed *that* for dense retrieval; the encoder "filter[s] out incorrect details." | Bridges query↔clause lexical gap; drift risk. |
| **Step-Back** (2310.06117) | Abstract to "high-level concepts and first principles" to guide reasoning; big gains on Multi-Hop (MuSiQue +7%). | Retrieve governing principles behind a specific clause. |
| **ReAct** (2210.03629) | Interleaves reasoning traces + actions; "interface with external sources such as knowledge bases"; "overcomes… hallucination and error propagation." | General tool-using agent — best for interactive `query ask`, not the deterministic batch evaluator. |

### 3.3 Evaluation standards
- **ALCE** (2305.14627) — "the first benchmark for Automatic LLMs' Citation Evaluation," metrics along **fluency, correctness, and citation quality**; finding: "even the best models lack complete citation support 50% of the time" on ELI5. **Closest public analog to our clause-citation metric.**
- **RAGAS** (2309.15217) — reference-free RAG metrics: retrieval context relevance, **faithful** use of passages, generation quality. Useful vocabulary for our own harness.

---

## 4. Bleeding-Edge / Emerging Approaches — Graph / KG-Agentic (the on-point cluster for `graphont`)

The Graph-RAG survey (2408.08921) formalizes the workflow as **Graph-Based Indexing → Graph-Guided Retrieval → Graph-Enhanced Generation**, motivated by the fact that "the complex structure of relationships among different entities… presents challenges for [flat] RAG." Our `graphont` already does indexing + graph-guided retrieval; the agentic upgrade lives in the **retrieval loop** and **generation grounding**.

| Approach | What it does (from abstract) | Maturity | Fit to our Neo4j clause graph |
|---|---|---|---|
| **GraphRAG (Microsoft)** (2404.16130) | LLM builds an **entity KG** + **pregenerated community summaries** (closely-related entity groups); community summaries → partial responses → final summary. Wins on **global "what are the main themes" sensemaking** at 1M-token scale. | Early-production | **Exactly our in-code missing "Channel-II community-report" limitation.** Add a Leiden-community + LLM-summary channel for global/thematic compliance questions. |
| **Think-on-Graph (ToG)** (2307.07697) | Treats the **LLM as an agent** doing **iterative beam search over the KG**, discovering "the most promising reasoning paths." Training-free, plug-and-play; gives "**knowledge traceability and knowledge correctability**." | Established | Agentic traversal of `:REL`/`:INVOKES`. **Traceability = citation provenance** — every hop is an auditable clause/concept link. |
| **Think-on-Graph 2.0** (2407.10805) | **Hybrid, tight-coupling** KG + document retrieval that **alternates graph and context retrieval iteratively**; KG links documents via entities, documents give entity context. "Deep and faithful reasoning." | Emerging→established | Best structural match: our `:Clause` text ↔ `:Concept` graph is exactly "documents linked by entities." Alternate concept-expansion ↔ clause-text retrieval. |
| **Reasoning on Graphs (RoG)** (2310.01061) | **Planning-retrieval-reasoning**: LLM first "generates **relation paths grounded by KGs as faithful plans**," then retrieves valid reasoning paths for "**faithful and interpretable** reasoning." | Established | Generate a plan over `:REL` edges ("access-control → password → length") before retrieving clauses → grounded, auditable clause chains. |
| **Graph-CoT** (2404.07103) | Iterative loop of **LLM reasoning → LLM-graph interaction → graph execution** over text-attributed graphs (GRBench). | Early | The generic "graph traversal as a tool" loop expressed as LangGraph nodes. |
| **G-Retriever** (2402.07630) | RAG over textual graphs as a **Prize-Collecting Steiner Tree** optimization; "resist hallucination" and handle graphs "exceed[ing] the LLM's context window." | Early | Principled subgraph selection when many clauses/concepts are relevant — a smarter alternative to flat top-k. |
| **HippoRAG** (2405.14831) | KG + **Personalized PageRank**; **single-step retrieval matches iterative IRCoT while 10–30× cheaper and 6–13× faster.** | Early→established | **Cost lever.** A PPR pass over the concept graph could get multi-hop-quality recall in one shot — critical at 435 cases. |

**Official tooling.** The **Neo4j GraphRAG for Python** package (`neo4j-graphrag`, fetched from neo4j.com/docs) ships production retrievers directly over a Neo4j driver — `VectorRetriever`, `VectorCypherRetriever`, hybrid retrievers, and **Text2Cypher** (LLM-generated Cypher), plus vector-index creation/upsert helpers. This is the sanctioned path for LLM-driven Cypher/graph retrieval as an agent tool. **Maturity: production.**

---

## 5. Stack-Specific Integration (LangGraph + Neo4j `graphont`; short Qdrant note)

### 5.1 (a) LangGraph agentic loops as nodes + edges (orchestration we already use)
Our pipeline *is* a LangGraph `StateGraph` (`src/rag/retrieval/graph.py`) with mode routing (`route_by_mode`) and a `decide_after_grading` conditional edge already present. The LangGraph official tutorials (**Self-RAG**, **CRAG**, **Adaptive RAG**, **Agentic RAG** — all HTTP 200) translate §3.2 papers into node/edge graphs almost 1:1; they are the scaffolds to adapt. Generic loop:

```
route → retrieve(tool) → grade(retrieval evaluator) ─(good)→ generate → citation_gate ─(ok)→ END
                              │(weak)                                        │(unsupported clause)
                              └→ transform/re-query ──(loop, capped)         └→ regenerate (×1)
```

**Key LangGraph constraint (documented in our own `edges/routing.py`):** conditional-edge functions **do not persist state mutations** — only node return values merge into `GraphState`. Any grader/critic whose output must survive MUST be a **node**, not an edge side-effect. Store `requery_count`/`regenerate_count` in state and hard-cap them.

### 5.2 (b) Neo4j / KG-agentic retrieval (the on-point design for `graphont`)
Today `omd_context_assembly` calls the tri-channel `retrieve()` **once**. The agentic upgrade wraps that same retriever in a bounded graph-reasoning loop. Concrete node/edge design (additive `--mode agentic-graphont`):

1. **`concept_plan` (RoG-style planning)** — LLM proposes a **relation-path plan** over `:REL`/`:INVOKES` from the query concepts (e.g. `AccessControl → Authentication → PasswordPolicy`). Grounds retrieval in auditable graph paths, not free text. [RoG 2310.01061]
2. **`graph_retrieve` (existing tri-channel tool)** — run `omd_retrieval.retrieve()`; optionally seed concept-expansion depth from the plan (widen the `Q ∪ 1-hop :REL` step to plan-guided k-hop). Keep the cross-encoder rerank + weighted RRF as-is (they are assets — CRAG/Self-RAG add a loop *around*, not a replacement of, ranking).
3. **`retrieval_grade` (CRAG evaluator)** — prompt the existing OpenRouter judge to score the reranked clause set Correct/Ambiguous/Incorrect. **Replace CRAG's web-search fallback with corpus re-query** (§5.4). Must be a NODE (state persistence). [CRAG 2401.15884]
4. **`corpus_requery` (correction branch, capped ≤2)** — on weak grade, apply a deterministic ladder: (i) LLM query-rewrite [2305.14283]; (ii) decompose into sub-questions [2210.03350]; (iii) **expand another `:REL` hop / relax hub-gating**; (iv) reweight channels (e.g. lift `W_DENSE` per the in-code Exp #11/#28 findings) or deepen `RECALL_DEPTH`. Loop back to `graph_retrieve`.
5. **`generate` (existing primus node)** — unchanged.
6. **`citation_grounding_gate` (Self-RAG ISSUP)** — extract asserted clause IDs from the draft, verify each against retrieved `citation_id` metadata; strip/flag unsupported IDs or regenerate once. **This is the direct clause-citation-faithfulness lever.** [Self-RAG 2310.11511; ALCE 2305.14627]

**Optional, higher-value additions (from §4):**
- **Community-report channel** (Microsoft GraphRAG) to close the in-code "Channel-II not built" gap for global/thematic questions ("what are the CII governance themes across CCoP"). [2404.16130]
- **HippoRAG-style Personalized PageRank** over the concept graph as a *cheap* multi-hop recall pass — potentially matching an iterative loop at a fraction of the cost. [2405.14831]
- **ToG-2 alternation** (graph ↔ clause-text retrieval) for deep multi-clause questions, if the single re-query loop proves insufficient. [2407.10805]

### 5.3 (c) Qdrant note (older `hybrid` mode only)
The Qdrant + fastembed dense/BM25/RRF hybrid stack is used by the separate, older `hybrid` mode — **not** `graphont`. The same LangGraph agentic loop (§5.1) applies there unchanged (retriever swapped for the Qdrant adapter). The Neo4j GraphRAG package even lists Qdrant as an "external retriever" backend, so a hybrid graph+vector design is possible but out of scope here.

### 5.4 Why "no web fallback" (regulatory-corpus-specific)
CRAG's paper uses "large-scale web searches… as an extension." For CCoP — a **closed, authoritative, numbered corpus** — web fallback would import ungrounded/contradictory text and *destroy* clause-citation faithfulness. "Correction" must mean **re-query within CCoP** (rewrite / decompose / more graph hops / channel reweight). This is the single most important adaptation of the CRAG pattern for our domain.

---

## 6. Recommendation

**Adopt a bounded KG-agentic loop over the existing tri-channel Neo4j retriever, added as a distinct `--mode agentic-graphont`:** RoG-style `concept_plan` → existing `graph_retrieve` tool → CRAG-style `retrieval_grade` → corpus-internal `corpus_requery` (capped ≤2) → `generate` → Self-RAG `citation_grounding_gate` (regenerate ≤1). Reuse everything we have (Neo4j graph, IDF/`:REL`/`:INVOKES` structure, cross-encoder rerank, weighted RRF, OpenRouter judge, the LangGraph `decide_after_grading` skeleton).

**Rationale (evidence-backed).** (i) Self-RAG explicitly improves *citation accuracy* — our metric. (ii) RoG/ToG show KG-**path-grounded** reasoning is "faithful and interpretable" and gives "traceability" — for numbered clauses, a grounded path *is* a citation chain. (iii) CRAG's evaluator+correction is plug-and-play and maps onto our existing grade/decide skeleton. (iv) It's additive and iteration-capped, so batch cost stays bounded.

**Trade-offs accepted.** +1 to +3 extra LLM calls/case (plan + grade + gate, plus optional re-query) → higher latency/token cost ×435; mitigate with an Adaptive-RAG router (only complex cases loop) and/or a HippoRAG single-pass alternative. Reduced determinism from branching; mitigate with `temperature=0` graders, hard caps, and per-decision logging (pipeline already logs verbose retrieval diagnostics + `-contexts.json` sidecar).

**When NOT to do this.** If a diagnostic shows current top-k=8 already surfaces the governing clause and only *generation* mis-cites → ship **only** the `citation_grounding_gate` (cheapest high-value piece) and skip the loop. If per-case budget is hard-capped → prefer HippoRAG-style single-pass PPR over an iterative loop. A free-form ReAct agent is the wrong choice for the deterministic batch evaluator (reproducibility); reserve it for interactive `query ask`.

---

## 7. Disadvantages & Limitations

- **Cost/latency multiply ×435.** Each agentic hop is an LLM round-trip; uncapped loops blow up wall-clock and tokens. Caps + adaptive routing bound worst case but add control-flow complexity.
- **Grader quality is the ceiling.** A prompted CRAG evaluator / Self-RAG gate inherits the judge's blind spots (lenient → junk clauses pass; strict → needless re-queries). Calibrate against ground truth (reuse the 18-case κ bed).
- **Closed-corpus correction can still miss.** Without web fallback, if the governing clause is simply unrecalled by any channel (the in-code Act §7 / RtF §2.3 misses), the loop wastes passes. RoG planning / extra `:REL` hops / the reranker help but don't guarantee — the in-code docstring itself flags the reranker as the real fix for "recalled-but-diluted" clauses.
- **Prompted ≠ trained.** Self-RAG's native gains come partly from a fine-tuned critic; the prompt-based LangGraph approximation is weaker and adds calls *(magnitude unverified for our domain)*.
- **Reproducibility tension** for an *evaluation* framework whose job is stable measurement — branching + LLM graders reduce run-to-run identity. Needs strict determinism controls; may need multi-seed aggregate reporting.
- **KG-agentic adds graph-maintenance burden** — relation-path planning quality depends on `:REL`/`:INVOKES` completeness and the concept-alias surface map; the community-report channel (if added) needs a Leiden/summarization build step. Constraints inherited from Neo4j availability + the bge encoders + cross-encoder + OpenRouter rate limits.

---

## 8. Implementation Guidance

### 8.1 Verified current topology (`graphont`)
```
query_analysis ─(route_by_mode: mode=graphont)→ omd_context_assembly ─→ generate ─→ END
                                                   │ (calls omd_retrieval.retrieve(k=8) ONCE:
                                                   │  graphChannel-I ⊕ BM25 ⊕ bge-dense
                                                   │  → weighted RRF → cross-encoder rerank
                                                   │  + injected :Definition grounding)
```
Insertion points confirmed in code: `omd_context_assembly.py` (single `retrieve()` call), `route_by_mode` (additive mode branch precedent: `graphcpl`/`graphont`), `decide_after_grading` (existing conditional edge to reuse).

### 8.2 Proposed additive topology (`--mode agentic-graphont`, planner sketch — no code written)
```
query_analysis
   └─(mode=agentic-graphont)→ [adaptive_route?]
        ├ trivial → generate
        └ complex → concept_plan → graph_retrieve(omd tool) → retrieval_grade
                          ↑                                        │
                          └──── corpus_requery ◄──(weak, cap≤2)──(decide)
                                (rewrite/decompose/+:REL hop/reweight)
                                                                   │(ok)
                                                                   ▼
                                                          generate → citation_grounding_gate
                                                                   │(unsupported clause → regenerate ×1)
                                                                   ▼ (ok)
                                                                  END
```

### 8.3 New nodes to design (all NODES, not edges — state persistence)
1. `concept_plan` — RoG relation-path plan over `:REL`/`:INVOKES`. [2310.01061]
2. `retrieval_grade` — CRAG Correct/Ambiguous/Incorrect via OpenRouter judge; log buckets to `-contexts.json`. [2401.15884]
3. `corpus_requery` — deterministic re-query ladder; track `requery_count`. [2305.14283 / 2210.03350]
4. `citation_grounding_gate` — Self-RAG ISSUP over asserted clause IDs vs `citation_id` metadata; track `regenerate_count`. [2310.11511 / 2305.14627]
5. *(optional)* `community_report_channel` [2404.16130]; `ppr_recall` [2405.14831]; `adaptive_route` [2403.14403].

### 8.4 Gotchas
- **Conditional edges can't persist state** (our `routing.py` documents this empirically) → graders are nodes.
- **Hard-cap every loop** via state counters; never trust the LLM to stop.
- **`temperature=0`** for all graders; log every branch decision for diffable runs.
- **Calibrate on the 18-case stratified κ bed** (`bdc4927d`) before the full 435.
- **Keep the cross-encoder rerank + weighted RRF** — the papers add loops *around* ranking, not instead of it; our reranker is the documented fix for dilution.
- **No web fallback** (§5.4) — corpus-internal re-query only.

### 8.5 PoC scaffolds to copy
- LangGraph tutorials (verified live): Self-RAG, CRAG, Adaptive-RAG, Agentic-RAG — 1:1 node/edge translations of §3.2 papers.
- Neo4j GraphRAG Python package — `VectorCypherRetriever` / `Text2Cypher` as graph-tool references for the `graph_retrieve` / re-query nodes.

---

## 9. Open Questions & Risks

- **Retrieval vs. generation failure?** Run a diagnostic on the 18-case bed: if top-k=8 already contains the governing clause, ship only the citation gate. *(needs measurement)*
- **Legal/regulatory-specific citation evidence is thin.** The strongest transferable evidence is ALCE (general attribution) + RoG/ToG (KG-path faithfulness). I found **no fetched paper specifically measuring agentic-RAG clause-citation accuracy on a numbered regulatory corpus** — this is a genuine gap; treat the mapping "grounded KG path ≈ clause citation" as a well-motivated hypothesis, not a proven result. *(open)*
- **Which re-query lever recovers CCoP misses?** Empirical ablation needed (rewrite vs decompose vs +`:REL` hop vs channel reweight vs reranker upgrade to qwen3-reranker-8b).
- **Cost envelope** for 435 cases with +1–3 LLM calls each — decides whether adaptive routing / HippoRAG single-pass is mandatory.
- **Reproducibility** of an agentic evaluator — determinism controls sufficient, or multi-seed reporting needed?
- **Dependency risk:** OpenRouter rate/cost at scale; Neo4j uptime; concept-alias/`:REL` completeness bounding RoG plan quality.

---

## 10. References

*All arXiv abstracts fetched and read from arxiv.org on 2026-07-12; all doc URLs returned HTTP 200.*

**Agentic-RAG survey & text-RAG patterns**
- [Agentic Retrieval-Augmented Generation: A Survey on Agentic RAG, arXiv 2501.09136](https://arxiv.org/abs/2501.09136) — taxonomy (cardinality/control/autonomy/knowledge-rep); reflection/planning/tool-use/multi-agent.
- [Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection, arXiv 2310.11511](https://arxiv.org/abs/2310.11511) — reflection tokens; "gains in… citation accuracy for long-form generations."
- [Corrective Retrieval Augmented Generation (CRAG), arXiv 2401.15884](https://arxiv.org/abs/2401.15884) — lightweight retrieval evaluator + confidence-triggered actions; decompose-then-recompose; web-search extension (we swap for corpus re-query).
- [Adaptive-RAG, arXiv 2403.14403](https://arxiv.org/abs/2403.14403) — query-complexity classifier routes no/single/iterative retrieval.
- [FLARE: Active Retrieval Augmented Generation, arXiv 2305.06983](https://arxiv.org/abs/2305.06983) — retrieve-when-low-confidence; iterative regeneration.
- [IRCoT: Interleaving Retrieval with Chain-of-Thought, arXiv 2212.10509](https://arxiv.org/abs/2212.10509) — multi-step retrieval; "reduces model hallucination."
- [Self-Ask (Compositionality Gap), arXiv 2210.03350](https://arxiv.org/abs/2210.03350) — decomposition into follow-up questions.
- [Query Rewriting for Retrieval-Augmented LLMs (Rewrite-Retrieve-Read), arXiv 2305.14283](https://arxiv.org/abs/2305.14283) — LLM/RL query rewriting.
- [HyDE: Precise Zero-Shot Dense Retrieval without Relevance Labels, arXiv 2212.10496](https://arxiv.org/abs/2212.10496) — hypothetical-document embedding.
- [Take a Step Back (Step-Back Prompting), arXiv 2310.06117](https://arxiv.org/abs/2310.06117) — abstraction to principles; +7% MuSiQue.
- [ReAct: Synergizing Reasoning and Acting, arXiv 2210.03629](https://arxiv.org/abs/2210.03629) — tool-using reason+act agent.

**Citation / faithfulness evaluation**
- [ALCE: Enabling Large Language Models to Generate Text with Citations, arXiv 2305.14627](https://arxiv.org/abs/2305.14627) — first automatic citation-eval benchmark; fluency/correctness/citation-quality; "best models lack complete citation support 50% of the time." *(Corrected from an earlier draft's wrong ID 2305.06311, which is a different paper.)*
- [RAGAS: Automated Evaluation of RAG, arXiv 2309.15217](https://arxiv.org/abs/2309.15217) — reference-free faithfulness/context metrics.

**Graph / KG-agentic RAG (on-point for Neo4j `graphont`)**
- [From Local to Global: A Graph RAG Approach (Microsoft GraphRAG), arXiv 2404.16130](https://arxiv.org/abs/2404.16130) — entity KG + community summaries for global sensemaking (= our missing Channel-II).
- [Think-on-Graph (ToG), arXiv 2307.07697](https://arxiv.org/abs/2307.07697) — LLM-as-agent beam search over KG; "knowledge traceability and correctability"; training-free.
- [Think-on-Graph 2.0, arXiv 2407.10805](https://arxiv.org/abs/2407.10805) — tight-coupling iterative KG + document retrieval; "deep and faithful reasoning."
- [Reasoning on Graphs (RoG), arXiv 2310.01061](https://arxiv.org/abs/2310.01061) — planning-retrieval-reasoning; KG-grounded relation paths → "faithful and interpretable."
- [Graph Chain-of-Thought (Graph-CoT), arXiv 2404.07103](https://arxiv.org/abs/2404.07103) — iterative reason→graph-interact→execute; GRBench.
- [G-Retriever, arXiv 2402.07630](https://arxiv.org/abs/2402.07630) — RAG over textual graphs via Prize-Collecting Steiner Tree; hallucination-resistant.
- [HippoRAG, arXiv 2405.14831](https://arxiv.org/abs/2405.14831) — KG + Personalized PageRank; single-pass matches iterative IRCoT at 10–30× cheaper / 6–13× faster.
- [Graph Retrieval-Augmented Generation: A Survey, arXiv 2408.08921](https://arxiv.org/abs/2408.08921) — formalizes Graph-Based Indexing → Graph-Guided Retrieval → Graph-Enhanced Generation.

**Foundational**
- [Retrieval-Augmented Generation for Knowledge-Intensive NLP, arXiv 2005.11401](https://arxiv.org/abs/2005.11401) — original RAG (static baseline).
- [RAG for LLMs: A Survey, arXiv 2312.10997](https://arxiv.org/abs/2312.10997) — naive/advanced/modular RAG taxonomy.

**Official tooling docs (HTTP 200, fetched 2026-07-12)**
- [Neo4j GraphRAG for Python](https://neo4j.com/docs/neo4j-graphrag-python/current/) — `VectorRetriever` / `VectorCypherRetriever` / hybrid / **Text2Cypher** retrievers over a Neo4j driver; vector-index helpers; lists Qdrant/Weaviate/Pinecone as external retriever backends.
- [LangGraph — Self-RAG tutorial](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_self_rag/)
- [LangGraph — Corrective RAG (CRAG) tutorial](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_crag/)
- [LangGraph — Adaptive RAG tutorial](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_adaptive_rag/)
- [LangGraph — Agentic RAG tutorial](https://langchain-ai.github.io/langgraph/tutorials/rag/langgraph_agentic_rag/)
- [Neo4j LangChain — Cypher QA integration](https://python.langchain.com/docs/integrations/graphs/neo4j_cypher/)

**In-repo primary sources (read this session)**
- `src/rag/graph/ontology_v2/omd_retrieval.py` — tri-channel retriever, IDF/`:REL`/`:INVOKES` scoring, weighted-RRF constants, cross-encoder rerank, in-code known limitations.
- `src/rag/graph/ontology_v2/omd_context_assembly.py` (and `_neo.py`) — single-shot `retrieve(k=8)`; Neo4j driver.
- `src/rag/retrieval/graph.py`, `src/rag/retrieval/edges/routing.py` — LangGraph topology, `route_by_mode`, `decide_after_grading`, conditional-edge state-persistence pitfall.
