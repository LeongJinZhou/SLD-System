# Production readiness and release evidence

Updated: 2026-10-09. This is a release record, not a declaration that the localhost review server is production-ready.

## Latest profile/chat/annual reporting release — API 1.6

Implemented safe public approved club and participant profiles, full self profile with captured photo, shared compact/full chat with persistent deletable account-private history, annual AGM uniqueness/legacy year projection and guarded stale-roster recovery, annual and weekly SLD tracking, recorded future weekly meetings, contextual server-owned student/SLD review identity, receipt-per-item autosave/upload barriers and automatically applied filters. Details and current API contracts are in PROFILE_CHAT_REPORTS.md.

Current checks: 20 Python suites observed passing across the sequential run and targeted reruns after fixes; actual isolated MariaDB/MySQL included cross-worker history/delete and once-only finance approval after the canonical reviewer identity change. All 15 Node suites were run again by root and passed. Python compilation and JavaScript syntax passed. Independent source/HTTP/controller review closed legacy AGM invisibility, stale annual recovery, finance reviewer spoofing, undefined new financial submission ID, receipt race, chat pagination and in-flight typing findings.

Original-format exports passed package/PNG/digest/source-style checks and actual rendering. Root visually inspected updated AGM cover (annual SESSION and full club-position designation) and minutes signatures; no clipping in these fixtures. Browser layout/keyboard/mobile acceptance remains unverified under the prior refusal. Live Google/photo completeness, provider quality and Exabytes deployment remain university staging checks.

Preview API1.6 was reloaded with existing data, and live HTTP checks exercised visitor public club/student/self profiles, own chat save/list/delete and SLD annual/weekly tracking. A Python urllib read of the large JavaScript asset encountered a Windows connection reset; a diagnostic curl download returned HTTP200, complete263577bytes and a hash identical to current source. API requests passed. The intermittent local transfer cause remains unconfirmed; this is not a universal networking/scrolling correctness claim.

## Current operational increment — 2026-10-09

Implemented revisioned autosaved AGM/weekly reports, four ordered distinct version-bound signatures, reasoned returns and renewed signatures, explicit guarded AGM handover, operational performance separate from finance, safe public upcoming events, permission-first assistant retrieval with task links and optional configured generation. Reverse-engineering documentation now includes ARCHITECTURE.md, FUNCTION_FLOWS.md and generated SOURCE_REFERENCE.md.

Verification: all 18 Python suites observed passing across the sequential run and affected reruns, including an actual isolated MariaDB 10.11.14 integration run without skips. All 12 Node suites and JavaScript syntax checks passed. Python compilation passed. Assistant tests use genuine ordinary student and assigned-role HTTP sessions, provider payload stubs, invalid source/URL rejection, fallback and revocation during generation; no live external generation was called. New four-stage report races use SQLite HTTP; the MySQL suite independently checks production storage/session/finance boundaries rather than every new report race.

Signed AGM, minutes and sports PDFs were generated; original source sections, unrelated package parts, embedded current-version signatures, logo substitution, blank-page prevention and continued table headers were checked. Independent review inspected five AGM pages, four minutes pages and three sports pages, finding no remaining clipping/signature/table-context defect in those representative fixtures. This is not a guarantee for arbitrary future entry lengths.

An intermittent Windows connection reset occurred during the initial system PDF download. A targeted response/write diagnostic and the subsequent clean system run passed; its cause remains unconfirmed. No speculative networking patch was made. Deployment load/rendering acceptance remains necessary.

The owned disposable QA database was shut down cleanly; no university records or production service were changed. Browser scrolling/responsive/keyboard acceptance, real university Google directory/sign-in, electronic-signature policy, live model quality and Exabytes runtime/deployment remain external checks. Membership/payment collection, indemnity, Drive provisioning and administrator template replacement remain planned; this release does not silently call them complete.

Latest hosting/UI increment: twelve Python suites and eight Node suites passed, including real MariaDB 10.11.14 migration, shared sessions/transactions, concurrent exactly-once financial approval, notification privacy/read persistence, WSGI routing, portable multilingual PDF and scroll/role/inbox controllers. Broad parallel execution encountered one Windows connection reset during registration PDF download in the event suite; its isolated sequential rerun passed. The parallel-export/runtime cause remains unproven and deployment load acceptance stays open. Independent source review found no remaining material issue in the changed scope. PDF font fallback was rendered and inspected; browser layout/scrolling was not.

## Implemented and locally verified foundations

| Area | Evidence and limit |
|---|---|
| Restricted identity | Google OIDC/domain/audience/nonce/PKCE configuration paths exist; live university sign-in not verified |
| Club access | One-time president grant, per-club committee/advisor roles, server locks and revision checks; real role lifecycle pending |
| Review integrity | Stored submitted snapshots/digests; advisor then SLD; return/resubmit; immutable approval |
| Dates/deadlines | Server-recorded timestamps, future planned schedules, day policy and audited expiring club exceptions |
| Draft safety | Serialized autosave/recovery controller; source/Node tests; actual browser tests pending |
| Audit | Club filtering before grouping/counting/pagination; proposal detail filter; SLD all-club scope |
| Directory | SLD-only complete paginated import, safe photo URLs, full-ID/intake filters; mock API contract checked |
| Data recovery | tools/backup.py uses SQLite backup API and integrity check; isolated backup/temporary restore test passed |
| Preview separation | Preview personas/data separated from live mode; seven fictional roles available, including an ordinary student without committee assignments |
| Export | Original proposal package preserved; actual Word/PDF and budget Excel; sample rendering evidence retained |
| Session handling | Expired sessions pruned; expired mutation returns authentication recovery rather than misleading CSRF failure |
| Event participants | Event-only draft/report/evidence access; no unrelated club balance/profile or proposal submission rights; HTTP scope checks |
| Actual accounts | Private evidence, revisioned reports, budget variance, post-event SLD approval and atomic once-only cents ledger; HTTP/PDF checks |
| Google setup | Public setup guide and local JSON launcher; credentials absent, no live login verified |

Production storage now uses MySQL-compatible InnoDB transactions and a shared database advisory mutation lock across workers; local SQLite preview retains its process lock. Directory network calls are outside that lock; import rechecks the persisted session under the shared mutation lock before replacement. This establishes tested consistency boundaries, not measured capacity for the intended population. MySQL sessions are encrypted in shared storage; local SQLite sessions remain in memory. See EXABYTES_HOSTING.md for hosting requirements and deployment configuration.

Earlier finance increment evidence: seven HTTP suites and six Node suites passed. Finance tests include a deliberately aborted ledger insert (report approval rolled back), concurrent approval (one posting, one conflict), private evidence/event-only isolation, version/variance checks, future-event rejection and financial PDFs with valid long multiline text. Normal financial PDF rendered and inspected. Google guide HTML/CSS served successfully; launcher syntax parsed. These are local correctness checks, not real OAuth, browser acceptance or load certification.

## External prerequisites still pending

| Requirement | Owner / what must be verified |
|---|---|
| University domain/hosting | University IT selects host/domain, service account and HTTPS proxy; localhost loopback server is not public deployment |
| OAuth and directory | University-owned client credentials, redirect URI, People API enablement, authorized scope, admin allowlist and actual maintained-field mapping |
| Directory completeness | Confirm which profiles/domain contacts and photos SLD can access; compare live results to an approved university sample |
| Service operation | Supervised process, startup/restart policy, update/release procedure, diagnostics, monitoring and rollback |
| Backup operations | Storage/access/retention/scheduling plus a real operational restore drill; no schedule or external storage configured |
| Privileged roles | University authorizes initial SLD accounts; audited UI for grant/revoke/admin lifecycle is a later implementation |
| Session operation | MySQL uses encrypted shared expiring sessions and revoked tombstones; verify key custody and real-worker operation on Exabytes. SQLite preview sessions remain in memory |
| UI acceptance | Desktop/mobile, keyboard/focus, signing and session-recovery browser checks; prior browser access was declined and not bypassed |
| Load acceptance | Representative concurrent autosaves/reviews/import/export and intended pilot acceptance; current suites are correctness checks, not load certification |
| Business policy | Confirm signature alternative, later financial authority, retention and club handover/amendment rules |
| Google Calendar | User-confirmed links/ICS exist; live Google Calendar synchronization is not configured |
| Remaining modules | Membership/payment collection, financial adjustments/transfers/refunds/zero-activity closure, Drive, indemnity collection, AGM/weekly reporting, template administration |
| Financial operations | University reconciliation/cash custody and opening approval; file storage/quotas/malware scanning, controlled adjustments and retained evidence |

## Configuration inventory

| Variable | Required use |
|---|---|
| GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET | University Google client credentials, outside versioned source |
| GOOGLE_DIRECTORY_ENABLED | Enables requested directory scope/integration |
| SLD_ADMIN_EMAILS | Explicit authorized university SLD emails |
| SLD_APP_URL | Exact origin/OAuth redirect base; HTTPS deployment base when hosted |
| SOFFICE_PATH | Optional approved LibreOffice renderer path |

The server uses the launching environment and does not silently load arbitrary .env files. `.env.example` lists names without secrets. [Google setup](GOOGLE_SETUP.md) explains tools/start_google.ps1: the default mixed local prototype supports verified Google identities and clearly fictional test roles in preview.sqlite3. `-OfficialMode` disables fictional access and chooses sld.sqlite3, but does not establish deployment readiness. Preview must not be enabled for an official release. Native originals and the retained template stay unchanged.

## Release workflow

1. University IT supplies the hosting/identity configuration and accountable operators.
2. Run the correctness suites and review unresolved findings in PLAN.md.
3. Validate real QIU identity/directory mapping, each role, signed reviews and scoped exports in staging.
4. Verify browser behavior and representative load on the chosen host.
5. Create a checked backup, perform the operational restore drill, and record rollback steps.
6. SLD validates the five-club pilot and signs off policy and manuals.
7. Deploy the verified release with preview disabled, monitor the pilot, and retain observed evidence.

No live contacts, university approvals, external calendar writes or official deployment have been performed as part of local testing. Source references: [Google OIDC](https://developers.google.com/identity/openid-connect/openid-connect), [People directory API](https://developers.google.com/people/api/rest/v1/people/listDirectoryPeople), [Google calendar import behavior](https://support.google.com/calendar/answer/37118?hl=en).


## Proposal signatures: 2026-10-08

Implemented visible drawn signatures for one President/Vice President preparer, assigned advisor and SLD reviewer, with authenticated identity, immutable server dates, revision/digest binding, self-review protection and return/resign history. Original Word/PDF mapped cells are implemented; a representative three-signature PDF was rendered and visually reviewed. Remaining named university approval cells are printed template text, not recorded approvals. This does not establish university acceptance of electronic signatures or live Google directory accuracy. Browser interaction and live university sign-in require authorized verification.

Signature increment checks: all 14 Python suites and nine Node suites passed, including actual isolated MariaDB/MySQL storage/session/finance regression. The new simultaneous preparer test uses real HTTP with SQLite; it does not separately certify signature races on the production host.
## Current review baseline — 9 October 2026
See review/QIU_SLD_Requirements_and_Workflows.md for the full plain-language requirements, current status and SLD/ICT acceptance worksheet. Local lifecycle checks cover photos, post-event completion, deficit reasons, ordered withdrawal approval with Finance/fund evidence and server-timed AGM handover. Root22 non-MySQL suites passed; isolated MySQL regression passed in backend QA; frontend reported19Node suites passed. These are local checks, not production or rendered-browser acceptance. Some Windows Word/PDF downloads intermittently reset their connection; cause remains unresolved and staging download reliability is a release check. Membership/payment collection, outdoor indemnity, Drive integration, live Calendar synchronization and full template/role administration remain planned.
