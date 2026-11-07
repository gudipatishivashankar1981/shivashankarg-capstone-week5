---
doc_id: OPS-004
title: Business Continuity and Incident Escalation Procedure
topic: Operations
owner: Business Resilience Office
version: 2.8
effective_date: 2026-01-01
review_date: 2027-01-01
classification: Internal
rights_status: Synthetic content authored for the capstone project; approved for project use
---

# Business Continuity and Incident Escalation Procedure

## 1. Purpose and scope

This procedure describes how Meridian Digital Services ("Meridian") classifies business incidents, who must be told and how quickly, how we keep critical services running through a disruption, and how we learn from incidents. It covers technology outages, security and data incidents, loss of a site, and safety events. IT-specific incident handling is described in IT-005; this procedure sits above it and applies when business operations or clients are affected.

## 2. Business incident severity levels

Sev 1 - Critical. A full outage of a client-facing service, or an outage affecting more than one client; a serious safety incident; a major data breach; or the closure of a Meridian site.

Sev 2 - Major. Significant degradation of a service for a single client, or the outage of an internal system that is critical to delivery or payroll.

Sev 3 - Minor. Limited impact, where a workaround exists and no client commitments are at risk.

The person who first notices an incident should classify it at the higher level if unsure. The Incident Commander can lower the severity later.

## 3. Escalation times

For a Sev 1 incident, the Incident Commander must be notified within 15 minutes of detection, and the executive on-call must be informed within 30 minutes. A bridge call is opened and updates are shared every 30 minutes.

For a Sev 2 incident, the Director responsible for the affected service must be notified within 1 hour. Updates are shared every 2 hours.

For a Sev 3 incident, the incident is logged and the owning manager is informed by the end of the next business day.

An IT P1 incident (IT-005) that affects a client's service is automatically a Sev 1 business incident. A suspected data breach involving Confidential or Restricted data is reported to Security Operations within 2 hours (IT-006), and the Incident Commander decides on the severity.

## 4. Incident roles

An incident is run by an Incident Commander, who makes decisions and sets priorities. A Technical Lead directs the investigation and the fix. A Communications Lead sends the updates to employees, clients and executives. A Scribe records the timeline. The Incident Commander for Sev 1 and Sev 2 incidents is drawn from the on-call rota published on the intranet.

## 5. Client communication

When a Sev 1 incident affects a client, the Account Director must tell the client within 1 hour of the incident being declared, unless the contract requires a shorter time. Communication with clients goes only through the Account Director or a person they nominate. Other employees must not contact clients or post about the incident on external channels. Clients receive updates at the same cadence as internal updates unless they have agreed otherwise.

## 6. Post-incident reviews

A blameless post-incident review is held within 5 working days of every Sev 1 and Sev 2 incident. A written root-cause analysis (RCA) is published within 10 working days, with owners and dates for the corrective actions. The Business Resilience Office tracks actions until closure and reports the trends to the Executive Committee quarterly.

## 7. Business continuity planning

7.1 Recovery objectives. Critical systems (Tier 1) have a recovery time objective (RTO) of 4 hours and a recovery point objective (RPO) of 15 minutes. Important systems (Tier 2) have an RTO of 24 hours and an RPO of 4 hours. Other systems (Tier 3) have an RTO of 72 hours and an RPO of 24 hours.

7.2 Team plans. Every team maintains a continuity plan and a call tree, which lists who must be reached and how. Managers review them every 6 months and whenever team members change.

7.3 Testing. The Business Resilience Office runs a continuity exercise twice a year, with at least one test of a full site closure and one of a major technology outage.

## 8. Site closures and emergencies

8.1 Decision. The Facilities team and site leadership decide whether to close an office. The decision is communicated through the Emergency Notification System by SMS, email and mobile app, and by a banner on the intranet.

8.2 What employees do. In a site closure, employees work from home using their managed laptop and the VPN (IT-002), unless their role cannot be done remotely. Employees must keep their contact details on PeopleHub up to date so they receive alerts.

8.3 Evacuation. In an evacuation, employees follow the fire wardens to the assembly point shown on the floor plan and report to their warden. Nobody may re-enter a building until the all-clear is given.

8.4 Injuries. A workplace injury or near-miss must be reported to Facilities within 24 hours.

## 9. Reporting a possible incident

Employees who notice a possible incident should report it straight away, even if they are not sure. For technology issues, call the IT Helpdesk on extension 5555. For safety issues, call the security desk of the site. Reporting in good faith is never penalised.

## 10. Frequently asked questions

Who must be told within 15 minutes of a Sev 1? The Incident Commander. When must the client be told? Within 1 hour, by the Account Director. When is the post-incident review held? Within 5 working days. What is the recovery time for a Tier 1 system? 4 hours.
