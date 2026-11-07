---
doc_id: IT-001
title: Password, MFA and Access Management Standard
topic: IT
owner: Information Security Team
version: 6.1
effective_date: 2026-02-01
review_date: 2027-02-01
classification: Internal
rights_status: Synthetic content authored for the capstone project; approved for project use
---

# Password, MFA and Access Management Standard

## 1. Purpose and scope

This standard defines how employees and contractors of Meridian Digital Services ("Meridian") authenticate to Meridian systems and how access to those systems is requested, approved, reviewed and removed. It applies to every user account, including accounts used on client-owned systems when Meridian is the identity provider. The standard follows current industry guidance that favours long passwords and strong multi-factor authentication over frequent forced password changes.

## 2. Password requirements

2.1 Length. Passwords must be at least 14 characters long. Passphrases made of several unrelated words are encouraged because they are easier to remember and harder to guess.

2.2 No periodic expiry. Standard user passwords do not expire on a schedule. A password must be changed immediately if it is known or suspected to be compromised, and when the Security team tells the user to do so. Privileged and administrator accounts are the exception: their credentials must be rotated every 90 days.

2.3 Reuse. Passwords used for Meridian accounts must not be reused on personal or third-party services. The system blocks passwords found in public breach lists and passwords that contain the user's name or Meridian.

2.4 Storage. Employees must store passwords only in the corporate password manager. Writing passwords on paper or storing them in files, chat or email is not permitted.

2.5 Sharing. Passwords must never be shared, including with managers, colleagues or the IT Helpdesk. The Helpdesk will never ask for a password. Shared or generic accounts are not permitted; where a team needs shared access, the system owner must set up named access or a vaulted credential.

## 3. Multi-factor authentication

Multi-factor authentication (MFA) is mandatory for all users, on all Meridian systems, from every location. Users must enrol in the approved authenticator app on their first day. Users with privileged access must use a FIDO2 hardware security key. Text-message (SMS) codes are not accepted as an MFA method. Users who receive an MFA prompt they did not trigger must deny it and report it through the Report Phish button or by calling the Helpdesk, because it may indicate that their password has been stolen.

## 4. Account lockout and self-service reset

An account is locked for 30 minutes after 5 consecutive failed sign-in attempts. Users who forget their password can reset it at any time through the Self-Service Portal at selfservice.meridian.example, provided they have enrolled in MFA. If a user has lost the device that holds their MFA authenticator, they must contact the IT Helpdesk. The Helpdesk will verify the user's identity and ask the user's manager to confirm the request. It will then issue a Temporary Access Pass that is valid for 4 hours and lets the user enrol a new authenticator.

## 5. Requesting access

5.1 Standard access. Access to applications and data is requested through ServiceHub under Access Requests. Each request needs the approval of the requester's line manager and of the system owner. The target time to fulfil an approved standard request is 3 working days.

5.2 Least privilege. Access is granted on a need-to-know basis and only at the level the role requires. Requests for access to Confidential or Restricted data (see IT-006) must state the business reason.

5.3 Privileged access. Administrator and production access needs an additional approval from the Information Security Team. Privileged access is time-bound and is granted for a maximum of 30 days at a time. Extending it requires a new request.

5.4 Client systems. Access to client environments follows the client's onboarding process as well as this standard. Delivery Managers must confirm that the user has completed the mandatory training described in OPS-003 before requesting production access.

## 6. Access reviews

System owners review standard access to their systems every year and privileged access every quarter. Access that is no longer needed must be removed within 5 working days of the review. Dormant accounts that have not signed in for 90 days are disabled automatically.

## 7. Movers and leavers

When an employee changes role, the new manager must request any additional access, and the old manager must request removal of access that is no longer needed. When an employee leaves Meridian, HR notifies IT, and all of their access is disabled by the end of their last working day. Managers must complete the offboarding checklist in OPS-003 so that mailbox, files and devices are handled correctly.

## 8. Reporting problems

Users must report suspected account compromise, lost authenticators and suspicious sign-in prompts to the IT Helpdesk immediately. A suspected compromise is treated as a P1 incident under IT-005. Phishing emails should be reported with the Report Phish button in the email client; reporting a phishing email never leads to disciplinary action.

## 9. Exceptions

Exceptions to this standard are rare. They require a written request to the Information Security Team through ServiceHub, a documented business reason, a compensating control and the approval of the Director responsible for the system. Exceptions are time-limited to a maximum of 6 months and are reviewed before renewal.

## 10. Frequently asked questions

How often do I have to change my password? Not on a schedule, unless you hold privileged access, in which case every 90 days; change it at once if you think it has been exposed. How long should it be? At least 14 characters. I forgot my password; what do I do? Use the Self-Service Portal. I lost my phone with my authenticator on it; what do I do? Call the Helpdesk for a Temporary Access Pass.
