# FActScore — Fine-grained Atomic Evaluation of Factual Precision (Min et al., EMNLP 2023)

**Category**: Hallucination detection AND ground-truth design (atomic-fact decomposition)
**Canonical sources**:
- Paper: [Min et al., EMNLP 2023 — arXiv:2305.14251](https://arxiv.org/abs/2305.14251)
- Code: [shmsw25/FActScore](https://github.com/shmsw25/FActScore)
- Package: `pip install factscore`

## Scoring mechanics

FActScore = fraction of atomic facts in a generation that are supported by a reliable knowledge source.

### Two-stage pipeline

1. **Atomic Fact Generation (AFG)**:
   - Sentence-split the generation.
   - For each sentence, prompt an LLM: "List all independent factual statements in this sentence."
   - Output: a list of **atomic**, **context-independent**, **minimal** factual claims.
2. **Atomic Fact Validation (AFV)**:
   - For each atomic fact, retrieve relevant passages from the knowledge source (Wikipedia in the paper).
   - Verify the fact against retrieved passages via LLM (e.g., "Is 'Einstein was born in 1879' supported by this passage? YES/NO").
   - Score = fraction SUPPORTED.

### Composite

- FActScore is a single 0-1 precision metric per generation.
- Paper reports per-topic (e.g., per-biography) scores and aggregates.

## Prompt scaffolding

**AFG prompt** (simplified):
```
Decompose the following sentence into independent factual statements...
Sentence: {sentence}
Atomic facts:
1. ...
```

**AFV prompt** (simplified):
```
Knowledge:
{retrieved passages}

Claim: {atomic fact}
Is the claim supported by the knowledge? Output TRUE or FALSE.
```

## Ground-truth requirements — **the schema design contribution**

FActScore is dual-purpose: it's a metric AND a GT design method.

### As a GT design method

The paper argues that **binary "factual / not factual" ground truth is inadequate** for long-form text. Instead, ground truth should be:

- **Atomic**: one claim per GT entry, not one reference passage per generation.
- **Context-independent**: claims must stand alone ("Einstein was born in 1879", not "He was born in 1879").
- **Verifiable**: tied to a specific knowledge-source passage.

### Schema shape

```
{
  "topic": "Albert Einstein",
  "atomic_facts": [
    {"fact": "Einstein was born on March 14, 1879", "source": "wiki_einstein_intro"},
    {"fact": "Einstein was born in Germany", "source": "wiki_einstein_intro"},
    ...
  ]
}
```

**Knowledge source**: for FActScore, it's a Wikipedia dump + retriever; for our case, it would be the CCoP corpus + Qdrant retriever.

## Annotation cost

Paper reports:
- Human decomposition: ~15-30 min per biography yielding 20-40 atomic facts.
- GPT-4 can decompose at comparable quality; costs ~$0.01 per biography.
- Human verification is more expensive — ~1 hour per biography at >95% inter-annotator agreement.

**For our 118 test cases**: an average `expected_response` has 3-8 atomic facts. GPT-4 decomposition: ~1-2 hours + $3-5 API. Human verification: ~2-5 min per case (since our facts are shorter than biographies) = ~4-10 hours total.

## Bias / reliability controls

- **Atomic granularity** prevents "this answer is partially right" ambiguity — each fact is binary SUPPORTED/NOT.
- **Retrieval-based verification** decouples fact existence from the LLM's parametric knowledge.
- Automated FActScore reported **<2% error** vs human FActScore — impressive.
- Paper reports mixed results: **LMs are biased toward verifying claims they generated** — a form of self-enhancement bias in the verifier. Mitigation: use a different-family LLM for verification than for decomposition.

## Reported limitations

- Atomic-fact decomposition loses inter-fact dependencies ("He was born in Germany" depends on "he = Einstein"). The paper's AFG prompt tries to enforce context-independence, but this makes decomposition more expensive.
- **Precision only — no recall**: FActScore measures precision of stated facts, not whether the model missed important facts. For compliance QA where missing a CRITICAL requirement is the failure mode, precision alone is insufficient.
- Retrieval recall for the verification step caps the maximum FActScore — if the retriever misses the relevant passage, a true fact scores as unsupported.

## Domain fit for cybersecurity compliance QA

- **Highly applicable**: our `expected_response` is precisely the kind of free-text answer that FActScore was designed to decompose. Our CCoP corpus + Qdrant retriever directly plays the role of the knowledge source.
- **Highly applicable as GT enrichment**: our `key_facts` field is already a partial atomic-fact decomposition (but tied to the EXPECTED answer, not as a checklist for the RESPONSE). Extending `key_facts` into a full atomic-fact schema aligns our GT with FActScore conventions.
- **Complementary to D3**: our current D3 checks citation correctness (clause exists + attribution is right). FActScore checks claim-level grounding ("this specific statement is supported"). Both are needed for CCoP.
- **Recall gap**: FActScore is precision-only. To catch missing CRITICAL facts (our D2 / D1 concerns), we still need our `key_facts`-based recall check.

## Concrete borrowable patterns

1. **Atomic-fact field in GT**: add `expected_atomic_facts: list[{fact, source_clause, tier}]` to our schema. Our existing `key_facts` is close — needs explicit source-passage linkage.
2. **Automated decomposition**: for existing `expected_response` free-text, use GPT-4 to generate atomic facts, then expert-verify.
3. **Two-LLM verification**: decomposer LLM ≠ verifier LLM to mitigate self-enhancement bias.
4. **Precision + Recall**: report both — precision against model's claims (FActScore proper) AND recall against our `key_facts` CRITICAL tier.
5. **Retrieval-based verification**: our Qdrant store + clause text cache already provides this infrastructure — we just need the atomic-claim decomposition step added.

## Sources used

- Paper: https://arxiv.org/abs/2305.14251 (accessed 2026-04-24)
- ACL Anthology: https://aclanthology.org/2023.emnlp-main.741/ (accessed 2026-04-24)
- Code: https://github.com/shmsw25/FActScore (accessed 2026-04-24)
