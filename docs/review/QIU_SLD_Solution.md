# QIU Student Life Division System
## Proposed solution and workflows

For SLD and ICT review | 9 October 2026

### Purpose
One university website to manage clubs, events, reports and club finances. Students complete guided online forms; advisors and SLD review the same records. Exports follow the university's original form layouts.

| Current problem | Solution |
|---|---|
| Inconsistent forms and missing information | Guided fields and original-format exports |
| Documents scattered across emails | One record with status, attachments and review history |
| Difficult tracking of members and money | Membership/payment reconciliation and approved financial records |
| Manual follow-up | Dashboard, missing-document checklist and notifications |

### Users and access
Students browse clubs and upcoming activities. Committee manages assigned clubs/events. Advisors review assigned clubs. SLD oversees all clubs and controls operating settings. Superadmin manages authorised staff and roles.

One person may hold different positions in multiple clubs. Access follows the selected club or event. Public browsing does not grant access to private forms, receipts or bank details.

### Rules across all forms
Sign in using verified **@qiu.edu.my Google accounts**. Refresh available name, picture, student ID, programme or staff designation/department at login. Fill relevant identity and club information automatically.

Drafts save automatically. Mark required fields with red asterisks and complete them before moving forward. Show progress, status and the next action. Require a second confirmation before a final submission to SLD.

Signatures capture the correct name, position and server date in their respective sections. Recorded dates cannot be edited. Returned forms show correction reasons; corrected versions need renewed signatures.

<!-- pagebreak -->
# 1 Clubs and reports

### Club registration
SLD assigns the proposed President and advisor, granting one registration opportunity. The President enters the club biography, logo and committee. President, Vice President, Secretary and Treasurer are mandatory; additional positions may be added.

**Workflow:** SLD authorises → President completes form → advisor reviews/signs → confirmed send to SLD → SLD opens and locks the submitted application → approve or return.

Pending applications remain editable until SLD first opens them. Approval activates the club profile/workspace. Returning an application explains the required corrections.

### Profiles and membership
Club profiles show the logo, biography, hierarchy, upcoming activities and annual history. Personal profiles show each student's club/event positions.

Students join through a club QR code. Record membership period, payment method and evidence. Committee records cash; online payments retain proof. Reconcile member numbers, collections and deposits in the semester membership-drive report.

### Weekly activity and AGM
| Report | Main information | Signatures | Photos |
|---|---|---|---|
| Weekly | Sports attendance or non-sports minutes/activity | President → Secretary → Advisor → SLD | Minimum 2 |
| Annual AGM | AGM summary, membership list/count, outgoing achievements and incoming committee | President → Secretary → Advisor → SLD | Minimum 1 |

SLD tracks submitted and missing reports by club and period. Every form has PDF export with signatures and a clear review log.

### Committee handover
SLD acknowledges the approved AGM and starts handover. Incoming members receive training access with pending titles; outgoing officers retain their titles during the overlap. After **7 days by default**, incoming titles activate and outgoing club access ends. SLD controls the overlap period. Preserve previous committee and activity history.

<!-- pagebreak -->
# 2 Events and documents

### Guided proposal
Include event details, venue, planned start/end times, automatically calculated duration, at least two objectives, selected SDGs, programme and participants. Choose collaborators from registered clubs or enter another organisation. Select committee members from university directory records and assign positions.

Include budget, income, expenses and supporting quotations/documents. ICT, maintenance and logistics requests can be marked **Not applicable** when not needed.

Submit at least **14 days before the event by default**. SLD controls the number of days and may grant a reasoned short-notice exception to a selected club.

### Approval
**Draft → one President/Vice President preparer signs → advisor reviews/signs → double-confirm send → SLD approves or returns with a reason.**

Each submitted version has one preparer. Signatures remain in the correct student, advisor and SLD sections. Corrections require renewed review. The budget should break even; **SLD may approve a deficit with a recorded reason**. Proposal approval does not change the actual club balance.

### Event completion
Approval adds the event to the system calendar and assigned organisers' dashboards. Provide a controlled event folder. Outdoor events require applicable participant indemnity forms before participation.

After the event, submit the completion report, attendance, actual finances, receipts, survey results, post-mortem and **at least two different photos**. SLD reviews completed records and missing items.

SLD downloads photos as a ZIP named with activity/event, club, date and submitting person. Keep each event's proposal, receipts, photos and reports together.

### Exports
Website entries populate the original university form layout. Every application/form has PDF export; provide Word and Excel where appropriate. SLD manages approved template updates, preserving historical signed versions.

<!-- pagebreak -->
# 3 Finances and withdrawals

### Financial records
Use one row per income/expense item with description, quantity, amount and receipt. Save automatically and compare actual figures against the approved proposal budget.

**Committee records actual transactions → uploads receipts → confirms submission → SLD reviews → approved transactions update the balance.**

Pending records and budgets do not alter balances. Keep corrections traceable and prevent duplicate posting. Show club balance, monthly/yearly charts and expandable event transaction details. Activity performance is separate from financial totals.

### Withdrawal workflow
1. Treasurer prepares and signs the request.
2. President reviews and signs.
3. Advisor signs and confirms the send to SLD.
4. SLD reviews/signs; request waits for Finance.
5. SLD uploads Finance's signed approval document.
6. SLD confirms all approvals; status becomes Waiting for transfer.
7. Treasurer uploads proof of funds received and signs receipt.
8. SLD acknowledges receipt and closes the request.

Transfer is expected within **14 days by default**, controlled by SLD. Notify linked committee/advisors when status changes. Keep transfer evidence separate from expenses to avoid counting money twice.

### Annual archive
After AGM approval and acknowledgement, SLD downloads an organised archive containing committee/AGM, weekly reports, events, financial records and withdrawals. Each event contains its proposal, receipts, photos and reports.

Students may view published annual hierarchy/activity history. Full archives, bank details and private financial evidence remain restricted.

<!-- pagebreak -->
# 4 Dashboards and ICT review

### Follow-up and communication
| User | Main dashboard |
|---|---|
| Student/committee | Assigned clubs/events, tasks and signatures |
| Advisor | Assigned club progress and awaiting reviews |
| SLD | All clubs, approvals, missing reports, member counts and financial follow-up |

Filters apply automatically. Group history within the related club/proposal/report. Notifications link to permitted tasks. The SLD calendar and annual activity grid show meetings, weekly activities, AGMs and events, with monthly/yearly views. Approved events can link to Google Calendar.

The lower-right assistant opens compact chat or a full page, with deletable personal history. Students ask about public upcoming events; committee/advisors ask about assigned records; SLD asks across clubs. Answers link to relevant permitted records.

### ICT solution requirements
| Component | Purpose |
|---|---|
| Python backend | Checks access, workflow rules and saves |
| MySQL database | Stores records, assignments and history |
| Browser website | Forms, dashboards and exports |
| QIU Google access | Verified login and available directory details |
| Document conversion | Original-layout PDF output |
| Private file storage | Protected receipts, signatures and photos |

ICT must confirm QIU's Exabytes server supports Python, MySQL, HTTPS, PDF conversion, sufficient storage and Google integrations. Require server-synchronised time, protected credentials, restricted downloads, backups, recovery and a support owner. Confirm university-data permissions before connecting an external AI service.

### Review decisions
SLD agrees deadlines, payment handling, signing responsibilities, handover/transfer periods, exceptions and retention. ICT confirms hosting, identity access, security, exports, recovery and workload.

Start with five clubs, then expand to 30+ clubs, around 2,000 students, 50+ advisors and 10 SLD staff after acceptance. This document describes the proposed solution, rather than development progress.
