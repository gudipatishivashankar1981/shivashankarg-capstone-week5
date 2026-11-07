# ADR 0002: API Contract – `POST /ask` and Answer Schema v1

| | |
|---|---|
| **Status** | Accepted (Milestone 1) |
| **Date** | 2026-11-07 |
| **Decision owner** | Shivashankar Gudipati, AI Solutions Architect |
| **Related** | ADR 0001 (framing), `src/pipeline/models.py`, `src/api/main.py`, `tests/test_models.py` |

## 1. Purpose of the API contract

The EKA will change many times over the coming months: new retrievers, rerankers, models, prompts and guardrails. The consumers will not: the intranet widget, the chat bot, the evaluation harness, the cost dashboard and, later, ServiceHub and PeopleHub. This contract is the single stable seam between them.

The contract exists to:

1. Let the pipeline be rebuilt behind the API without breaking any consumer.
2. Make **trust signals first-class**: every answer carries its sources, a confidence score, its cost and its retry count.
3. Give the evaluation harness and production the **same response shape**, so test results predict production behaviour.
4. Define **how the contract itself may change** (section 4), so that change is deliberate and reviewable.

## 2. `/ask` endpoint specification

### 2.1 Summary

| Item | Value |
|---|---|
| Method and path | `POST /ask` (this is the v1 endpoint; a future major version is served at `/v2/ask`) |
| Authentication | `Authorization: Bearer <token>` (static service tokens in M1, SSO-issued JWTs later) |
| Request content type | `application/json` |
| Response content type | `application/json` |
| Side effects | None on business data. The call is logged and its cost is recorded, so clients may safely retry after a timeout. |
| Timeouts | Server target p95 ≤ 8 s. Clients should use a 30 s timeout. |
| Also exposed | `GET /health` (public liveness probe) and `GET /usage` (the caller's spend for the current UTC day) |

### 2.2 Request body

| Field | Type | Required | Rules |
|---|---|---|---|
| `question` | string | yes | 3–2,000 characters after trimming whitespace. |
| `top_k` | integer | no | 1–10, default 5. A hint for how many passages to retrieve. The server may ignore it. |

Unknown fields are rejected with `422` so that client typos fail loudly.

### 2.3 Response body: `Answer` (schema version `v1`)

```python
class Answer(BaseModel):
    content: str
    cost_usd: float
    retries: int
    confidence: float
    sources: list[str]
    schema_version: str = "v1"
```

| Field | Meaning and rules |
|---|---|
| `content` | The answer in plain language, or the standard escalation message. Never empty. |
| `cost_usd` | Total retrieval and model cost of producing this answer, in USD. ≥ 0. Placeholder and escalation-only responses may be 0. |
| `retries` | Number of generation or retrieval retries the pipeline used. ≥ 0. |
| `confidence` | Calibrated score from 0.0 to 1.0 that the answer is correct and supported by its sources. Not a raw model probability. |
| `sources` | Citations as `"<doc_id>"` or `"<doc_id>#<section>"`, for example `"HR-001#2"`. Ordered by relevance. May be empty only when the response is an escalation. |
| `schema_version` | The contract version that produced this body. Always `"v1"` on `/ask`. |

**Escalation convention (v1).** There is no separate escalation flag in v1. Clients **must** treat `confidence < 0.40` as “the assistant could not answer reliably” and route the employee to a human. In that case `content` starts with the standard escalation message naming the HR Service Desk and IT Helpdesk, and `sources` may be empty. This keeps the five required fields stable while making failure handling explicit. A dedicated flag arrives as an additive change in v1.1 (section 6).

### 2.4 Example: successful answer

```http
POST /ask HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{"question": "How many days of annual leave do employees receive?"}
```

```json
{
  "content": "Full-time employees receive 20 working days of paid annual leave per calendar year.",
  "cost_usd": 0.0021,
  "retries": 0,
  "confidence": 0.94,
  "sources": ["HR-001#2"],
  "schema_version": "v1"
}
```

### 2.5 Example: graceful escalation (also what the M1 placeholder returns)

```json
{
  "content": "I couldn't find a reliable answer to this in the approved knowledge base. Please contact the HR Service Desk (hrdesk@meridian.example) for people and policy questions, or the IT Helpdesk (ServiceHub, extension 5555) for technology questions.",
  "cost_usd": 0.0009,
  "retries": 1,
  "confidence": 0.18,
  "sources": [],
  "schema_version": "v1"
}
```

### 2.6 Response headers

| Header | Purpose |
|---|---|
| `X-Request-ID` | Correlation ID. A client-supplied value (8–64 characters of `A-Za-z0-9._-`) is echoed; otherwise one is generated. Quote it in support requests. |
| `X-Cost-USD` | Same value as `cost_usd`, for gateways and dashboards that do not parse the body. |
| `X-Schema-Version` | Same value as `schema_version`. |

### 2.7 Errors

Every non-2xx response uses one envelope. Input text is never echoed back, because questions can contain personal data.

```json
{"error": {"code": "invalid_request", "message": "Request body failed validation.", "request_id": "9f2c…", "details": [{"field": "question", "message": "String should have at least 3 characters"}]}}
```

| Status | `error.code` | When |
|---|---|---|
| 401 | `unauthorized` | Missing, malformed or invalid bearer token (includes the case where no tokens are configured: the service fails closed). Response carries `WWW-Authenticate: Bearer`. |
| 422 | `invalid_request` | Body fails validation. `details` lists the offending fields. |
| 429 | `budget_exceeded` | The caller has used its daily cost budget. Retry after 00:00 UTC or ask for a higher budget. |
| 500 | `internal_error` | Unexpected failure. No internal detail is returned; the cause is in the server log under the same `request_id`. |
| 404 / 405 | `not_found` / `method_not_allowed` | Unknown path or method. |

“I don't know” is **not** an error. It is a successful `200` with low confidence and an escalation message, so that clients handle it as a normal path.

### 2.8 Security and operations built into the contract

- **Authentication.** Bearer tokens are loaded from configuration, compared in constant time, never logged and never baked into code.
- **Logging.** One structured line per request: request ID, method, path, status, latency, principal, question length and a short hash, confidence, source count, retries and cost. **Question text is not logged by default.**
- **Cost control.** Per-principal daily budget checked before paid work starts; spend visible in `X-Cost-USD` and `GET /usage`.

## 3. Alternatives considered

| Alternative | Why we did not choose it |
|---|---|
| **OpenAI-style chat-completions API** | Familiar to developers, but it has no native field for sources, confidence or cost, and it invites free-form, multi-turn prompts we have scoped out. We would be extending it immediately. |
| **GraphQL** | Flexibility we do not need. One question, one answer. Adds a schema layer and makes cost and rate control harder. |
| **gRPC** | Efficient for service-to-service traffic, but the first consumers are browsers and an evaluation script. Can be added later behind the same models. |
| **Streaming-first (SSE or WebSocket)** | Better perceived latency, but harder to test, log, cache and evaluate. Planned as an additive mode once the non-streaming baseline is stable. |
| **Header or media-type versioning only** | Hidden from logs, gateways and curl examples, and easy to forget. Path versioning is explicit and routable. |
| **No version at all (“we will not break anyone”)** | Breaks consumers silently. The `schema_version` field costs one string and makes drift detectable. |
| **Return 404/204 when nothing is found** | Forces every client to special-case “no answer”. A `200` with low confidence and an escalation message is one code path. |
| **Separate `/escalate` endpoint** | Splits one user interaction into two calls and leaks an internal decision. A convention in the response is simpler for v1. |
| **Rich answer object now** (structured citations, steps, follow-ups) | Better UX, but it widens the contract before we know what consumers need. Better to ship the minimal five fields and add proven fields. |

## 4. Schema versioning rules

1. **Two version markers.** The *path* carries the major version (`/ask` is v1, `/v2/ask` would be v2). The body field `schema_version` states the contract that produced the response. They must agree.
2. **Compatible changes (allowed within v1, no new path).** Adding an optional response field with a default; adding an optional request field; adding a new endpoint; adding a new `error.code`; tightening a documented range only where no valid value is rejected; improving answer quality, calibration or latency.
3. **Breaking changes (require v2).** Removing or renaming a field; changing a field's type, units or meaning (for example redefining `confidence`, or `cost_usd` becoming cents); making an optional request field required; changing the format of `sources` entries; changing the escalation convention; changing authentication in a way that rejects current clients.
4. **Tolerant-reader rule for consumers.** Clients must ignore unknown response fields and must not depend on field order. The server rejects unknown *request* fields.
5. **Deprecation.** A breaking change ships as a new major version served alongside the old one. The old version is supported for at least **6 months** after the new one is generally available and returns `Deprecation` and `Sunset` headers during that window.
6. **Review gate.** Every change to `Answer` needs an ADR amendment, an updated changelog entry and a passing contract test. `tests/test_models.py` freezes the v1 field set and types, and fails on any addition, removal or rename.
7. **Evaluation alignment.** The harness records `schema_version` in each saved run so results from different contract versions are never compared silently.
8. **Semantics of `confidence`.** Changing the *method* used to compute confidence (for example a new calibration) is a compatible change but must be announced in the changelog, because the 0.40 escalation threshold is re-tuned with it. The escalation threshold is part of the contract; changing it needs a changelog entry and a new baseline run.

## 5. Trade-offs

| Decision | Benefit | Cost |
|---|---|---|
| Minimal five-field `Answer` | Stable, easy to implement and test; forces trust signals into every response | No structured citations, no explicit escalation flag in v1 |
| Escalation by convention (`confidence < 0.40`) | One response shape for all outcomes | Clients must know the convention; a threshold change affects all of them |
| `200` for “cannot answer” | One happy path, simple clients | Monitoring must look at confidence, not only HTTP status |
| Cost in body and header | Easy cost attribution and FinOps | Exposes internal cost figures to every authorised client |
| Static bearer tokens in M1 | Simple, testable, fail-closed | Service-level identity only: no per-user personalisation or document-level access control yet |
| Path-based major versions | Explicit, routable, observable | Two versions in parallel during migration |
| Strict request validation | Typos and abuse fail fast | Slightly less forgiving for early clients |

## 6. Future evolution strategy

| Step | Change | Type | Why and when |
|---|---|---|---|
| **v1.1** | Add `escalated: bool` (default `false`) | Additive | Replace the threshold convention with an explicit flag once the escalation policy is stable (M3). |
| **v1.1** | Add `citations: list[Citation]` (`doc_id`, `title`, `section`, `url`, `snippet`, `version`) while keeping `sources` | Additive | Richer source display; `sources` stays for existing clients. |
| **v1.1** | Add `request_id` to the body | Additive | Easier support from UI logs. |
| **v1.2** | `POST /feedback` (thumbs, reason, `request_id`) | New endpoint | Feeds K1/K2 measurement and the golden set. |
| **v1.2** | Optional streaming mode (`Accept: text/event-stream`) | Additive | Perceived latency, after the baseline is stable. |
| **v1.3** | Optional `session_id` and conversation context | Additive | Multi-turn follow-ups, currently out of scope. |
| **Auth** | Replace static tokens with SSO-issued JWTs carrying user, role and region | Auth change | Enables personalised answers and document-level access control. If it rejects existing clients, it ships as v2. |
| **v2** | Only if a breaking change cannot be avoided: for example, `confidence` split into retrieval and answer confidence, or structured multi-part answers | Breaking | Served at `/v2/ask` alongside v1 for at least six months. |

**Operational follow-ups.** Add contract tests to the consumers' CI; publish the OpenAPI document (generated from `src/api/main.py`) as the single source of truth; move the in-memory cost ledger to a shared store; add per-principal rate limiting alongside the cost budget.
