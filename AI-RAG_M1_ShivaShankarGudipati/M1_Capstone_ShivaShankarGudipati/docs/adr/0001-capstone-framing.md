# ADR 0001: Capstone Framing – Enterprise Knowledge Assistant (EKA)

| | |
|---|---|
| **Status** | Accepted (Milestone 1, subject to Design Review DR#1) |
| **Date** | 2026-11-07 |
| **Decision owner** | Shivashankar Gudipati, AI Solutions Architect |
| **Reviewers** | Design Review panel (DR#1); HR, IT Service Delivery and Information Security representatives |
| **Related** | ADR 0002 (API contract), `docs/stakeholder-map.md`, `data/golden_set_full.jsonl`, `scripts/run_rag_eval.py` |

## 1. Context

Meridian Digital Services (a fictional global IT-services firm of roughly 14,000 employees in India, the UK and the US) keeps its operational knowledge in policy documents, handbooks and procedures spread across HR, IT and Operations. Employees get answers in four ways, and each one is slow or unreliable:

- They ask the **HR Service Desk or an HR Business Partner** for policy clarifications (leave, hybrid work, performance, benefits).
- They ask the **IT Helpdesk** for technical procedures (VPN, passwords, devices, software requests).
- They ask **their manager** for operational rules (expenses, procurement approvals, hiring, delivery governance).
- They try the **internal portals**, whose keyword search returns long documents and often the wrong version.

The result is repeated questions, avoidable tickets, manager and SME interruptions, and inconsistent answers. The corpus that would answer most of these questions already exists and is already approved. What is missing is a fast, trustworthy way to reach it.

## 2. Problem statement

> Employees cannot quickly get an accurate, sourced answer to routine HR, IT and operational questions, so they raise tickets and interrupt people who then answer the same questions repeatedly.

We will build an **Enterprise Knowledge Assistant (EKA)** that retrieves approved internal knowledge, answers in plain language, cites its sources, states how confident it is, and **hands the employee to a human when it cannot answer reliably**. Milestone 1 does not build the RAG pipeline. It fixes the scope, the corpus, the evaluation set, the API contract and the success measures that every later milestone will be judged against.

## 3. EKA scope

**Scope test.** The EKA must satisfy all three conditions of the brief:

| Condition | How this scope meets it |
|---|---|
| **Enterprise** | Only internal organisational documents (HR, IT, Operations), all classified Internal and approved for project use. Authenticated employees only. |
| **Knowledge** | Retrieves and quotes existing content. It does not invent policy and does not answer from general model knowledge. |
| **Assistant** | Question-and-answer interaction: one question in, one cited answer out, or a graceful escalation. |

**In scope (locked for M1–M5)**

- Single-turn, English-language question answering over 16 documents in three topic clusters: HR (5), IT (6) and Operations (5).
- Cross-document synthesis, for example a new-joiner question that touches HR, IT and manager guidance.
- Source citations as `doc_id[#section]`, a confidence score from 0 to 1, per-request cost and retry count.
- Escalation to the right human channel (HR Service Desk, IT Helpdesk) when evidence is missing or confidence is below 0.40.
- Refusal of requests for another person's Restricted data and of requests to bypass security controls.
- Evaluation against a human-verified golden set, with a regression gate in CI.

**Out of scope (explicitly)**

- Transactions and workflows (applying for leave, raising tickets automatically). Later versions may hand off to ServiceHub or PeopleHub.
- Personalised answers that need the employee's own records (their leave balance, their rating).
- Legal, medical, tax or immigration advice, and any statutory entitlement beyond what the policy documents say.
- Unapproved sources: email, chat, shared drives, client project documents, Confidential or Restricted material.
- Multi-turn memory, multi-language support and voice. Scheduled for later evaluation, not for the baseline.

## 4. Stakeholders

Detailed personas are in `docs/stakeholder-map.md`. In summary:

| Stakeholder | Interest in the EKA | What they need from M1 |
|---|---|---|
| **Executive sponsor** (VP Employee Experience) | Fewer tickets, faster answers, risk under control | KPI targets with baselines and a business case |
| **Employees** (Ananya Rao, new joiner) | Quick, trustworthy answers without waiting | Plain answers with a visible source |
| **People managers** (Marcus Chen, Delivery Manager) | Fewer interruptions, answers they can forward | Citations and cross-document answers |
| **HR Business Partners** (Priya Nair) | Policy answered consistently; ownership of content | Clear content ownership; analytics on gaps |
| **IT Service Desk** (Rahul Mehta) | Deflection of how-to tickets with clean hand-off | Escalation that carries context |
| **Information Security, Privacy and Legal** | No data leakage, auditable behaviour | Data-classification rules enforced; logging without question text |
| **AI/engineering team** | A stable contract and a measurable baseline | ADR 0002, golden set, evaluation harness |

## 5. KPI targets

Three sponsor-level KPIs decide whether the EKA is a success. **Baselines marked "estimate" are illustrative planning assumptions for this fictional organisation and must be replaced with real figures from a ticket export and an employee survey before DR#1 sign-off.** The accuracy baseline is measured, not estimated.

| # | KPI | Definition | Baseline | Target | Business justification |
|---|---|---|---|---|---|
| **K1** | **Question resolution rate** (self-service) | Share of employee knowledge questions resolved by the EKA with no human follow-up (answer accepted, or no ticket or email on the same topic within 48 hours) | **38%** (estimate: portal search success and intranet survey) | **≥ 55% at 3 months, ≥ 70% at 6 months** after pilot launch | Every unresolved question becomes a ticket or an interruption. Resolution at the first touch is the main driver of both cost reduction and employee experience. |
| **K2** | **Answer accuracy** (information retrieval accuracy) | Share of answers that are correct, complete and supported by the cited sources, measured on the golden set and by a monthly SME audit of 100 sampled production answers. Hard questions must be refused or escalated correctly. | **25%** measured on the golden set by the M1 lexical baseline (`run_rag_eval.py --fake`: 4 of 16 answerable questions passed; 1 of 4 hard questions handled correctly) | **≥ 90%** of answerable questions and **100%** correct escalation or refusal on hard questions | A wrong answer about leave, expenses or security carries compliance and trust costs far above the savings. Adoption depends on trust, and trust is lost faster than it is won. |
| **K3** | **Helpdesk ticket reduction** | Monthly count of policy and how-to tickets across the HR Service Desk, IT Helpdesk (P4 how-to) and Finance or Procurement queries | **9,000 per month** (estimate: HR 3,200; IT 4,300; Ops and Finance 1,500) | **−30% (≤ 6,300 per month) at 6 months; −40% at 12 months** | Direct EBIT effect. Illustrative case: 2,700 tickets avoided per month × USD 6 handling cost ≈ USD 194k per year, plus about USD 162k per year of manager and SME time (assuming half of deflected queries would have interrupted a person: 2,700 × 12 × 50% × 0.25 h × USD 40). Against an assumed run cost below USD 100k per year, the net benefit is about USD 250k per year. |

**Supporting metrics and guardrails** (tracked, but not sponsor-level):

| Metric | Target |
|---|---|
| Citation precision (cited documents that are the right documents) | ≥ 90% |
| Escalation recall on questions the corpus cannot answer | 100% on the golden set; ≥ 95% in production audits |
| False-escalation rate on answerable questions | ≤ 15% |
| Time to answer (replaces a 1-business-day P4 response target) | Median ≤ 4 s and p95 ≤ 8 s of server time |
| Cost per answered question | ≤ USD 0.03 |
| Monthly active users (adoption) | ≥ 60% of employees at 6 months |
| Restricted-data leakage incidents | 0 |

## 6. Technology approach

**Decision: a grounded Retrieval-Augmented Generation (RAG) pipeline behind a stable HTTP contract, built in thin vertical slices and gated by the golden set.**

```
Approved documents ──► Ingest & version ──► Chunk by section ──► Index (BM25 + embeddings)
                                                                   │
Employee ──► POST /ask ──► Auth, log, cost ──► Hybrid retrieve ──► Rerank ──► Grounded generation
                                  │                                              │
                                  │                       Cite sources + score confidence
                                  ▼                                              │
                          Cost / audit log ◄─────────── Answer (schema v1) ◄──── Escalate if confidence < 0.40
```

| Layer | Decision for the baseline | Rationale |
|---|---|---|
| Ingestion | Markdown/PDF/Word converted to sectioned text with metadata: `doc_id`, version, owner, classification, effective date | Citations and freshness need the structure of the source. |
| Chunking | Section-aware, about 300–500 tokens, light overlap; each chunk keeps its section number | Policy questions are answered by whole clauses; section IDs give precise citations. |
| Retrieval | Hybrid: BM25 plus dense embeddings, then a cross-encoder reranker; retrieve 20, rerank to 5 | Policies are full of exact terms and numbers (“USD 50”, “P1”) that lexical search handles well, while paraphrased questions need embeddings. |
| Store | PostgreSQL with pgvector and full-text search for the first release | One familiar datastore. Revisit if chunk volume or latency requires a dedicated engine. |
| Generation | Hosted enterprise LLM behind a model-agnostic gateway; strict “answer only from the provided passages and cite them” prompt | Avoids fine-tuning cost, allows model swaps, and keeps the model choice out of the contract. |
| Confidence and escalation | Score combines retrieval strength, evidence agreement and an answer-support check; below 0.40 the EKA escalates | Abstaining is a feature: a graceful “ask HR” beats a confident error. |
| Governance | Document-level access metadata, no Restricted content in the index, no question text in logs by default, audit trail | Meets the data-classification rules in IT-006. |
| Evaluation | Golden set plus a baseline harness now; LLM-as-judge calibrated against SME review later; CI regression gate | Every change is compared with the saved baseline. |

**Evidence from this milestone.** The offline lexical baseline (BM25 and extractive answers) passes 25% of the golden set overall: 50% of easy questions, 0% of the cross-document questions and 25% of the hard ones. This is the floor to beat. It confirms the two design bets: single-document lookups are within reach of retrieval, but cross-document synthesis, calibrated confidence and abstention need real generation, reranking and an answer-support check.

## 7. Alternatives considered

| Option | Why it is attractive | Why we did not choose it |
|---|---|---|
| **A. Do nothing; improve portal search only** (enterprise search, synonyms, tagging) | Cheapest, no generative risk | Returns documents, not answers. Employees still read 800-word policies and cross-document questions stay unanswered. Does not move K1 or K3 enough. |
| **B. Fine-tune an LLM on policy documents** | Fluent, no retrieval step at run time | Cannot cite sources, goes stale when policy changes, expensive to retrain, and still hallucinates. Poor fit for auditable policy answers. |
| **C. Long-context “stuff every document in the prompt”** | Simple to build and works for 16 documents | Cost and latency scale with corpus size and not with question complexity; weakens citation precision; breaks down at realistic corpus sizes. Retained as an evaluation comparator. |
| **D. Buy a SaaS virtual-agent product** | Fast to launch, vendor-managed | Less control over grounding, citations, escalation rules and data residency; harder to evaluate against our own golden set. Retained as a build-versus-buy checkpoint at the end of M3. |
| **E. Rule-based FAQ chatbot / decision trees** | Predictable, easy to approve | Needs manual maintenance for every question and cannot synthesise across documents. Covers the easy 40% and none of the rest. |
| **F. Grounded RAG with hybrid retrieval (chosen)** | Answers with citations, updates when documents change, supports escalation | More moving parts, needs evaluation discipline and content ownership; mitigated by the design below. |

## 8. Trade-offs

| Tension | Our position | Cost we accept |
|---|---|---|
| **Accuracy versus coverage** | Prefer a correct escalation over a plausible guess. Threshold 0.40, tuned on a held-out set. | A lower resolution rate in the early months; some answerable questions will escalate. |
| **Latency versus quality** | Reranking and an answer-support check add roughly 0.5–1.5 s. Target p95 of 8 s. | Slower than a bare LLM call, but a visibly sourced answer within seconds still beats waiting a business day. |
| **Cost versus quality** | Start with a mid-size model; route only low-confidence cases to a larger model. | Some complex cross-document answers may need a second pass. |
| **Build versus buy** | Build the pipeline and evaluation; consume the LLM and vector store as services. | Engineering ownership, in exchange for control of grounding and the contract. |
| **Freshness versus stability** | Re-index on document publication; every answer cites a document version. | Short window after a policy change where the index lags; mitigated by effective-date metadata. |
| **Simplicity versus scale** | One datastore (PostgreSQL) for the first release. | Possible migration if the corpus grows by orders of magnitude. |
| **Transparency versus brevity** | Always show sources and confidence. | Longer answers and a more cautious tone. |
| **Contract stability versus speed of change** | Freeze schema v1 now (ADR 0002); evolve by additive fields. | Some desirable fields (for example a structured citation list) wait for v1.1. |

## 9. Consequences, risks and open questions

**Consequences.** The API contract and evaluation set are fixed early, so retrieval and model choices can change without breaking consumers. The golden set becomes a governance artefact and must be owned and versioned. Content owners in HR, IT and Operations become part of the operating model, because the assistant is only as good as the documents behind it.

**Key risks and mitigations**

| Risk | Mitigation |
|---|---|
| Confident wrong answer on a policy | Strict grounding, abstention threshold, citation display, monthly SME audit, golden-set gate. |
| Stale or conflicting documents | Version and effective-date metadata; content-owner review dates; conflict tests added to the golden set. |
| Leakage of Restricted data | Index only Internal content in M1–M3; document-level access control before any Confidential content; no question text in logs. |
| Employees stop trusting after one miss | Visible confidence, easy “talk to a human” path, quick fix loop for reported errors. |
| Golden set too small or too easy | 20 questions is a baseline, not a ceiling; grow to 100+ questions from real queries in the pilot. |
| Cost drift | Per-request cost in every response, daily budget guard, cost per question as a tracked KPI. |

**Open questions for DR#1.** (1) Real ticket volumes and costs to replace the estimates in section 5. (2) Which approved enterprise LLM and region will be used. (3) Who signs off the escalation wording for each channel. (4) Whether manager-only content (for example calibration guidance) needs role-based access in the first release.

## 10. Review triggers

Revisit this decision if: the golden-set pass rate on answerable questions stays below 70% after the M3 build; the corpus grows beyond 30 documents or includes Confidential content; the hosting or data-residency constraints change; or a build-versus-buy review shows a vendor can meet K1–K3 with equivalent controls.
