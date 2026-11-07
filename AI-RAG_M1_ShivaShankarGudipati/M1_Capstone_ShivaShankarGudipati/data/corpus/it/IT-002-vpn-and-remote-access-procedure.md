---
doc_id: IT-002
title: VPN and Remote Access Procedure
topic: IT
owner: Network and Security Operations
version: 3.4
effective_date: 2026-02-01
review_date: 2027-02-01
classification: Internal
rights_status: Synthetic content authored for the capstone project; approved for project use
---

# VPN and Remote Access Procedure

## 1. Purpose and scope

This procedure explains when and how employees connect to the Meridian corporate network from outside a Meridian office. It covers the installation and use of the SecureLink VPN client, rules for public networks and travel, and basic troubleshooting. It applies to employees and contractors who use a Meridian-managed laptop.

## 2. When the VPN is required

2.1 Systems that need the VPN. The VPN must be active whenever a user accesses internal systems from outside a Meridian office. These systems include source-code repositories, internal ticketing tools, file shares, test environments and client environments reached through Meridian's network.

2.2 Systems that do not. Cloud applications that sign in through single sign-on, such as email, chat, PeopleHub and ServiceHub, can be used without the VPN. Users should still connect the VPN when working on Confidential or Restricted data (see IT-006).

2.3 Public networks. Employees may use public Wi-Fi in cafés, airports and hotels only while the VPN is active. Users must not connect to open networks that ask them to install a certificate or profile.

## 3. Installing the client

SecureLink is pre-installed on every Meridian-managed laptop. If it is missing, users can install it from Software Center without raising a request. Personal laptops and unmanaged devices are not allowed to connect to the VPN (see IT-003). Contractors using their own equipment must use the virtual desktop service arranged by their Delivery Manager.

## 4. Connecting step by step

1. Open SecureLink from the system tray or the Applications folder.
2. Select Connect. The client picks the nearest gateway automatically. Gateways are located in Mumbai, London and Virginia.
3. Sign in with your Meridian single sign-on credentials.
4. Approve the multi-factor authentication prompt in the authenticator app (see IT-001).
5. Wait until the status changes to Connected and the shield icon turns green.

The VPN uses a full tunnel, which means all traffic from the laptop is routed through Meridian's security controls while the connection is active. Sessions disconnect automatically after 60 minutes of inactivity and after a maximum of 12 hours, and users must sign in again. Users should disconnect when they have finished working with internal systems.

## 5. Travel and restricted countries

VPN access is blocked by default from countries on the restricted-travel list published by Information Security. Employees who must travel to those countries on business have to request a loaner laptop at least 10 working days before they leave, as described in IT-003. Employees must not take their usual Meridian laptop to those countries. Employees working from another country under Work from Anywhere (HR-003) must connect the VPN and must check that the country is not on the restricted list before they travel.

## 6. Troubleshooting

6.1 Authentication failed. Check that the date and time on the laptop are set automatically, that the authenticator app shows a valid code, and that the account is not locked. An account is locked for 30 minutes after 5 failed attempts (IT-001).

6.2 Gateway unreachable. Switch to a different network, for example a mobile hotspot. Some hotels and airports block the ports that SecureLink uses. Select a different gateway manually from the drop-down list in the client.

6.3 Slow connection. Close applications that stream video or large files, move closer to the router or use a wired connection, and reconnect to a different gateway.

6.4 Connected but internal sites do not load. Disconnect, restart the laptop and reconnect. Clear the browser cache. Check the ServiceHub status page to see whether the system is affected by a known incident.

6.5 Raising a ticket. If the problem is not solved after about 15 minutes of troubleshooting, raise a ticket in ServiceHub. A single user who cannot connect is normally logged as P3 with a target resolution of 3 business days. Users who cannot work at all should call the Helpdesk so the ticket can be prioritised (see IT-005).

## 7. Acceptable use

The VPN is provided for Meridian business. Users must not use it to access content that breaks the Code of Conduct (HR-002), to bypass geographic restrictions on streaming services, or to give other people access to Meridian systems. All VPN sessions are logged, and logs are retained for 12 months for security investigations.

## 8. Security incidents

Anyone who believes their laptop or credentials were compromised while connected to the VPN must disconnect, and then report it to the IT Helpdesk immediately. If a laptop is lost or stolen, it must be reported within 2 hours of discovery (IT-003). Security Operations may revoke a user's VPN certificate remotely at any time.

## 9. Frequently asked questions

Can I use the VPN on my personal laptop? No. Do I need the VPN to read my email? No, but you do to reach internal code repositories. Why was my VPN disconnected after a few hours? Sessions end after 12 hours or after 60 minutes of inactivity.
