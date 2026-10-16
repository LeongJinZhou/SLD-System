# QIU Student Life Division System
## Project review, complete workflows and delivery plan

**Review date: 15 October 2026 | Audience: project owner, SLD and ICT**

### 1. Introduction and conclusion
The project is a university website for managing clubs, events, committee responsibilities, reports and club funds. Its main purpose is to replace inconsistent emailed documents with guided forms, shared review stages, reliable records and exports that follow QIU's original layouts.

The current source identifies itself as **API 1.7**. A substantial local operational prototype exists. It is **not a complete official university service**: important modules are missing, real university connections are unverified, and operational acceptance is outstanding.

### Is it spaghetti?
**The concern is justified, but the whole application is not an unstructured tangle.** There are separate modules for authentication, storage, reports, finance, evidence, withdrawals, profiles, notifications and the assistant. Server-side access checks, version checks, signed snapshots and regression tests provide useful foundations.

However, the main frontend has grown into one large, densely written file. Backend routing and core business rules remain concentrated in a central application object. Modules depend on helpers from that central file. Status documents also contradict one another. These make change impact difficult to follow and create a real maintenance risk.

**Recommended direction:** stabilise the existing system, establish one reliable status baseline, then separate the largest responsibilities incrementally. The evidence does not justify discarding everything or claiming the present structure is ready for unrestricted growth.

### How to read the status
| Label | Meaning |
|---|---|
| Implemented locally | A working code path exists; local evidence is identified. It does not mean university acceptance. |
| Partial | Part of the requirement exists, but a material part is missing or inconsistent. |
| Not implemented | No complete operational module was found for the requested outcome. |
| Unverified externally | Code/configuration may exist, but real QIU/Exabytes/provider behaviour has not been established. |

This is a dated source and evidence audit, not a promise that every screen is bug-free. Application code was not refactored or deployed for this review. The earlier five-page solution document remains a separate stakeholder overview.

<!-- pagebreak -->
# 2. Overall solution and responsibilities

### Intended scale
Start with five clubs. The wider planning population is more than 30 clubs, about 2,000 students, more than 50 advisors and about 10 SLD staff. These numbers are requirements for planning and testing, not measured capacity results.

| Person | Responsibility | Access boundary |
|---|---|---|
| General student | View own profile, published clubs, hierarchy and upcoming activities | No private accounts, evidence or approval records |
| Club committee | Prepare assigned club/event records and supply evidence | Assigned club only; signing also depends on position |
| Event committee | Work on its assigned event and evidence | Does not receive the club's unrelated accounts |
| President/Vice President | One eligible event-proposal preparation signature | One preparer per submitted version |
| President/Secretary | Required weekly/AGM signing stages | Current entitled office holders |
| Treasurer | Withdrawal submission and acknowledgement of funds received | Current entitled Treasurer |
| Advisor | Review assigned clubs and sign assigned stages | Cannot use a directory title to access unrelated clubs |
| SLD | Manage all club follow-up, approvals, policies and controlled exceptions | Still follows signing/version rules |
| Superadmin | Intended staff/role administration | Full management module remains missing |

A person may hold different positions in several clubs. Pending incoming committee members may learn and draft during handover, but do not receive the current officer's signing authority merely from a displayed pending title.

### Complete business journey
1. University/ICT configures verified identity, hosting, storage and authorised SLD accounts.
2. SLD authorises a President and advisor for one club registration.
3. Registration is prepared, reviewed and approved; the club workspace becomes active.
4. Committee maintains membership, prepares events and submits weekly/annual reports.
5. Events pass proposal review, take place, then acquire evidence and actual accounts.
6. SLD approves actual financial records; only these approvals affect balances.
7. Annual AGM approval leads to controlled committee handover and annual archives.
8. Dashboards, notifications, calendar, history and the assistant support follow-up throughout.

Steps involving membership collection, indemnity collection and automatic Drive provisioning are intended future flows, not completed modules.

<!-- pagebreak -->
# 3. What is done: operational modules

| Area | Current status | What exists / important boundary |
|---|---|---|
| One-time club registration | Implemented locally | SLD grant bound to President/advisor; consumed on creation |
| Club approval | Implemented locally | Advisor review, SLD first-open lock, approval and reasoned return |
| Club roles and multiple positions | Implemented locally | Current assignments checked separately for each club/event |
| Personal and club profiles | Implemented locally | Distinct self/public views, logos, safe hierarchy and assignments |
| Proposal form | Implemented locally | Autosave, required-step gates, objectives, SDGs, collaboration, committee and conditional support |
| Planned event schedule | Implemented locally | Start/end validation and derived duration |
| Lead-time policy | Implemented locally | Default 14 days, SLD settings and reasoned club exceptions |
| Proposal signing | Implemented locally | One President/VP preparer, advisor, SLD; version-bound identity/date |
| Deficit exception | Implemented locally | SLD must record reason; budget approval never posts money |
| Weekly and AGM reports | Implemented locally | Separate forms and four ordered signatures; annual/week trackers |
| Handover | Implemented locally | Explicit SLD start; default 7-day overlap; server-time access expiry |
| Photos and photo ZIPs | Implemented locally | Minimum 2 event/weekly and 1 AGM, validated distinct images, SLD ZIP |
| Event completion report | Implemented locally | After-event summary/evidence, submission, SLD review/return, export |
| Actual event accounts | Implemented locally | Item evidence, budget variance, SLD review and once-only ledger posting |
| Withdrawals | Partial | Ordered electronic stages and Finance/fund files exist; clean-install PDF dependency defect and settlement gaps remain |
| Annual full-file archive | Partial | Organised private ZIP exists; withdrawal form PDF and wider missing modules are not fully covered |

**Important:** these labels describe present functionality, not the result of a complete new test run of every module on 15 October. Fresh checks and historical checks are separated in section 16.

Local completion has genuine substance: records have revision checks, signing stages bind submitted versions, and money posting is controlled on the server. Those protections should be retained during cleanup.

<!-- pagebreak -->
# 4. What is partial or not done

| Area | Current status | Remaining outcome |
|---|---|---|
| QIU Google sign-in | Unverified externally | University-owned client, real users, approved redirects/domain and session acceptance |
| Directory and profile photos | Unverified externally | Real field mapping, accessible contacts/photos and completeness checks |
| QR membership and payment collection | Not implemented | Joining, duplicate/unpaid cases, cash/bank verification and reconciliation |
| Semester membership report | Not implemented | Authoritative member list/count and reconciled collections |
| Outdoor indemnity | Not implemented | Participant forms, consent/emergency details, access and completeness controls |
| Surveys/post-mortem collection | Partial | Completion summary/photos exist; dedicated supporting-document workflow is incomplete |
| Proposal cost attachments | Partial | Budget tables exist; full proposal-stage quotation/supporting-file collection is missing |
| Google Drive folders | Not implemented | Automatic university-owned event folder and controlled permissions |
| Calendar | Partial | Internal entries, Google add links and ICS export exist; live synchronization is missing |
| Notifications | Implemented locally | In-app notices/read state; email/push delivery is not connected |
| Assistant | Partial | Scoped local retrieval/history/links exist; live generated-answer quality and provider approval unverified |
| Template administration | Not implemented | SLD replacement upload, reviewed mapping, activation/version management |
| Superadmin/staff lifecycle | Partial | SLD allowlist/assignment controls exist; full audited staff/role CRUD is missing |
| Financial adjustments | Not implemented | Controlled refunds, corrections, reconciliation and withdrawal settlement linkage |
| Universal signature consistency | Partial | Proposal/report/withdrawal identity is canonical; registration still trusts a submitted display name |
| Production operation | Unverified externally | Exabytes deployment, HTTPS, monitoring, capacity, backup/restore and support |
| Browser acceptance | Not verified | Real desktop/mobile scrolling, keyboard, canvas signing and recovery |
| Documentation/rebuild reliability | Partial | Useful references exist, but version/status statements and packaging checks have drifted |

### No reliable overall completion percentage
Counting screens would hide missing operational work. Membership is an entire business process, while a label change is small. Use the module status and acceptance gates in this report instead of an invented percentage.

### Policy decisions still needed
SLD/Finance/ICT must settle cash custody, payment verification/refunds, withdrawal settlement, reporting obligations/exemptions, indemnity coverage/deadlines, electronic-signature acceptance, record retention and operational ownership. Existing defaults do not settle all these policies.

<!-- pagebreak -->
# 5. Login, profile and registration workflows

### W01. Login and identity
1. User selects QIU Google sign-in.
2. Server verifies the identity, university domain and login response.
3. Capture available name, email, picture and directory fields. Students use student ID/programme; staff use designation/department. Do not invent missing values.
4. Resolve current club/event assignments and explicitly authorised SLD access.
5. Open the correct dashboard and personal profile. Refresh trusted profile information on later logins.

**Status:** code exists; actual university sign-in/directory access remains unverified. Preview identities are fictional. A Google job title alone does not grant SLD privileges. Preserve the full QIU student ID; its final four digits are not a safe unique identity key.

### W02. Club registration
1. SLD creates a registration authorisation identifying club, President, advisor and period.
2. Assigned President creates the application, consuming that one-time permission.
3. Enter club biography/logo and four mandatory officers; add other positions if needed. Draft changes autosave.
4. Submit the version for advisor review and signature.
5. Advisor confirms the final send to SLD.
6. While awaiting SLD's first review opening, permitted edits require renewed advisor review. SLD opening deliberately locks the submitted application.
7. SLD approves or returns it with a reason. Approval opens the club workspace; return reopens correction and renewed review.

**States:** draft → pending advisor → pending SLD → reviewing SLD → approved, or returned → corrected/resubmitted.

**Current defect:** registration review stores a client-entered signing display name beside the trusted actor email. This can mislabel who appears in exports. It does not demonstrate a role bypass, but it needs correction before official use.

### W03. Drafts, errors and returns
Autosave may retain incomplete drafts; forward form navigation validates required sections. An old revision must produce a conflict rather than overwrite another editor. Upload failures remain visible and must not be described as saved. Session expiry should lead to sign-in/recovery of retained work.

Every returned record needs the reason, returning role, relevant time and a clear next action. Corrected signed forms start a new review version; previous signatures remain historical. Two-step SLD submission confirmation is a user check, not an extra approval role.

<!-- pagebreak -->
# 6. Event proposal workflow

### W04. Draft to approved event
1. A committee member chooses an approved club and opens a proposal draft. Assigned event organisers may edit within their event permissions; they do not gain club-wide access or preparer signing authority.
2. Complete event title, purpose, venue, planned start/end, programme, participants and at least two objectives. Duration is calculated from the schedule.
3. Select SDGs from the list. Select collaborating registered clubs, or choose Other and enter the organisation. Collaboration does not grant access.
4. Select directory people for the event committee and assign positions. Indicate whether ICT/maintenance/logistics are needed; irrelevant sections become Not applicable.
5. Enter proposed income/expenses and supporting reasons. Full proposal-stage quotation attachment handling remains a gap.
6. Server checks the configured lead time: default 14 days before event start. SLD can change the day policy or issue a reasoned, expiring club exception. An exception is not event approval.
7. One eligible President or Vice President signs Prepared by. The submitted content/version is frozen.
8. Assigned advisor reviews and signs, then explicitly confirms the final send to SLD. Return requires a correction reason.
9. SLD reviews and signs. If expenses exceed income, SLD must record a deficit approval reason. SLD may return instead.
10. Final approval creates one internal calendar record. Approved proposal information becomes available according to each user's access.

**States:** draft → pending advisor → pending SLD → approved; a returned version re-enters preparation and the signature chain.

### Identity and document rules
Prepared by, advisor Reviewed by and SLD Reviewed by occupy separate cells in the retained university form. Names/positions/departments come from trusted context; signing dates come from the server and cannot be edited. Printed names of other university officials are not proof that they approved the record.

One submitted proposal cannot acquire two preparer signatures. Revisions, digests and signature records connect approvals to the correct content. A digest is a file/content fingerprint, not independent proof of legal signature acceptance.

### What approval does not do
It does not post actual income/expenses, complete indemnity collection, create a working Drive folder automatically, prove the event took place or guarantee Google Calendar synchronization. Each has a separate workflow or remaining delivery requirement.

<!-- pagebreak -->
# 7. Weekly reports, AGM and handover

### W05. Weekly activity report
1. Committee selects the club and actual activity date/type.
2. Sports reports capture attendance; non-sports reports capture meeting/activity minutes and actions.
3. Add at least two different activity photos. Photos belong to that exact report.
4. President signs/submits → Secretary reviews/signs → advisor reviews/signs and confirms send to SLD → SLD reviews/signs.
5. Any allowed return requires a reason; correction produces a new signed review chain.

**States:** draft → pending secretary → pending advisor → pending SLD → approved, or returned.

Completed activities cannot be reported as future completed work. An entered future next meeting is planning information, not evidence that it happened. SLD's weekly tracker reports recorded evidence; no report is not automatically proof of absence or a policy-defined overdue obligation.

### W06. Annual AGM report
1. Use the separate AGM workspace and reporting year; actual meeting date is recorded separately.
2. Include AGM summary, membership numbers/list, outgoing achievements and incoming committee, including the four mandatory officers.
3. Add at least one photo.
4. Complete President → Secretary → Advisor → SLD signatures with final SLD confirmation.
5. SLD follows the annual tracker for Missing, Draft, Returned, Pending stages and Approved.

One AGM record per club/reporting year is maintained. A stale draft committee snapshot needs an explicit guarded refresh. Approved annual reporting does not silently replace officer access. Membership-list collection still lacks its complete membership source module.

### W07. Committee handover
1. After AGM approval, SLD explicitly acknowledges and starts handover using current report/club versions.
2. Record outgoing/incoming rosters and server start/end times. Default overlap is 7 days; SLD may set another permitted value.
3. Outgoing officers retain current titles. Incoming members receive pending access for training/drafting, without current officer signing authority.
4. At the exact server deadline, access checks use the incoming roster and titles; outgoing club access ends. Independent event assignments remain separately evaluated.
5. Preserve the annual hierarchy and published activity history.

This access switch is calculated during server record reads rather than relying on a daily scheduled job. That protects deadline enforcement but also couples club reads to handover policy. Outstanding Secretary obligations are guarded before starting handover.

<!-- pagebreak -->
# 8. Event evidence and actual financial accounts

### W08. Completion and photos
1. Approved event reaches its recorded end time.
2. Assigned organisers prepare the post-event summary and attach at least two different photos.
3. Autosave the completion draft; confirm the final send to SLD.
4. SLD reviews and signs approval, or returns with a correction reason.
5. The activity can be identified as evidenced completion rather than merely a past scheduled event.

Photos are private uploads with size/type/readability and duplicate checks. Event/weekly minimum is 2; AGM minimum is 1. Current photo controls limit file size/count; they are not a malware-scanning service. SLD ZIP filenames identify activity, club, date and submitting person.

**Gap:** summary/photos are implemented, but a complete attendance/survey/post-mortem supporting-file collection and follow-up obligation model is not delivered. Completion and actual accounts are distinct reviews; there is not yet one comprehensive event-closure gate tying every obligation together.

### W09. Actual accounts and balance
1. Organisers open accounts for an approved event and enter income/expense rows.
2. Link supporting receipts to the correct row; explain differences from the proposed budget.
3. Changes and receipt associations autosave. Pending attachment operations must finish before sending.
4. Confirm submission to SLD. A return reopens correction; pending/approved reports cannot be casually edited.
5. SLD approves only after the event ends and required completion-photo evidence exists.
6. The approval and ledger posting commit together, once. Concurrent/stale approval must not post a second time.

**Balance:** approved opening balance + approved actual income − approved actual expenses.

Proposed budgets, unreviewed receipts and pending withdrawals do not affect this balance. Monetary posting uses integer cents to avoid rounding drift. Club committees/advisors see permitted club finances; event-only organisers see their event accounts. SLD can prepare and approve actual accounts; the code does not require two independent finance officers. Finance must agree whether that separation is required.

**Missing financial operations:** controlled corrections/refunds, full cash/deposit reconciliation, settlement of withdrawal advances against event expenditure, and approved handling of cancelled/zero-activity events. Finance must agree these rules before official financial reliance.

A withdrawal transfer is not itself an expense. When settlement is added, it must reconcile cash movement with actual expenditure without counting both as spending.

<!-- pagebreak -->
# 9. Withdrawal workflow

### W10. Request to acknowledged receipt
| Step | Responsible person | Resulting state |
|---|---|---|
| Prepare items, recipients, amounts and bank information | Club committee; Treasurer submits/signs | pending_president |
| Review and sign the submitted version | President | pending_advisor |
| Review/sign and confirm final send to SLD | Advisor | pending_sld |
| Review and sign | SLD | pending_finance |
| Upload Finance's signed approval document | SLD | pending_all_approve |
| Confirm complete approvals and sign | SLD | waiting_transfer |
| Upload bank-in/fund receipt and sign received | Current Treasurer | pending_acknowledgement |
| Acknowledge receipt | SLD | acknowledged |

Items and recipient allocations must total the requested amount. Finance does not have a system login for this route: SLD records its signed document. The system does not independently establish whether an uploaded file contains a genuine Finance approval; SLD remains responsible for checking it.

The transfer target is default 14 days from SLD all-approval. The server freezes that deadline from the setting used at approval. A later policy change does not rewrite it. Passing the date does not assert that a bank transfer happened.

Finance/fund documents are private, stored with actor, time, version and file fingerprint. Current Treasurer must supply the correct receipt evidence before signing received. Final acknowledgement is a single controlled transition. Reasoned returns retain previous signed evidence and reopen correction.

### Current limitations
- **Clean-install defect:** PDF validation imports pypdf, but the application dependency list and hosting diagnostic omit it. A valid file may be rejected as unreadable on a clean installation. The developer runtime containing the library can hide this defect.
- No direct bank integration or automatic transfer confirmation.
- No automatic expense posting from withdrawal stages; settlement/reconciliation is still missing.
- Annual archive includes withdrawal records, approval/receipt files and signature history, but not the rendered withdrawal-form PDF alongside them.

These are specific gaps, not evidence that every withdrawal stage is absent. The ordered route and guarded access are implemented; the incomplete surrounding operations prevent calling the whole financial process finished.

<!-- pagebreak -->
# 10. Supporting workflows

### W11. Calendar, performance and dashboards
SLD approval creates an internal event entry. The calendar screen is SLD-only; assigned users have scoped event/performance views. Activity analysis also includes actual weekly/AGM records and evidence-aware completed events. Distinguish future/ongoing/past scheduled events from confirmed activity. The annual activity grid is for club performance, not the financial ledger.

Students see assigned club/event widgets; advisors see their review work; SLD sees all clubs and follow-up. Filters apply automatically. Google add-event links and ICS exports are available. **Automatic live Google Calendar synchronization is not implemented.**

### W12. Notifications and activity
Meaningful assignment/status transitions create in-app notices for currently connected committee/advisor and actionable SLD work. Routine unchanged autosaves do not generate an alert stream. Opening a notice checks current access; an old notice cannot restore removed permissions.

Activity records contain actor, action and server time. Relevant entries group within proposals/reports and selected club context. SLD sees all; committee/advisor views remain scoped. Email/push delivery remains unconnected.

### W13. Assistant and public profiles
Student browses public club profiles/hierarchy and published activities. Own profile is separate and contains captured personal assignments. Private contact, student ID, bank and signing information must not enter public profiles.

Chat button opens a compact window; expand opens a full page. Question → current-permission filtering → local retrieval → grounded response with permitted links → save personal history. Optional external generation requires explicit configuration/approval. Users can delete their own history. Changed/revoked sources invalidate stored private answer availability.

Ordinary-student assistant currently retrieves public upcoming events, not all internal club knowledge. Committee/advisor asks about assigned records; SLD asks across clubs. Local retrieval is not a university-validated generative RAG service. No assistant approval/signing action is provided.

### W14. Annual archive and exports
SLD selects a club/year after approved AGM acknowledgement/handover start. Server collects hierarchy, weekly/AGM records, event proposals, receipts, photos, completion/financial reports and private audit versions into an ordered ZIP with a file manifest. Private archive access is SLD-only.

The archive is assembled synchronously in memory with a 256 MB uncompressed limit. It cannot include modules/files never collected. It is a convenient compilation, not a scheduled backup or a frozen year-end retention system. Original-form exports still require representative long-text/multilingual checks on the target renderer.

<!-- pagebreak -->
# 11. Intended workflows not yet complete

### W15. Membership and semester reporting
**Planned:** SLD/club defines membership period and fee → committee shares join QR → student identifies/registers → selects cash/bank payment → bank proof uploaded or cash recorded → authorised verifier checks payment → membership status updates → reconcile members/collections/deposits → export semester membership-drive report.

Before building, decide duplicate membership, unpaid access, fee exemptions, refunds, who may confirm cash/bank evidence and who owns deposited funds. This must produce an authoritative membership list; a displayed report field alone does not achieve it.

### W16. Outdoor indemnity and post-event obligations
**Planned:** outdoor event identified → participant list/forms issued → participant/required guardian provides details and consent → authorised people review completeness before participation → retain protected documents under policy.

Decide participant coverage, guardian rules, collection deadline, emergency-data access and whether missing consent blocks participation. Add dedicated survey/post-mortem/attendance evidence, due dates and a completion checklist. SLD should see missing documents per event.

### W17. Google Drive and Calendar integration
**Planned:** approved event → create university-owned Drive folder → assign only approved permissions → organise proposal/evidence folders → store folder reference → reconcile removed access and failed provisioning. Link failures must be visible and retryable without duplicate folders.

For live Calendar synchronization, select the university calendar owner and define create/update/cancel behaviour. A downloadable ICS file is a copy, not a synchronized record. ICT must approve credentials, scopes and ownership before either integration is used.

### W18. Administrative changes and recovery
**Planned:** authorised admin requests staff/role change → verifies scope → applies change with audit → affected sessions/access rechecked. Template replacement requires field mapping, sample rendering and activation/version policy; historic signed exports retain their approved template version.

Provide retention/archiving rules, operational restore, monitoring and controlled data correction. Existing SLD policy settings do not equal complete administration of every user and module.

### Why these remain separate
Membership, participant consent, financial settlement and record retention each have their own authority and consequences. Combining them into miscellaneous proposal fields would hide missing rules and increase the very maintenance problem this audit identifies.

<!-- pagebreak -->
# 12. Architecture: what exists and where complexity sits

| Layer | Main source | Responsibility |
|---|---|---|
| Interface | web/app.js, web/styles.css | Screens, state, navigation, autosave, signatures and API calls |
| Central application | server.py | HTTP routing, core club/proposal rules, permissions, bootstrap and record operations |
| Identity/storage | auth.py, storage.py, wsgi.py | Google identity, persistence, shared sessions and hosting adapter |
| Business modules | club_reports.py, finance.py, withdrawals.py | Report/account/withdrawal workflows |
| Evidence/output | evidence.py, exports.py | Photos/completion/archive and document generation |
| Supporting views | profiles.py, performance.py, notifications.py, assistant.py | Public/scoped profiles, activity, notices and retrieval |

### Measured source observations
- web/app.js: **306,232 bytes, 488 physical lines, 301 named function declarations**; 96 lines exceed1,000 characters. Several forms are single extremely long lines. This is a readability and responsibility-concentration issue, not a performance benchmark.
- server.py: **1,440 lines**; do_POST spans 489 lines and do_GET 157. It owns both dispatch and many workflow decisions.
- Separate backend modules genuinely exist. Function counts or short physical line counts do not prove good separation when statements are compressed together.
- MySQL uses records(kind,id,data), logs and sessions tables. Most business data is serialized JSON. This is MySQL-backed, but not a conventional normalized relational business schema.

### Why this matters
Changing shared frontend state/rendering can affect unrelated forms, navigation or unsaved edits. Reverse dependencies on server helpers make isolated domain testing/refactoring harder. JSON relationships are largely checked in application code rather than foreign keys and explicit business tables.

MySQL's database-wide advisory mutation lock helps ensure consistent multi-worker writes. It also serializes writes across clubs. Bootstrap performs broad collection/decorating work, and some paths scan record collections. These are scaling hypotheses requiring measurement, not proof of an observed overload at the intended population.

Photos/receipts/documents stored as base64 in database records add storage and transfer overhead. Archives and original-layout PDF conversion consume server memory/processing. Separate file storage and background jobs may be appropriate once measured needs and hosting support are known.

**Verdict:** a modular backend prototype with a large central application and frontend monolith, accumulating technical debt. Some spaghetti symptoms are present; a blanket claim of no structure is not supported.

<!-- pagebreak -->
# 13. Findings and priorities

| ID / priority | Observed problem | Required response |
|---|---|---|
| F01 / Before pilot | pypdf used for withdrawal PDFs but undeclared and unchecked | Declare compatible dependency, include hosting check, test valid PDFs in a clean install |
| F02 / Before pilot | Registration signing display name remains client-supplied | Use authenticated canonical signer metadata; align drawn-signature policy and export tests |
| F03 / Before pilot | Status documents conflict with API 1.7 and each other | Create one current feature/status register; mark dated historical sections clearly |
| F04 / Before pilot | Legacy document packager assumes 18 pages/73 IDs while current concise source is 5 pages | Repair or retire obsolete rebuild path; use one reproducible document entry point |
| F05 / Before financial reliance | Withdrawal settlement, corrections/refunds and cash reconciliation incomplete | Finance-approved workflow, evidence and exact-once accounting rules |
| F06 / Before operational sign-off | Annual archive lacks rendered withdrawal form and cannot include missing collections | Add human-readable withdrawal export and agreed complete archive manifest |
| F07 / Stabilisation | Frontend concentrated and densely formatted | Format without behaviour change; split state/API/render/domain modules incrementally |
| F08 / Stabilisation | Central routing/App helper coupling | Extract shared errors/identity/access contracts, then domain services and thin route adapters |
| F09 / Capacity acceptance | Global write serialization, broad scans and synchronous archive/PDF work | Measure representative workloads before changing transaction guarantees |
| F10 / Release gate | Real Google, Exabytes, backup/restore, browser and load acceptance absent | Complete controlled university staging and record actual outcomes |

### Known unresolved runtime observation
Earlier local testing recorded intermittent Windows connection resets while downloading Word/PDF files. Some later runs succeeded, but the cause remains unresolved. This audit did not reproduce or clear it. Investigate and test reliable downloads on the actual staging stack; successful controller tests do not settle it.

### What was not established
No new browser rendering/scroll/keyboard verification, live university login, production database connection, bank transfer, external AI generation or Exabytes deployment was performed. The earlier browser refusal was respected. Findings F01/F02 are source-confirmed; a clean production deployment failure or malicious-user privilege escalation is not claimed.

The immediate aim is dependable operational behaviour and clear ownership. A wholesale framework rewrite before closing these concrete gaps would add risk without proving a better outcome.

<!-- pagebreak -->
# 14. Remaining delivery plan

The order below is dependency-based. Dates and effort estimates should be agreed after ICT hosting and SLD/Finance decisions; none are invented here.

| Stage | Work and owner | Exit condition |
|---|---|---|
| 1. Establish baseline | Project owner + SLD: approve scope/status register; identify authoritative workflow and policies | One agreed feature list, states, responsibilities and pilot scope |
| 2. Close concrete defects | Developer: F01-F04, signer consistency, archive output gap and failed-download investigation | Clean install/import, trusted signer, reproducible docs and reliable representative downloads |
| 3. Separate responsibilities | Developer + reviewer: readable frontend, domain modules, shared API/errors/access contracts, thin routing | Existing regression suites pass; each changed workflow has unchanged acceptance behaviour |
| 4. Verify university foundation | ICT: Exabytes staging, MySQL, HTTPS, Google fields/photos, renderer, secrets, support and restore | Real authorised users complete login/export/recovery on the chosen host |
| 5. Complete membership | Developer + SLD/Finance: W15, member list, cash/bank verification and semester reports | Members/payments/deposits reconcile with traceable differences |
| 6. Complete event obligations | Developer + SLD: W16, proposal cost uploads, attendance, indemnity, survey/post-mortem and closure | SLD can identify every missing obligation and enforce agreed completion rules |
| 7. Complete financial operation | Developer + Finance: settlements, corrections/refunds and reconciliation | Advances and expenses reconcile without duplicate ledger effect |
| 8. Complete administration/integrations | Developer + ICT: roles, templates, Drive and live Calendar under approved scopes | Controlled lifecycle/version/access updates with failure recovery |
| 9. Accept five-club pilot | SLD + advisors + committee + ICT | Real end-to-end scenarios pass; material defects closed and support manual accepted |
| 10. Scale and operate | ICT + SLD: measured capacity, monitoring, backups, phased club rollout | Actual service targets met with tested recovery and named owners |

Stages 5-8 can be split into independent work packages only after their rules and interface contracts are agreed. Do not expand scope while treating an unresolved acceptance failure as completed.

### How to refactor without losing working behaviour
First preserve isolated regression fixtures and record current request/response/state contracts. Fix test loaders that extract one-line functions before formatting; otherwise harmless multiline changes can break the harness. Format separately from functional changes. Move one domain at a time, verifying returns, signatures, revoked access and autosave races. Keep ledger approval/posting in one transaction. Defer schema migration or lock redesign until backed by measured requirements and a reversible migration plan.

<!-- pagebreak -->
# 15. Acceptance and handover checklist

### SLD business acceptance
- One-time registration cannot be used twice; first SLD opening locks the correct version; correction is understandable.
- One person can hold multiple club/event positions without receiving unrelated access.
- Proposal required sections, objectives, SDGs, conditional requests, schedules and short-notice rules work together.
- One proposal preparer and the correct ordered reviewer signatures appear in separate original-form cells.
- Weekly/AGM reports have required photos and four signatures; trackers distinguish draft, submitted and approved.
- Handover expires outgoing club authority at the server deadline, while historical signatures remain unchanged.
- Actual accounts update the balance only after SLD approval, once; Finance agrees settlement and correction rules.
- Withdrawal Finance approval, transfer proof, Treasurer receipt and SLD acknowledgement are all traceable.
- Notifications, returned reasons and dashboards clearly tell each role what to do next.
- Membership, indemnity and post-event obligations pass their agreed completeness/reconciliation checks before being included in pilot scope.

### ICT operational acceptance
- Clean dependency installation; production mode rejects preview access and requires MySQL.
- Real QIU Google identities, fields/photos, session expiry and revoked-role access verified.
- Dedicated HTTPS application origin, private files, protected secrets and trusted server clock.
- Original-layout Word/PDF/Excel outputs checked for long text, Unicode, signatures and required archive contents.
- Reliable downloads, simultaneous autosaves/reviews and large export behaviour tested on the chosen host.
- Real desktop/mobile/keyboard/signing/recovery checks; source inspection is not their substitute.
- Backup restoration, release rollback, monitoring, retention and incident/support ownership demonstrated.
- External AI/Drive/Calendar permissions reviewed and no private data exposed to public users.

### Pilot success and outstanding decisions
Exercise a complete annual/event cycle with representative roles and Finance evidence, using controlled test data. Record expected/actual outcomes and defects, rather than declaring success from the number of screens. Confirm the acceptable workload, recovery period, report deadlines and signature policy before official sign-off.

No generic promise of “zero bugs” or automatic compatibility with all Exabytes plans is appropriate. Compatibility depends on the university's actual server capabilities and operational acceptance.

<!-- pagebreak -->
# 16. Evidence, source map and terms

### Fresh checks for this audit
On 15 October, the frontend reviewer ran JavaScript syntax validation and **19 Node controller suites**, all passing. The backend reviewer ran **test_lifecycle_review.py, test_profiles.py and test_wsgi.py**, all passing in isolated local tests. These cover selected boundaries; the entire Python collection and live MySQL suite were not rerun for this audit.

Earlier project records describe broader Python/MySQL, export and rendered-document checks on 9 October. Those are historical evidence and have not been relabelled as fresh results. Existing representative form renders do not establish every future export layout or browser interaction.

### Source map for technical verification
| Topic / finding | Source location |
|---|---|
| API 1.7 and broad bootstrap | server.py:622-647 |
| App storage, handover projection | server.py:272-315 |
| Large request handlers | server.py:748-904 and 916-1404 |
| Registration display-name attribution, F02 | server.py:1173-1186; web/app.js:41,149 |
| Withdrawal states and PDF import, F01 | withdrawals.py:55-181, especially 143 |
| Dependency/diagnostic gap | requirements.txt:1-8; tools/hosting_check.py:19 |
| Annual archive coverage, F06 | evidence.py:323-405 |
| Shared mutation locking, F09 | storage.py:90-126 |
| Serialized business records | mysql_schema.sql; server.py:288-323 |
| Source-format generation | exports.py; retained templates/ |
| Scoped access/reports/assistant | club_reports.py, finance.py, profiles.py, notifications.py, assistant.py |
| Stale status documentation, F03 | PRD.md opening; docs/SPECIFICATION.md opening; docs/PRODUCTION_READINESS.md:67 |
| Obsolete pack checks, F04 | tools/package_review_docs.py:1-60 |

Audit working notes are retained in .agency/audit-2026-10-15/backend.md, frontend.md and review.md. Technical specifications, manuals and source inventory remain useful references but dated statements should be read against this audit's current code findings. This report preserves the earlier concise solution rather than silently replacing it.

### Plain-language terms
**Backend:** server code that checks rules. **Frontend:** screens/browser behaviour. **API:** messages between them. **Revision:** saved version number. **Snapshot:** frozen submitted content. **Ledger:** approved money entries. **Transaction:** linked changes succeed together or none do. **Monolith:** many responsibilities in one application/file. **Coupling:** one part depends heavily on another. **Technical debt:** structure that increases the cost/risk of later changes. **RAG:** retrieve permitted evidence before generating an answer. **Staging:** a controlled host for realistic acceptance before official use.

**Next decision:** agree the baseline and stabilisation stages first. Keep the working protections, close the concrete defects, then finish the missing business processes through explicit acceptance gates.
