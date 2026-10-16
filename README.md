# QIU Student Life Division

Local operational prototype: login/profile capture, club registration, original-template proposals, four-stage weekly/AGM reports, scoped assistant, public approved events, operational performance calendar and actual event accounts with approved balances. Working prototype for correction; not a deployed official service.

## Documentation

- [User manual and all seven preview accounts](docs/USER_MANUAL.md)
- [Google sign-in setup guide and local credential launcher](docs/GOOGLE_SETUP.md)
- [System specifications, permissions and API/data logic](docs/SPECIFICATION.md)
- [Workflow flowcharts](docs/WORKFLOWS.md)
- [Every feature flow and API acceptance contract](docs/FUNCTION_FLOWS.md)
- [Architecture and reverse engineering guide](docs/ARCHITECTURE.md)
- [Generated function/call/source reference](docs/SOURCE_REFERENCE.md)
- [Scoped assistant configuration](docs/ASSISTANT_SETUP.md)
- [Technical glossary](docs/GLOSSARY.md)
- [Production-readiness evidence and remaining setup](docs/PRODUCTION_READINESS.md)
- [Interface audit: bugs, AI-slop findings and verification limits](docs/UI_AUDIT.md)

Current API version: 1.6. Proposal drafts autosave with serialized revisions and same-account session recovery. SDGs use controlled named selections, with at least two ordered objectives and optional ICT/logistics. Completion gauges describe required fields, independently of approval. Select a dedicated club to narrow proposals and expandable activity. SLD contacts support available photos, programme, full ID, club and intake filters. Day-based policy defaults to 14; SLD can grant/revoke a reasoned, expiring club exception. No exception can submit a past event or bypass signatures.

## Run the local preview

For another machine, install `requirements.txt` into a Python environment and run `python server.py --preview`. This workstation already has the selected runtime and authentication dependencies; the application can use its installed export libraries. Google configuration is separate from package installation.

```powershell
& 'C:\Users\QIU\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' server.py --preview --port 8765
```

Open http://127.0.0.1:8765. Preview president, vice-president, secretary, treasurer, advisor and SLD personas are fictional and visibly labelled. Preview uses data/preview.sqlite3; Google mode uses data/sld.sqlite3. Both persist across server restarts. Neither database is committed. Preview sign-in is disabled unless --preview is explicitly passed. The server binds only to loopback.

Start as SLD staff -> Overview -> Assign a registration. Enter club name, semester, president demo.student@qiu.edu.my and advisor demo.advisor@qiu.edu.my. Sign out and enter Student -> start the assigned registration. Only that president can create it once; the assignment is consumed at first saved creation. Ordinary students cannot create clubs. Assigned club name, semester, advisor and president stay fixed.

Enter biography/logo and the four officers. Preview directory lookup supports demo.student@qiu.edu.my, demo.vice@qiu.edu.my, demo.secretary@qiu.edu.my and demo.treasurer@qiu.edu.my. Registration autosaves after a short typing pause and flushes before in-app navigation/sign-out. Saved progress is visible to the advisor and SLD. Pending registrations remain editable until SLD first opens the submitted registration. Pending edits require a fresh advisor acknowledgment; signed history is retained. SLD first-open locks edits on the server. SLD may return a locked registration for corrections even while awaiting the advisor; final approval requires the advisor signature. Approved registrations remain locked.

Autosave shows saving/saved/error. Failed or conflicting edits remain on screen and block in-app exit; an explicit reload discards unsaved entries only after confirmation. Background refresh does not adopt an unseen revision. Browser close/crash/network loss cannot guarantee delivery: unsaved changes trigger a browser warning, with a small-payload pagehide backup. Large logos save through the normal request and exceed browser keepalive limits. The SLD dashboard refreshes its queues/counts while preserving assignment fields. Existing earlier preview clubs remain retained.

Select Proposals, choose a club, enter the original form sections, add programme/budget rows, save and export. Word exports fill templates/event-proposal.docx; PDF renders the same filled DOCX. Excel is a separate event-budget workbook, not a reproduction of the proposal's Word pages.

## Server dates and submission policy

Created, last-saved, submitted, signature, review and audit timestamps come from the server and cannot be edited, including by SLD. Stored record times use UTC; the interface displays Malaysia time. Future planned event dates/times remain editable in drafts.

Submit for review checks the saved event start against the server clock. Default minimum lead time is 14 days; submission exactly at the deadline is accepted. Late drafts may still be saved. SLD alone changes the lead time under Settings to a whole number from 1 to 365 days, and can issue/revoke an expiring club permission with a reason for an urgent future event. Settings/permission revisions prevent lost updates; each change records its server actor/time. Submitted proposals retain the policy and any used exception evidence in their snapshot, become read-only and remain exportable. Advisor signing then SLD approval are implemented.

Delivery mode (Physical/Virtual) and event setting (Indoor/Outdoor) are separate. Outdoor indemnity remains mandatory; collection is still deferred to the event module.

## Real Google Workspace setup

Start with [the complete setup guide](docs/GOOGLE_SETUP.md), also linked from the login screen at `/setup/google`. `tools/start_google.ps1` reads downloaded Web-client JSON locally and restores its process environment after exit. Default mixed prototype keeps Google sign-in above seven fictional roles and uses the test database. Contact searches/imports still use fictional fixtures in that mode; add `-Directory -OfficialMode` for local real-directory verification in the separate database, without test buttons. No real Google connection has been verified yet.

Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET and SLD_ADMIN_EMAILS in the server environment using university-managed credentials, then start without --preview. Register the exact redirect URI `http://127.0.0.1:8765/auth/callback` for local testing. SLD_APP_URL must match the browser origin (127.0.0.1 and localhost are different origins). Server verifies Google's signed ID token, audience, issuer/expiry, nonce, verified email and hosted domain qiu.edu.my; the OAuth request's domain hint alone is not authorization.

Set GOOGLE_DIRECTORY_ENABLED=true and enable People API and directory sharing/authorized scopes in QIU's Google Workspace. Requested scope is https://www.googleapis.com/auth/directory.readonly. Each login captures fresh available names, email, photo, organizations and externalIds for the exact signed-in email. University ID, Student/Staff type and programme/department are populated only if these fields are exposed and mapped; missing fields are shown as unavailable. Screenshot appearance does not establish API access or field equivalence. QIU may need an administrator-authorized mapping for employeeType/custom fields. Tokens are confined to short-lived server sessions: local SQLite sessions are in memory; hosted MySQL sessions are encrypted with a separately protected key. Imported directory contacts are limited to the approved university fields.

Google directory Staff classification does not grant SLD privileges. SLD admins are explicitly allowlisted by university email; advisor review is scoped to the assigned club email. Live login/directory have not been tested without university credentials.

References: [Google OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect), [People directory access](https://developers.google.com/people/v1/directory), [directory search fields](https://developers.google.com/people/api/rest/v1/people/searchDirectoryPeople).

## Original-format exports

The retained source remains unchanged. Exports preserve source styling, headers/footers, logos and table structures; signed exports add three PNG media/relationships in their mapped cells. Proposal signatures now appear in three distinct original-table cells: Prepared by (President OR Vice President), advisor Reviewed by (top right), and SLD Reviewed by (previously blank second-row left). Exactly one preparer signs each submitted version. Names, designations and departments are captured from authenticated/trusted profiles; absent directory job titles use the actual application role (Club Advisor or SLD Officer), while absent departments show Unavailable. Dates come exclusively from server signing time and cannot be edited. Returns clear current signatures; immutable earlier signatures remain in history, and corrected submissions require fresh signatures. Printed registrar, bursar and COO cells remain separate and unsigned.
Club registration exports a separate professional PDF report (profile, logo, officers, server timestamps and signed review history); no original registration template was supplied. Both current forms have PDF download controls.

## Approved clubs, events and audit

Approved registrations open a reusable club profile. Each identity can hold different positions across clubs; advisor privileges are derived from that club's assignment, not a global role switch. Approved-club committee members or SLD prepare proposals. Submission requires an event start/end and the configured lead time, then advisor signs -> SLD approves. Returns require a reason; correction/resubmission retains previous versions and rechecks the deadline. Approved records are immutable.

SLD approval creates one system calendar entry automatically. The monthly calendar displays Malaysia time. Add to Google Calendar opens a confirmation link; `.ics` downloads can be imported into staff calendars. This does not establish live synchronization. [Google's import guide](https://support.google.com/calendar/answer/37118?hl=en) explains that imported events do not stay synchronized. University-owned OAuth/calendar configuration is still required for future live synchronization.

The activity table shows human-readable actions, actor, club and server timestamp with pagination. SLD sees all activity; committees/advisors see only clubs to which they are currently assigned. Access is checked before pagination. Export permissions use the same club scope. `tests/test_events.py` verifies these workflows through actual HTTP requests.

Long content can grow rows or move page breaks. Original format preservation does not guarantee a fixed page count for arbitrary text. Review final exports. Future template replacement requires a reviewed field mapping; arbitrary upload-to-form automation is not implemented.

PDF conversion uses SOFFICE_PATH or project-local .tools/libreoffice. `.agency/setup_pdf.py` downloads a checksum-verified official LibreOffice MSI and extracts it into the project cache using Windows administrative extraction; it does not install the desktop application. No PDF substitute is produced when the renderer is unavailable.

## Verification

Earlier finance increment: seven Python HTTP suites and six Node suites passed. Added tests/test_event_access.py, tests/test_finance.py, tests/test_login.js, tests/test_finance_controller.js and tests/test_finance_views.js. They cover event-only isolation/revoked permissions, conditional original-template export, canonical directory identity, actual finance evidence/variance, database rollback/concurrent exact-once posting, long financial PDF content, login interpolation, retained in-flight financial edits and real progress/heatmap/expanded-event HTML. HTML mocks are not browser visual verification. Google launcher PowerShell syntax passed; live credentials remain absent.

```powershell
& 'C:\Users\QIU\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' tests/test_system.py
```

Tests use an isolated temporary database. They exercise draft -> submit -> return -> resubmit -> advisor -> SLD, permissions, immutable approved data, SQLite persistence, invalid form/budget values, Unicode Word exports, untouched template-package entries and spreadsheet formula injection. PDF is checked if the renderer is available.
`tests/test_registration.py` checks SLD authorization, one-time creation, bound identities, pending changes, review locks, correction returns and persistence. `tests/test_autosave.js` runs pure Node checks of the actual save/poll controller, including edits during a save, failure retention, navigation flush and unseen revision protection. These checks do not replace browser interaction verification.
`tests/test_deadlines.py` fixes the server clock to verify the exact Malaysia-time deadline boundary, late/invalid schedules, client metadata tampering, immutable submitted records, SLD-only settings, stale policy revisions and persistence.
Concurrent saves use revision checks: a stale editor receives a conflict instead of overwriting another committee member. Signed reviews refer to a stored submitted snapshot/revision and digest. The proposal's preparer is stored independently of whoever downloads the document.

The original and representative filled proposal were rendered with LibreOffice. All eight sample pages were inspected; objective numbering, ICT placement, paragraph spacing and table pagination were corrected. This sample check does not guarantee identical pagination for arbitrarily long entries. The final sequential API/export test passed; concurrent operational/load testing remains pending.

Browser access to the local preview was declined by the browser permission policy during this run. Rendered desktop/mobile and keyboard interaction verification therefore remains pending; code inspection is not claimed as visual verification.

## Deployment boundary and next modules

This localhost server is a prototype. Official rollout still needs university OAuth/directory verification, hosted HTTPS, secure operational secret management, backups/recovery, production hosting, role administration and operational/load checks. SQLite preview sessions are in memory and restart signs preview users out. MySQL hosting uses encrypted shared sessions with eight-hour expiry and revocation. Actual event accounts/private receipt evidence/SLD ledger posting are implemented. Membership fee collection, financial adjustments/refunds/transfers, Drive folders and indemnity collection remain future modules. Outdoor events show the mandatory indemnity requirement; collection is pending.

## Exabytes hosting, workspaces and notifications

Use [EXABYTES_HOSTING.md](docs/EXABYTES_HOSTING.md) for the Python 3.12+/MySQL-compatible deployment configuration. Production rejects SQLite and fictional preview mode. WSGI entrypoints are `wsgi:application` and `passenger_wsgi.py`; hosting uses a dedicated HTTPS domain root, not a subdirectory or the preview development server. Schema/import are explicit; source preview data remains intact. `python tools/hosting_check.py --connect` performs read-only checks without printing credentials. The purchased Exabytes account and original-template PDF renderer still need live confirmation.

Student, advisor and SLD workspaces now have grouped role-specific navigation; advisors start with reviews. The notification inbox/read badges follow current club/event access. Assignment and meaningful workflow changes create notices; routine unchanged draft autosaves do not. Email/push delivery is not configured. Same-record edits preserve viewport/focus/disclosures; actual navigation resets to the top. Browser/mobile scrolling still needs rendered verification.

New checks are `tests/test_notifications.py`, `tests/test_wsgi.py`, `tests/test_portable_pdf.py`, `tests/test_workspace.js` and explicit loopback-only `tests/test_mysql.py --port <QA-port>`. The real MariaDB 10.11.14 QA instance verifies the MySQL protocol, Unicode, source-preserving migration/nonempty-target rejection, transaction rollback, concurrent worker/revision behavior, encrypted shared sessions/revocation, reconnect and exactly-once financial approval. This is local engine evidence, not a production load or Exabytes deployment certification.

## Actual event accounts

Assigned organisers prepare actual income/expenses for approved events, attach private evidence and explain differences from the proposed budget. Reports save as drafts and submit to SLD; returned reports reopen. Only SLD approval after event end posts integer-cent ledger rows, once. Club balance is approved opening funds plus approved actual income minus approved actual spending. Proposed budget approval never changes it. Club committee/advisors see club graphs, activity calendar and expandable event records; event-only organisers see their event accounts, without unrelated club balance access. Financial PDF exports include evidence references and review-version history. See the role manual for precise limits.


## Reports, performance and assistant

Club reports autosave; one President submits with a drawn signature, then Secretary, advisor and SLD sign separate immutable stages. AGM approval is followed by a distinct guarded SLD handover action. Corrected reports need renewed signatures. Word/PDF export preserves supplied content sections with current signature cells and a tabular verification log.

Performance is operational, separate from finance: meetings/weekly activities, AGMs and event schedules with club/year/month/day drill-down. Ordinary students browse public approved upcoming/ongoing events; private records remain assigned-work only. The assistant retrieves current authorised records and returns clickable task sources. Grounded local answers work immediately; optional RAG generation requires server configuration and live acceptance. See the linked developer and role documents for complete logic and boundaries.

## Profiles, chat and report follow-up
API1.6 separates public approved club/student profiles from private operational workspaces, refreshes available login photos, provides shared floating/full assistant with persistent deletable per-account history, annual AGM uniqueness and year tracking, weekly follow-up and recorded future next meetings. Student signer designations reflect club position or applicable event role without granting extra signing authority. Forms retain original-format export and server signing dates. See [the profile/chat/report guide](docs/PROFILE_CHAT_REPORTS.md) and [implementation plan](docs/superpowers/plans/2026-10-09-profiles-chat-and-reports.md).
## SLD and ICT review documentation
Start with [plain-language requirements and workflows](docs/review/QIU_SLD_Requirements_and_Workflows.md). The same 18-page review pack is available as Word and PDF in docs/review; QIU_SLD_Review_Pack.zip bundles it with supporting technical documentation. It covers73 requirements, five workflow diagrams, role-based instructions, hosting prerequisites and a review worksheet. Current prototype and planned-module status are explicitly separated.
