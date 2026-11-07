---
doc_id: OPS-005
title: Project Delivery Governance and Status Reporting Guide
topic: Operations
owner: Delivery Excellence Office
version: 6.0
effective_date: 2026-01-01
review_date: 2027-01-01
classification: Internal
rights_status: Synthetic content authored for the capstone project; approved for project use
---

# Project Delivery Governance and Status Reporting Guide

## 1. Purpose and scope

This guide sets the governance rules for client projects at Meridian Digital Services ("Meridian"), including application development, application management and modernisation programmes. It defines status reporting, change control, risk escalation, release freezes, quality gates and project closure. It applies to every Delivery Manager, Program Director and project team member.

## 2. Weekly status reporting

2.1 Deadline. The Delivery Manager submits a status report for every active project by 17:00 local time every Thursday.

2.2 RAG status. Each report states an overall Red-Amber-Green status. Green means the project is on track. Amber means that effort or cost variance is up to 10%, or the schedule has slipped by up to 5 working days. Red means that variance is above 10%, the schedule has slipped by more than 5 working days, or a critical risk has no mitigation.

2.3 Persistent Red. A project that is Red for 2 consecutive weeks triggers a Director review and a recovery plan within 5 working days.

2.4 Timesheets. Team members submit timesheets weekly by 12:00 local time on Friday. The target utilisation for billable roles is 80%.

## 3. Change control

Any change to scope, schedule or price in the client contract needs a change request. Approval depends on the cumulative value of changes as a share of the contract value: below 5% is approved by the Delivery Manager; from 5% to 15% by the Program Director; above 15% by the Delivery Head, the client sponsor and Finance. Work on a change must not start until the client has agreed it in writing. Changes must be logged in the project's change register.

## 4. Risk management

The project risk register is reviewed every week. Each risk is scored on probability and impact, each from 1 to 5, and the score is the product of the two. A risk with a score of 15 or more must be escalated to the Program Director within 2 working days of being scored. Every risk has a named owner, a mitigation and a date for the next review. Issues that have already happened are logged separately.

## 5. Release management and the quarter-end freeze

5.1 Standard releases. Production releases follow the client's change-advisory process and Meridian's release checklist. Releases need a rollback plan, test sign-off and a named approver.

5.2 Quarter-end freeze. No production releases or non-emergency changes are made in the last 5 working days of March, June, September and December. The freeze reduces risk at a time when client financial processes are most sensitive.

5.3 Emergency changes. A change that is needed during the freeze to fix a production incident or a security vulnerability is an emergency change. It needs the approval of the Change Advisory Board (CAB) chair or deputy, who must respond within 4 hours of the request. The request must include the reason, the impact and the rollback plan.

5.4 Resourcing during the freeze. Delivery-critical team members who plan annual leave of more than 3 working days that overlaps the freeze need Director approval as well as their line manager's (HR-001). Project managers must name a cover for each delivery-critical role.

## 6. Quality gates

All code must be peer reviewed before it is merged. New code must have automated test coverage of at least 80%. Every release candidate must pass the automated regression suite and security scan. A project can only move to a new phase after the phase-gate checklist is completed and signed by the Delivery Manager.

## 7. Using AI tools in delivery

Teams are encouraged to use approved AI coding and productivity assistants to improve productivity. The rules in IT-004 and IT-006 apply: only the assistants listed in Software Center may be used, Restricted data must never be entered, and client data may be used only when the client contract allows it. A person must review AI-generated code and content before it is merged or sent to a client, and the same quality gates apply. Teams record the use of AI assistance in the project's productivity report.

## 8. Client escalation path

If a client raises a concern that the project team cannot resolve, the issue is escalated in this order: the Delivery Manager, the Program Director, the Account Director and the Delivery Head. Each level has 2 working days to respond. Any threat of contract termination, or any Sev 1 incident (OPS-004), is escalated to the Account Director immediately.

## 9. Project closure

When a project ends, the Delivery Manager completes the closure checklist: final acceptance from the client, release of resources, return of client data and access, closure of purchase orders and final invoicing. A lessons-learned review is held and recorded within 10 working days of closure. Project records are kept for 7 years after closure (IT-006). Client environments and access must be removed within 5 working days.

## 10. Roles

The Delivery Manager is accountable for the day-to-day delivery of a project. The Program Director is accountable for a group of related projects and for their business outcomes. The Delivery Head owns the delivery portfolio. The Delivery Excellence Office maintains this guide, audits compliance twice a year and reports to the Executive Committee.

## 11. Frequently asked questions

When is the weekly status report due? Thursday at 17:00 local time. What makes a project Red? Variance over 10%, a slip of more than 5 working days, or an unmitigated critical risk. When is the quarter-end freeze? The last 5 working days of March, June, September and December. Who can approve a change during the freeze? The CAB chair or deputy, within 4 hours.
