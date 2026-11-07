# Stakeholder Map – Enterprise Knowledge Assistant (EKA)

The personas below are fictional but built from the question patterns the EKA must serve. Together they cover the three groups that ask questions (employees, managers) and the three groups that answer or govern them (HR, IT, the executive sponsor). Figures are planning assumptions to be validated with real ticket data (see ADR 0001, section 5).

## At a glance

| # | Persona | Role | Primary need | Main EKA value | Influence | Interest |
|---|---|---|---|---|---|---|
| 1 | Ananya Rao | Associate Consultant (new joiner) | Fast answers on leave, VPN, expenses | Self-service in seconds | Medium | High |
| 2 | Marcus Chen | Delivery Manager | Reliable rules he can forward with a source | Fewer interruptions, cross-document answers | High | High |
| 3 | Priya Nair | HR Business Partner | Consistent policy answers, less repetition | Deflects routine queries, shows content gaps | High | High |
| 4 | Rahul Mehta | IT Service Desk Lead | Lower how-to ticket volume, clean hand-offs | Ticket deflection with context | High | High |
| 5 | Elena Fischer | VP, Employee Experience (executive sponsor) | Measurable outcomes with controlled risk | KPI evidence and a scalable service | Very high | High |

---

## Persona 1: Ananya Rao – Associate Consultant (new joiner)

**Role and experience.** Associate Consultant in the Pune delivery centre, 14 months with Meridian and in her first job after graduating. Works on a client application-support team, hybrid three days a week. Confident with technology, less confident about “how things work here”, and reluctant to look uninformed by asking her manager.

**Current workflow.** When she has a question, she first searches the intranet, finds a 20-page policy and gives up after a few minutes. She then asks a teammate in chat, whose answer may be out of date, or raises a ticket and waits up to a business day. For urgent questions (VPN failing before a client call) she calls the helpdesk and waits in a queue. Typical questions: “How many leave days do I get and what carries over?”, “Can I work from another city for a week?”, “How do I claim my travel?”

**EKA usage pattern.** Uses it several times a week, in short bursts, usually from the intranet chat widget on her phone or laptop. Questions are short and informal. She expects an answer in seconds, glances at the source link when the answer affects money or leave, and escalates to HR only when the EKA says it cannot answer.

**Benefits if the EKA succeeds.**

- Gets a correct answer in seconds instead of waiting up to a business day.
- Stops guessing or relying on second-hand answers, so mistakes such as claiming expenses late (the 30-day limit) fall.
- Gains confidence to ask “small” questions without feeling judged.
- Spends the saved time on client work.

**What would break her trust.** A confident wrong answer about leave or pay, or an answer with no source she can open.

**Success measure.** Share of her questions answered without a ticket; thumbs-up rate (K1, supporting metric).

---

## Persona 2: Marcus Chen – Delivery Manager

**Role and experience.** Delivery Manager with 12 years in IT services, based in London, leading 18 people across two client programmes. Responsible for hiring, onboarding, approvals, status reporting and incident escalation. Time-poor and frequently interrupted.

**Current workflow.** His team brings him questions about leave during release freezes, who approves a vendor purchase, how to onboard a new joiner and what to do during a client incident. He answers from memory, searches several policy documents, or asks HR and Procurement, and sometimes gets conflicting answers. When he forwards an answer to a client or a team member, he has to find the original document to prove it.

**EKA usage pattern.** Uses it a few times a day, often between meetings and from his laptop, for **multi-part, cross-document questions**: “New hire starts in three weeks – what do I need to arrange?”, “My lead developer wants leave during the quarter-end freeze – is that allowed?” He expects a combined answer with citations that he can forward, and will check the cited section before acting on anything involving approvals or money.

**Benefits if the EKA succeeds.**

- Fewer interruptions: team members get answers themselves.
- One consolidated answer instead of searching three policies.
- A citation to forward, ending “where does it say that?” threads.
- Fewer mistakes in onboarding and approvals (for example ordering a laptop at least 10 working days before the start date).
- More time for client delivery, which feeds utilisation and margin.

**What would break his trust.** Answers that merge policies incorrectly, or a missing escalation path during an incident.

**Success measure.** Manager interruptions per week; accuracy on cross-document questions (K2).

---

## Persona 3: Priya Nair – HR Business Partner

**Role and experience.** HR Business Partner with 9 years in HR, supporting about 600 employees across delivery and sales. Owns the interpretation of leave, hybrid work, performance and benefits policies for her business units and is a content owner for the HR documents in the knowledge base.

**Current workflow.** Roughly 40% of her inbound queries are repeat questions already answered in policy: carry-forward limits, probation rules, appraisal timelines, benefits enrolment. Each takes 5–10 minutes, and she often answers slightly differently from a colleague. She also receives sensitive questions (a colleague's salary, rating or disciplinary status) that must be refused and handled properly.

**EKA usage pattern.** Indirect and direct. As a *consumer* she tests the EKA with tricky policy questions and reviews flagged answers. As a *content owner* she checks usage analytics (top questions, unanswered questions and low-confidence topics) to find policy gaps, and updates documents so the EKA stays correct. She expects sensitive requests to be refused and to see them escalated to her.

**Benefits if the EKA succeeds.**

- Repetitive queries fall, freeing time for employee relations, coaching and workforce planning.
- Consistent answers everywhere, with a clear source of truth.
- A feedback loop that shows which policies are confusing or missing, such as the absent sabbatical policy.
- Fewer privacy incidents, because the assistant refuses requests for other people's Restricted data.

**What would break her trust.** The EKA giving authoritative-sounding answers on topics HR has not approved, or leaking personal data.

**Success measure.** Repeat-query volume to HR (K3); count of policy gaps fixed from EKA analytics.

---

## Persona 4: Rahul Mehta – IT Service Desk Lead

**Role and experience.** IT Service Desk Lead with 7 years in IT operations, running a follow-the-sun Level 1 and Level 2 team. Accountable for SLA attainment (P1: 15-minute response, 4-hour resolution; P4: 1 business day) and for ticket cost.

**Current workflow.** About 4,300 tickets a month are how-to or standard requests: VPN setup, password and MFA problems, software requests, lost-device procedure. Many arrive incomplete and need a back-and-forth before work can start. The team's knowledge base exists but is rarely used by employees. P1 and P2 incidents can be delayed by the noise from low-priority tickets.

**EKA usage pattern.** Does not use the EKA as a day-to-day tool, but monitors it. He reviews deflection and escalation reports weekly, tunes the escalation route so that hard cases arrive in ServiceHub with context (question, retrieved sources, confidence) and checks that urgent items (lost laptop, suspected compromise) are told to call extension 5555 immediately and not wait for a ticket.

**Benefits if the EKA succeeds.**

- Fewer P4 tickets, so the team focuses on genuine incidents and meets P1/P2 SLAs more reliably.
- Better tickets: escalations arrive with context, which shortens resolution time.
- Lower cost per employee supported, which feeds IT's cost-reduction target.
- Faster self-service for procedures that have a documented answer (for example, the 2-hour lost-device reporting rule).

**What would break his trust.** Wrong security guidance (for example, an incorrect password rule), or escalations with no context that increase handling time.

**Success measure.** P4 how-to ticket volume and SLA attainment (K3).

---

## Persona 5: Elena Fischer – VP, Employee Experience (executive sponsor)

**Role and experience.** Vice President of Employee Experience with 20 years in HR and operations leadership, jointly accountable with the CIO for employee-facing service levels and cost. Reports to the Executive Committee on employee satisfaction, service cost and risk.

**Current workflow.** She receives monthly service reports showing ticket volume, response times and employee-survey scores, and sees repeated complaints about “finding information”. She has to justify any new technology spend with a business case and is wary of generative AI risks: wrong policy answers, data leakage and runaway cost.

**EKA usage pattern.** Rarely asks the EKA questions herself. She reviews a **monthly dashboard** of the three sponsor KPIs (resolution rate, answer accuracy, ticket reduction) plus cost per question and adoption, and attends the quarterly risk review. She decides whether the pilot expands, pauses or stops.

**Benefits if the EKA succeeds.**

- A measurable reduction in ticket volume and handling cost (about 30% fewer knowledge tickets in six months).
- Improved employee-survey scores for “I can find the information I need”.
- A reusable, governed pattern for AI-assisted knowledge that other functions (Finance, Legal, Sales operations) can adopt.
- Evidence of responsible AI: sources, confidence, escalation, audit logs and cost control.

**What would break her trust.** A single high-profile incorrect or leaked answer; costs rising without matching KPI gains.

**Success measure.** K1, K2 and K3 against target; zero Restricted-data incidents.

---

## Wider stakeholder map

| Stakeholder | Interest | Influence | Engagement approach |
|---|---|---|---|
| Information Security and Privacy Office | Data classification, logging, access control | High (can block) | Early review of ADRs and logging rules; sign-off before pilot; no question text in logs by default |
| Legal and Compliance | Policy accuracy, regulatory risk, disclaimers | High | Approve out-of-scope list (no legal or medical advice) and escalation wording |
| HR, IT and Operations policy owners | Document quality and ownership | High | Named content owner per document, review dates, monthly analytics on gaps |
| Finance and Procurement | Cost and vendor approvals | Medium | Share run-cost model and cost-per-question; align on procurement thresholds (OPS-002) |
| AI platform and engineering team | Stable contract, clear evaluation | High | ADR 0002, golden set and baseline harness; weekly review of the evaluation report |
| Employees at large | Quality, speed, trust | Medium | Pilot with volunteer groups; in-product feedback; transparent “what the assistant can and cannot do” |

## Engagement cadence

Weekly: engineering and content-owner stand-up on evaluation results and content gaps. Monthly: sponsor KPI review. Quarterly: risk and governance review with Information Security, Privacy and Legal. After each milestone: design review with the same panel, using the golden-set results as evidence.
