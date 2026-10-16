# Technical glossary

## Actual accounts and Google setup

| Term | Meaning here |
|---|---|
| OAuth client | QIU-owned Google application credentials and exact registered callback; required before live Google sign-in |
| Callback / redirect URI | `/auth/callback`, where this server verifies the returned OAuth flow |
| Internal audience | Google app limited to the owning Workspace organization when configured by QIU |
| Scope | Specific requested Google data permission; directory access is separately authorized |
| Integer cents | Stored exact MYR amounts; MYR 10.25 becomes 1025, avoiding floating-point posting drift |
| Proposed budget | Expected income/costs; approval does not make it a transaction |
| Actual account | Evidence-backed event income/expenses sent to SLD for review |
| Budget variance | Difference between the planned items and actual amounts, requiring explanation |
| Ledger | Immutable actual rows posted when SLD approves event accounts after event end |
| Opening balance | One-time SLD-approved starting amount with its source/reason |
| Atomic posting | Report approval and all ledger rows commit in one database transaction |
| Exact-once posting | Stale/repeated approval fails; the same report cannot increase/decrease the balance twice |
| Event-only capability | Permission for one assigned event, without club-wide access |
| Heatmap | Calendar day cells shaded by actual event/action counts; not random performance data |

Revision: 2026-10-08. These terms describe this implementation rather than extra product features.

| Term | Meaning in this system |
|---|---|
| SLD | Student Life Division; the university team managing clubs and approving records |
| Club context | The club selected for viewing proposals, progress and activity |
| Committee | People assigned positions within a club, including the four mandatory officers |
| Role | Permission to act; club roles are scoped to that club |
| Authentication | Proving who signed in |
| Authorization | Checking whether that identity may perform this action on this club |
| OAuth | Google's delegated permission process for access to selected services |
| OpenID Connect / OIDC | Verified identity information supplied through Google sign-in |
| Hosted domain | The university domain claim required for QIU accounts |
| PKCE | Login-code protection binding the code to the initiating client flow |
| State / nonce | Random login values checked to prevent substituted/replayed authentication |
| Session | A temporary signed-in context stored on this server |
| Cookie | The browser's opaque session identifier; JavaScript cannot read this HttpOnly cookie |
| CSRF token | A secret bound to the session required for website mutations |
| API | Structured endpoints used by the website to read or change data |
| JSON | The structured request/record format exchanged with the server |
| HTTP status | Response category, such as 401 sign-in needed, 403 no permission or 409 conflict |
| Autosave | Background delivery of edited draft data without a Save button |
| Debounce | Briefly wait after input to avoid one request for every keystroke |
| Serialized saves | Finish one save before sending the next, preserving revision order |
| Revision | An increasing record version; stale revisions are rejected |
| Optimistic concurrency | Let editors work, then reject a save if another editor changed the record first |
| Snapshot | A frozen copy of submitted content |
| SHA-256 digest | A content fingerprint binding a signed review to that snapshot |
| Audit/activity log | Server-recorded history of relevant actions with actor, record and time |
| Pagination | Fetch a limited page rather than every history/contact record at once |
| Atomic transaction | Several database changes either all succeed or none do |
| SQLite | The local relational database engine |
| WAL | SQLite's write-ahead log supporting database consistency and concurrent readers |
| UTC / MYT | Recorded universal time / Malaysia display and planned-event time, UTC+8 |
| Deadline exception | An SLD-issued, expiring club permission to submit inside the lead window |
| SDG | One of the UN's 17 Sustainable Development Goals, selected from a controlled list |
| Directory | University-maintained Google identity/contact records exposed by permissions |
| Intake | Admission year and month encoded in QIU student IDs |
| DOCX | Word's document package; the supplied layout is retained during proposal filling |
| PDF | A generated fixed-page document for download and review |
| XLSX | Excel workbook format; used for the event budget |
| ICS / iCalendar | A calendar interchange file containing approved events |
| CSP | Browser policy restricting allowed scripts, images and other resources |
| HTTPS | Encrypted transport needed for the hosted operational system |
| Reverse proxy | A hosting service in front of the application handling HTTPS and connection controls |
| Backup / restore | A consistent saved database / verification that it can be recovered |
| Preview persona | A clearly fictional account used to test the local workflow |
| Production | The university's real operational deployment, subject to verified release prerequisites |

### Proposal form safeguards

| Term | Meaning in this system |
|---|---|
| Derived duration | Read-only elapsed time calculated from planned start/end values; it is not an editable recorded timestamp |
| Wizard gate | Required-field checks on each preceding section before moving forward; incomplete drafts may still autosave |
| Conditional required field | A field needed only when its controlling option applies, such as Other collaboration or requested ICT support |
| Idempotent creation key | A per-draft UUID scoped to actor/club so retrying a lost creation response recovers the same draft instead of creating another |
| Creation replay | Returning the original draft identity; current unsaved entries must still pass a normal revisioned save before being marked saved |
| Scheduled proposals | All proposals with valid planned dates, across draft/review/approval states; these counts do not post financial transactions |

### Hosting and notification terms

| Term | Meaning in this system |
|---|---|
| WSGI | Standard Python web-server interface; the hosting server calls the application without the localhost development server |
| Passenger | Application process manager used by enabled cPanel Python hosting |
| MySQL protocol / MariaDB | Application connects through PyMySQL; Exabytes advertises the compatible but separate MariaDB product |
| InnoDB transaction | Groups a workflow's database writes so failed approval does not leave partial financial postings |
| Advisory mutation lock | Shared database lock serializing revision checks and writes across application workers; correctness ceiling, not measured throughput |
| Fernet-encrypted session | Short-lived server session stored encrypted using a protected key shared by the workers |
| Revocation tombstone | Marks an old session unusable so another request cannot recreate it after sign-out |
| Scoped notification | Recipient-specific alert whose club/event permission is checked again before listing, counting or marking read |


### Operational reports and assistant terms

| Term | Meaning in this system |
|---|---|
| RAG | Retrieval-augmented generation; generate an answer from currently permitted retrieved excerpts |
| Grounded search | Deterministic record-based answer without a generative provider; distinct from a live RAG answer |
| BM25 | Local lexical ranking using term frequency, document frequency and document length; no embedding index |
| Corpus projection | Selected readable fields from authorised records; omits file bytes, signatures and tokens |
| Source whitelist | Server-issued evidence IDs and local task links; the model cannot invent an accessible task |
| Current-access recheck | Verify permission and unchanged source projection after generation and before returning an answer |
| Four-stage attestation | President, Secretary, advisor and SLD sign the same report version in separate ordered slots |
| Frozen signer assignment | Capture the required Secretary/advisor at submission, while still checking current assignment before signing |
| Causal schedule validation | Actual report ends before server now; optional next meeting follows activity and action deadlines are valid |
| AGM handover | Separate once-only SLD application of an approved new committee, not an automatic effect of report approval |
| Past scheduled | Event end has passed but the proposal alone does not prove actual completion |
| Actual completion evidence | Approved reported activity or approved actual event accounts; distinguish evidence from elapsed planning dates |
| Logbook | Professional table of server-recorded actions, actor/role, submitted version, review reason and integrity digest |
| Static source reference | Generated function/import/path inventory for navigation; not proof that every runtime path was tested |
| Deep link | Local task route to a club/proposal/report/event/actual accounts; current permission is checked on opening |

## Profiles and annual reporting terms
- Public projection: a deliberately limited approved-record view; it grants no operational permissions.
- Profile ID: an opaque stable reference used for a published person without exposing their university email.
- Annual report year: the AGM obligation year, separate from actual meeting date and semester metadata.
- Committee snapshot refresh (rebase): revision-guarded replacement of a stale editable AGM's current outgoing roster; historical signed versions remain unchanged.
- Chat source fingerprint: SHA-256 of the permitted source excerpt; changed source/access hides a saved response instead of silently showing stale private content.
- Item receipt association: evidence IDs belonging to one actual income/expense row; upload/save races must retain that row association.
- Auto-applied filter: selection/input updates results without a separate Apply action; text requests may debounce and discard older responses.