# QIU Student Life Division — system specification

Revision: 2026-10-08. API version: 1.4. Status: local prototype; production release pending the evidence in PRODUCTION_READINESS.md.

## Purpose and scope

Students complete university club and event forms through structured website fields. Advisors endorse the submitted version, SLD approves it, and exports follow retained source templates. The current build covers identity capture, authorized club registration, approved profiles, proposals, approval, calendar, scoped audit, SLD policy/directory contacts, actual event accounts with private evidence and approved ledger postings, AGM/weekly reports, controlled committee handover, operational performance and a permission-scoped assistant. Membership collection/payments, financial adjustment/transfer workflows, Google Drive provisioning, indemnity collection and administrator template replacement remain planned. The completion indicator does not count these unimplemented modules as complete.

## Latest proposal and event capabilities

Duration is computed from strict planned Malaysia start/end values on save/decorate/export, with integer seconds and readable day/hour/minute/second units. Invalid/incomplete draft schedules produce an empty duration, but submission fails. Client-supplied duration is ignored. Collaboration stores approved club IDs and an optional Other flag/text; a minimal authenticated catalog exposes only IDs/names. Server rejects duplicate, unknown or self-collaboration IDs, resolves names and clears inactive Other. Legacy free text is preserved as Other when normalized.

`step_errors` groups required checklist failures for Overview (0), Programme (1) and Budget/export (2). The client evaluates matching rules against current unsaved fields before moving forward; backward navigation remains possible. The server permits partial draft autosave and validates every required/conditional item at submission. Conditional requests add checklist items dynamically, so the completion denominator is not a fixed14. ICT is required when requested in either mode; logistics is physical-only. Present budget rows require description, nonnegative price and positive quantity, while empty tables remain legitimate.

New proposal drafts carry a UUID `creation_key`, retained in sanitized account-scoped recovery. The server scopes its mapping to the authenticated actor and organizing club and writes the mapping and first draft atomically. A repeated first-create request returns the original ID/revision with `creation_replayed`; the client then saves its current retained fields using normal revision checks before reporting them as saved. A replay after another save returns a conflict instead of overwriting changes. This key grants no access and is not a credential.

Club activity analysis attributes explicit club IDs or current legacy club/proposal/grant IDs. `activity_summary` counts all attributable logged actions, proposal statuses and financial-report statuses. Monthly/yearly `scheduled_events` counts all valid scheduled proposals; `events` remains the approved subset. Day cells carry event IDs/statuses so drafts are not presented as approvals. Money series still contains only approved actual ledger rows.

Objectives store ordered strings (legacy newline text normalizes on save); submission requires at least two distinct nonblank entries. `ict_required` and `logistics_required` are strict booleans, default true for legacy records. Unchecked support sections clear their inactive text; logistics also clears transport/departure/return fields. DOCX/PDF fills those sections as Not applicable without altering the source package's styles/media.

Committee rows carry email/name/university_id/role/responsibility. Server resolves QIU email to an available imported contact, trusted directory search cache, signed-in user or current club identity and overwrites supplied names/IDs. Missing provider IDs remain explicit; duplicate emails are rejected. Event-only access derives from current email assignments. Bootstrap returns only assigned proposals and minimal `event_clubs`; full `clubs`, registration exports and club balances require club membership/advisorship or SLD. Event participants can edit draft content but cannot create unrelated proposals, submit or alter committee assignments. Activity/calendar/export checks share event scope. Advisor self-endorsement is denied when assigned to that event committee.

## Actual finance data and logic

`finance.py` reuses SQLite records: `receipt` (private encoded bytes, MIME/size/hash/actor/time), `finance_report` (revisioned rows/status/history), `finance_version` (immutable submitted snapshot/digest), `ledger_entry` (approved row), and `finance_opening` (one-time SLD opening record). Evidence content is never returned in bootstrap or metadata lists. Downloads authenticate and check the current event scope; PDF/PNG/JPEG/WebP signatures and decoded 2MB size are checked. Magic signatures do not establish malware scanning; production file scanning/storage/quotas remain pending.

Money accepts decimal strings with up to two fractional digits and converts to integer cents. Budget references identify income/expense item indices; actual rows aggregate against matching planned items. Submission requires positive actual amounts, descriptions, evidence for every row and a variance explanation when amounts/items differ or a row is unplanned. Actual reports require approved proposals and organisers/SLD; advisors view but cannot prepare solely through advisor assignment.

Draft/returned -> pending_sld -> approved or returned. SLD approval requires event end <= server time. Submitted snapshots/digests and review attribution are server-owned. The existing mutation lock serializes review and revision checks; one SQLite transaction writes approved report and stable report-row ledger IDs. Duplicate/stale review fails before posting. Balance = approved opening + approved actual income − approved actual expenses; no proposed budget posts. Monthly/yearly financial series group ledger by SLD approval time in MYT, while event progress uses scheduled event start and action progress uses audit timestamps. Opening balance may represent a signed liability but may not be overwritten; approved ledger records have no edit/delete endpoint.

| Endpoint | Permission / result |
|---|---|
| GET /api/finance?club_id | Club committee/advisor or SLD; balance, ledger/events, graphs/activity days |
| GET /api/proposals/{id}/finance | Assigned event or club users / SLD; report, budget and private evidence metadata |
| POST /api/finance/reports | Approved event organiser / SLD; draft/returned revisioned save |
| POST /api/finance/reports/{id}/submit | Organiser / SLD; validation and immutable version |
| POST /api/finance/reports/{id}/review | SLD; return with reason or post-event approval/posting |
| POST /api/receipts; GET /api/receipts/{id} | Scoped organiser upload; scoped authenticated download |
| POST /api/finance/opening | SLD; one-time amount and source/reason |
| GET /api/finance/reports/{id}/export/pdf | Same event scope; actual financial PDF |
| GET /setup/google | Public local setup guide; no secret input |

Google launch configuration: tools/start_google.ps1 loads a private downloaded Web-client JSON into process environment. Default mixed local mode retains seven fictional roles and preview.sqlite3; `-OfficialMode` disables test roles and selects sld.sqlite3. Profile identity labels depend on `user.preview`, separately from database mode. Live OAuth/directory verification remains outstanding.

The intended pilot is five clubs; planning population is 30+ clubs, about 2,000 students, 50+ advisors and 10 SLD staff. Those figures are not measured concurrency or performance claims.

## Technology and file responsibilities

Official hosting now targets Python 3.12+ with MySQL-compatible InnoDB storage. `SLD_ENV=production` requires `SLD_STORAGE=mysql`; preview identities/SQLite are rejected in that mode. Local preview remains SQLite and existing data is preserved. `storage.py` provides utf8mb4 records/logs and encrypted shared sessions, with a database-wide advisory mutation lock and InnoDB transactions spanning revision checks and writes. One connection per worker is serialized with its lock and safely reconnects before a new transaction; no retry reconnect happens midtransaction. This global lock is a correctness-first throughput ceiling, not measured capacity for 2,000 users. Sessions use hashed opaque-cookie IDs and Fernet-encrypted payloads with expiry/revocation tombstones; every worker uses the same protected encryption key.

`wsgi.py` and `passenger_wsgi.py` delegate the existing handlers without opening a development-server socket. Hosting requires a dedicated HTTPS domain/subdomain mounted at `/`. `mysql_schema.sql` and `tools/migrate_mysql.py` explicitly initialize/import into a separate empty database, keeping the source read-only. `tools/hosting_check.py --connect` checks configuration, dependencies and database/schema using the same TLS options as the application; it does not deploy or certify provider entitlement. [EXABYTES_HOSTING.md](EXABYTES_HOSTING.md) describes exact deployment prerequisites.

`notifications.py` stores recipient-specific notifications for registration grants, newly assigned club/event members and meaningful submission/review/return/permission transitions. The actor is excluded, repeated autosaves with unchanged assignments produce no alerts, and SLD receives actionable review-stage notifications. Recipients are the organizing club's committee/advisor and current event assignees, not collaborating-club members with no access. List/count/read all recheck current assignment and ownership; revoked users cannot read historical notifications. `GET /api/notifications?offset=0&limit=25` returns scoped items/counts; `POST /api/notifications/{id}/read` writes the server read timestamp. Bootstrap includes `notifications_unread_count`. Notifications are in-app; email/push delivery is not configured.

| Component | Current implementation | Purpose |
|---|---|---|
| Website | HTML, CSS, vanilla JavaScript; web/app.js | Club context, forms, autosave, controlled selections, review and admin screens |
| API server | Python; server.py handlers; wsgi.py/Passenger production entry | Authentication, permissions, validation and workflows; standard-library server for local preview |
| Identity | auth.py, Google OpenID Connect, google-auth, requests | Verified university sign-in and profile refresh |
| Directory | Google People API, directory.readonly scope | University directory search and paginated SLD import |
| Data | MySQL-compatible InnoDB/utf8mb4 via PyMySQL in production; SQLite WAL for local preview | Transactions, shared-worker sessions, records/audit/notification persistence; explicit migration |
| Document generation | exports.py, lxml, retained templates/event-proposal.docx | Fill the original document package and calculate budget totals |
| PDF | LibreOffice for proposal; ReportLab for registration | Actual PDF generation; report fonts available on host |
| Spreadsheet | openpyxl | Proposal budget Excel export; formula injection protection |
| Calendar | calendar_export.py | Scoped, UTF-8-safe ICS export; website Google add-event links |
| Controlled catalog | catalogs.py | One list of 17 SDG identifiers and names |
| Recovery tooling | tools/backup.py | Consistent SQLite snapshot and temporary restore verification |

Dependencies are declared in requirements.txt. Preview is launched with `python server.py --preview --port 8765`. No real university authentication is simulated as verified by the preview.

## Identity and permissions

Google identities must have a verified @qiu.edu.my email and the QIU hosted-domain claim. Login validates state, nonce, PKCE and token audience. Name/email/photo come from Google; university ID, programme, department and person type depend on directory visibility and maintained fields. Directory labels never grant SLD authority. SLD access is currently an environment allowlist, SLD_ADMIN_EMAILS; privileged-role administration remains a production gap.

| Action | Assigned committee | Assigned advisor | SLD |
|---|---|---|---|
| Create a club | Assigned president, once, with SLD grant | No | Issues grant; does not bypass assigned-president creation |
| Edit registration | Before SLD review lock; returned for correction | View saved progress | Same recorded-state restrictions apply |
| Submit registration/proposal | Yes, within assigned club | No independent committee editing privilege | Yes where the route permits; advisor endorsement still required |
| Sign advisor review | No self-endorsement | Assigned club and correct stage | Cannot skip the required advisor stage |
| Final approval | No | No | Correct pending SLD stage only |
| Read/export club documents | Assigned clubs | Assigned clubs | All clubs |
| Read activity | Assigned clubs only | Assigned clubs only | All clubs; can filter by club |
| Change day policy / issue exception | No | No | Yes, with revision and audit |
| Browse/import contacts | No | No | Yes |

The same person can be president of club A and advisor of club B. Per-club roles remain independent. The four mandatory officers within one club are still distinct people. Global identity/person type is not replaced by an advisor assignment.

## Persistent records

| Record kind | Identity and significant fields |
|---|---|
| user | Verified provider ID, email, captured directory fields, application role |
| registration_grant | SLD assigned club/semester/president/advisor, one-time status, server times |
| club | Profile, officers, advisor, owner, revision, status, review history, lock time |
| club_version | Submitted revision, content snapshot and SHA-256 digest |
| proposal | Club ID, form sections, budget, revision, status, author, planned schedule |
| proposal_version | Submitted snapshot, digest, policy and exception evidence |
| system_settings | Operational day policy, revision, server actor/time |
| deadline_exception / deadline_exception_version | Current club permission and retained grant/revocation snapshots with reason, expiry, revision, server actor/time |
| calendar_event | One approved proposal ID, club, title, start/end, approval time |
| contact | University email, directory name/ID/photo URL, programme/intake, import time |
| logs table | Actor/name, action, record and club, server timestamp |

Database keys use complete record identifiers. Contacts use complete university email. Student ID QIU-202404-007157 means intake year 2024, month 04, serial 007157; the last four digits are 7157. All six serial digits and the full ID are preserved. A trailing-four search does not establish uniqueness. Invalid/missing IDs remain explicitly unavailable rather than guessed.

## Authoring, validation and progress

Draft proposal autosave accepts incomplete entries, including a missing title. Selected SDGs must be a unique list of strings from 1 through 17. Arbitrary typed SDG values are rejected on the server. Text/table/budget values are bounded, numeric amounts are finite and nonnegative, and client-supplied record metadata is ignored.

Proposal progress measures 14 required items: title, summary, venue, introduction, objectives, eligibility, conclusion, valid date/start/end, positive whole-number participant count, a complete activity row, complete itinerary row and complete organising responsibility row. Percentage = rounded completed/14 × 100. SDG selection is optional, as the original form says if required; selected values must still come from the controlled list. The optional SDG row does not reduce required-field progress. Empty extra rows are incomplete. A 100% form is ready for submission validation, not approved. Policy timing and permissions are still checked at submission. Club registration separately measures profile fields and the four mandatory officers against nine items.

Autosave debounces input, serializes requests and uses revisions to reject stale writes. Successful saves update metadata without replacing newer local text. Navigation, export and submission flush pending changes. Failed saves retain draft data and block unsafe in-app navigation. Browser close/crash/offline can prevent delivery; no autosave system guarantees network delivery on forced termination. Session recovery must preserve the local draft, require the same identity, and reload server revisions before another write.

## Dates, policy and urgent permission

Recorded times are server-generated UTC and immutable to every user. The UI displays Malaysia time (UTC+8). Planned event dates/times and a future permission expiry are inputs; they are not recorded-action timestamps.

Default lead time is 14 days. SLD may set a whole number from 1 to 365. Legacy settings in weeks are read as weeks × 7. A proposal is ordinarily admissible when server now ≤ event start − configured days; equality is accepted. Start and end are valid Malaysia-local datetimes and end > start. A past or already-started event cannot be submitted.

SLD can issue a club-specific, reasoned, future-expiring exception. It permits the club committee to submit inside the normal lead window while enabled and unexpired. It does not grant access to another club, approve the event or bypass required fields/signatures. SLD can revoke it. A late submission stores the exact exception revision/reason/issuer/time/expiry in its immutable snapshot; later revocation does not rewrite history. Submitted records preserve their policy days. Returned drafts are checked again when resubmitted.

## Activity and calendar

Activity is filtered by current club assignment before counting, grouping or pagination. An actor's past action in an unrelated club does not confer access. New proposal actions record the proposal ID and club ID, creating one expandable group for that proposal. Registration actions group under the club. Legacy proposal actions recorded only with a club ID cannot be reconstructed into a particular proposal reliably; they remain club-level history. Expanding a group loads only its matching record timeline.

Final SLD proposal approval atomically saves the approved proposal and one calendar_event keyed by its ID. Duplicate approvals are rejected. Calendar export is permission-scoped. Google add-event links and ICS import are available; live account synchronization is not connected. ICS escapes event text, folds UTF-8 lines, uses timezone-aware schedules and stable IDs.

## Directory import and photos

SLD imports the directory visible to its signed-in university account through all pages before replacing the stored snapshot. Imports retain existing contacts on fetch failure. Domain profile/contact sources are requested; non-QIU emails are excluded. Provider access controls, missing fields, hidden entries and missing photos are not overridden. Photo URLs are accepted only from HTTPS Googleusercontent hosts; preview avatars are explicitly fictional. The snapshot stores photo URLs rather than claiming an offline archive of Google image files. Profile and committee displays fall back to initials when a photo is unavailable.

SLD contact filtering supports programme, full student ID, club officers/advisor, intake year/month and a general search. Club filtering currently represents registered committee/advisor assignments; general membership is not implemented. Live bulk import, directory completeness and field mapping still require actual university verification. [Google People directory reference](https://developers.google.com/people/api/rest/v1/people/listDirectoryPeople).

## API contracts

All mutations require same-origin JSON and a session CSRF token; access is checked on the server.

| Method and path | Purpose |
|---|---|
| GET /api/bootstrap | Session, scoped clubs/proposals, policy, SDGs, calendar, exceptions, API version |
| POST /api/preview/login | One of seven fictional test personas; preview mode only |
| POST /api/registration-grants | SLD one-time authorization |
| POST /api/clubs | Authorized creation or revisioned registration save |
| POST /api/clubs/{id}/submit | Registration snapshot submission |
| POST /api/clubs/{id}/open-review | SLD first-open lock |
| POST /api/clubs/{id}/review | Assigned-stage signature/return |
| GET /api/clubs/{id}/export?format=pdf | Registration report |
| POST /api/proposals | Partial draft autosave with revision |
| POST /api/proposals/{id}/submit | Completeness, day/exception validation and immutable snapshot |
| POST /api/proposals/{id}/review | Advisor endorsement, SLD approval, or correction return |
| GET /api/proposals/{id}/export?format=pdf/docx/xlsx | Retained proposal/budget export |
| POST /api/settings | SLD day policy with current settings revision |
| POST /api/clubs/{id}/deadline-exception | SLD enabled/reason/future expiry/current exception revision |
| GET /api/activity | Scoped entries; club_id, record_id, grouped=1, offset, limit |
| GET /api/contacts | SLD filtered contacts; offset, limit |
| POST /api/contacts/import | SLD complete directory snapshot import |
| GET /api/directory?q= | Limited form lookup; not the SLD contact catalogue |
| GET /api/calendar/export | Scoped approved-event ICS |

API errors include error, code and fields. Relevant codes include SESSION_EXPIRED, ACCESS_DENIED, RECORD_NOT_FOUND, VALIDATION_ERROR and DEADLINE_PASSED. The UI gives an action, focuses a relevant field or recovery panel and retains unsaved data. A missing route/record is distinct from an expired session. Internal exceptions never disclose credentials or raw stack traces to users.

## Export guarantees and limits

Original proposal styles, theme, headers/footers and logo ZIP members remain unchanged. Data fills supplied tables and repeatable rows. Signed exports also add PNG media, document relationships and PNG content type when needed. Submission date uses submitted_at; signing dates use immutable signed_at. Submitted exports append actual review actor/time/revision/digest evidence. Proposal signatures now appear in three distinct original-table cells: Prepared by (President OR Vice President), advisor Reviewed by (top right), and SLD Reviewed by (previously blank second-row left). Exactly one preparer signs each submitted version. Names, designations and departments are captured from authenticated/trusted profiles; absent directory job titles use the actual application role (Club Advisor or SLD Officer), while absent departments show Unavailable. Dates come exclusively from server signing time and cannot be edited. Returns clear current signatures; immutable earlier signatures remain in history, and corrected submissions require fresh signatures. Printed registrar, bursar and COO cells remain separate and unsigned. Registration has a new report layout because no original registration template was supplied. Arbitrary long entries can change pagination; representative exports are rendered and reviewed, not declared universally pixel-perfect.

## Verification links

Tests: tests/test_registration.py, test_system.py, test_events.py, test_deadlines.py, test_administration.py and Node autosave checks. WORKFLOWS.md shows decision flows. USER_MANUAL.md covers roles and recovery. GLOSSARY.md explains technical terms. PRODUCTION_READINESS.md distinguishes checked implementation from release prerequisites.


## Version-bound proposal signatures

The submit mutation requires a visible, valid PNG and current revision. Under the database mutation lock it validates President/Vice President authority, freezes the preparer identity and server time, hashes the snapshot without its own digest, and atomically stores proposal_version and proposal_signature records. Advisor and SLD approval bind the same submitted revision/digest to their distinct slots. A competing or repeated preparation request receives a conflict. Self-review by a preparer or club/event committee member is blocked. Legacy unsigned proposals must return for correction before approval.

Immutable signature key: `{proposal_id}-r{submitted_revision}-{slot}`. Export accepts only slot/revision/digest matches in current signatures and excludes draft/returned attestations. Client fields cannot change identity, signing date or slot. Drawings are ephemeral UI state, excluded from autosave and recovery.


## Operational reports, performance and assistant — 2026-10-09

Detailed contracts, route permissions and feature logic are in FUNCTION_FLOWS.md; source reconstruction and data relationships are in ARCHITECTURE.md; all individual function names and observed calls are in generated SOURCE_REFERENCE.md. New API modules: club_reports.py, performance.py and assistant.py. Production remains Python/MySQL with no separate vector service or added embedding dependency.

Report content fields: type, club_id, title, semester, date, start_time, end_time, venue, activity_kind, summary, objectives, attendance, minutes, decisions, next_meeting, new_committee, opening_speech, agenda, election_summary, outgoing_activities, adjournment, member_count. Server-owned fields include record ID, created/updated/submitted times, status/revision, owner, outgoing committee/advisor snapshot, signer assignments, signatures, history, submitted revision/digest and handover attribution. Submitted reports progress pending_secretary -> pending_advisor -> pending_sld -> approved. Current-stage return clears active signatures and opens committee correction. President alone signs report submission; this does not change the proposal President OR Vice President preparer rule.

AGM handover is SLD-only and separately applied once after report approval. It checks current report/club revisions, frozen outgoing roster and unfinished Secretary-stage obligations. It updates current committee/owner atomically and records its approved report authority; old registration signatures do not attest the new committee.

Performance uses approved actual weekly/AGM reports and approved calendar events. It distinguishes scheduled, ongoing, past_scheduled and completion supported by approved actual-account evidence. Finance graphs remain financial. Public event projection is authenticated and contains only approved published upcoming/ongoing ID/club/title/schedule/venue/description; no internal history, committee, budget, receipt or signatures.

Assistant POST question is read-only except a shared account rate-counter record. Permission filtering precedes BM25 ranking/provider generation. Source excerpts exclude sensitive file/signature/token/directory payloads. No global private cache or accepted client history. Internal links are a fixed task whitelist, checked again on open. Response fields: answer, mode, provider_status, sources, scope, generated_at, matching_count and has_more. Configuration and live-provider limits are in ASSISTANT_SETUP.md.

## Profiles, compact chat and annual reports — 2026-10-09
See [Profiles, chat and annual reporting](PROFILE_CHAT_REPORTS.md) for current profile/public projections, assistant history/deletion, annual AGM tracker/rebase, contextual signatures, per-item receipts and auto-applied filter contracts. This supersedes earlier semester-only AGM assumptions. Public club browsing does not grant private operational access. Browser/live Google/provider/hosting acceptance remains pending.