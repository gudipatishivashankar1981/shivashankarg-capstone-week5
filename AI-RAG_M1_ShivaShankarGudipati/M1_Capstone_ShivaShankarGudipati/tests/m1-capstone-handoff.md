# EKA Capstone – Milestone 1 handoff

**Status:** M1 package complete and verified (51 unit tests pass; `scripts/validate_m1.py` passes, 1 warning: golden set not yet human-verified).
**Delivered:** `AI-RAG_M1_ShivaShankarGudipati.zip` (folder `M1_Capstone_ShivaShankarGudipati/`).

## Decisions locked in M1
- Fictional org: Meridian Digital Services (~14,000 employees). Corpus: 16 synthetic docs – HR 5, IT 6, Operations 5 (824–960 words each), doc ids HR-001…OPS-005, section-numbered for `doc_id#section` citations.
- Scope: single-turn English Q&A over Internal-classified policy docs; escalate when confidence < 0.40; refuse other people's Restricted data and security-bypass requests. Out: transactions, personal records, legal/medical advice, multi-turn, other languages.
- API (ADR 0002): `POST /ask` -> `Answer` v1 {content, cost_usd, retries, confidence, sources, schema_version="v1"}; escalation by convention (confidence < 0.40, 200 OK); path-based major versioning, additive-only changes within v1, 6-month deprecation window; uniform error envelope; bearer tokens via `EKA_API_TOKENS` (fail closed); no question text in logs by default; daily cost budget per caller.
- Planned v1.1 additive fields: `escalated`, `citations[]`, `request_id`.
- Tech approach (ADR 0001): hybrid retrieval (BM25 + embeddings) + reranker, pgvector/Postgres first, hosted LLM behind a model-agnostic gateway, grounded generation with citations, answer-support check, golden-set CI gate.

## KPIs (ADR 0001)
| KPI | Baseline | Target |
|---|---|---|
| K1 Question resolution rate | 38% (estimate) | 55% @3 mo, 70% @6 mo |
| K2 Answer accuracy | 25% measured (lexical baseline, 4/16 answerable pass; 1/4 hard) | >=90% answerable; 100% correct escalation on hard |
| K3 Knowledge tickets / month | 9,000 (estimate) | -30% @6 mo, -40% @12 mo |

## Baseline (offline BM25 + extractive, untuned): overall 25% pass; easy 50%, medium 0%, hard 25%
Saved in `eval_results/baseline.json`; compare future runs with `python scripts/run_rag_eval.py --fake --label X --compare baseline`.

## Known gap: ADR design vs M1 baseline code (documented in ADR 0001 "Known gaps", ADR 0002, DR1)
- ADR target: confidence = retrieval strength + evidence agreement + answer-support check. Baseline code: IDF-weighted term coverage of the top-1 chunk only.
- Effect: uncalibrated (mean confidence 0.56 on passed vs 0.51 on failed); 0.40 threshold is an untuned starting value; 3/4 hard questions answered instead of escalated; 5 answerable questions escalated.
- Also optional: `EKA_HANDLER=baseline` serves the lexical baseline through `/ask` (src/pipeline/baseline_handler.py).

## Open items / to do
1. Human-verify all 20 golden questions (set `human_verified`, `verified_by`, `verified_on`); `validate_m1.py --strict` enforces.
2. Replace K1/K3 baseline estimates with real ticket/survey data before DR#1.
3. Open questions for DR#1: approved LLM + region; who signs off escalation wording; role-based access for manager-only content.
4. Next milestones: ingestion + chunking + hybrid retrieval behind the existing handler protocol (`src/pipeline/handler.py`); grow golden set to 100+ from real queries.
