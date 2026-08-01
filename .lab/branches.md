# Branch Registry

| Branch | Forked from | Status | Experiments | Best metric | Notes |
|--------|-------------|--------|-------------|-------------|-------|
| research/maximize-rag-vs-llm-only | a67bbb7 (feature/phase2-eval) | plateau | #0-#25 | recall@C=0.4874 (Exp #19) | Stack: contextual + decoupled reranker + HyDE + parent-child merge (w=15). 6 consecutive discards (#20-25) post-#19 → MANDATORY FORK. Reranker is binding constraint at 0.487. |
| research/no-reranker-stack | a67bbb7 (baseline #0) | wrap-up | #26-#41 | recall@C=0.5484 (Exp #41, correctness-preserving) | Production-defensible best uses Exp 41's acronyms-only contexts (no hallucinations). Stack: contextual_v3 + HyDE + RRF(dense,CE=1.5) + merge(w=40). +286% vs baseline. Distance to 0.8: 0.252. Note: Exp 33 scored higher (0.6534) but relied on hallucinated CIIO expansions — disqualified for production/dissertation. |
