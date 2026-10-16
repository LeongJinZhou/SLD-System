# SLD system assessment — 16 October 2026

Project: `C:/Users/QIU/Documents/AI Project/SLD Program`.

Evidence: the existing audit and linked prior assessments establish the documentary baseline. Only checks explicitly listed under this renewed assessment are fresh; prior runtime results are not relabelled as current. This is not operational acceptance.

## Verdict

**A substantial local operational prototype worth keeping, but not yet an accepted official university service.** The next step is stabilisation and end-to-end acceptance, not a wholesale rewrite or an invented completion percentage.

The most accurate architecture description is a **coupled modular backend with a monolithic frontend**. Separate authentication, storage, reports, finance, withdrawals, evidence, profiles, notifications and assistant modules exist. Their central application/helper dependencies and concentrated frontend make changes harder to isolate. This is maintainability debt, not proof that every workflow is broken or that the intended population will overload it.

## What is valuable

- Server-side per-club/event authority rather than trusting displayed titles.
- Revision conflicts, submitted snapshots, ordered signatures and server timestamps.
- Reasoned returns and review history instead of silently editing signed records.
- Actual-money approval and ledger posting designed as one atomic, once-only operation; proposal budgets do not change balances.
- Broad local functionality across registration, proposals, weekly/AGM reporting, handover, completion evidence, actual accounts, exports and scoped supporting views.

These are source/documentary architecture strengths, not a security certification or a fresh execution of every route. Preserve them during cleanup.

## Important issues and release gates

| Priority | Issue | Required action |
|---|---|---|
| Before pilot, F01 | Withdrawal PDF validator uses undeclared `pypdf`; hosting diagnostic also omits it. | Complete clean-install dependency/diagnostic and valid/invalid PDF tests. |
| Before pilot, F01/F10 | 3 MiB raw withdrawal file becomes 4,194,304 base64 bytes, exceeding the 4,000,000-byte JSON request cap before overhead. PDF checks use an assertion removed by optimized Python. | Align limits; explicit validation and actual HTTP/optimized-mode boundary tests. |
| Before pilot, F02 | Registration accepts a client-supplied signing display name beside trusted actor identity. | Canonical authenticated signer attribution for new signatures; preserve historical records. This is not demonstrated privilege escalation. |
| Baseline/rebuild, F03/F04 | Version/status history is hard to reconcile; legacy document packager has obsolete expectations and can overwrite output before validation. | One current status register and isolated reproducible document builds; retain dated history. |
| Financial reliance, F05 | Withdrawal settlement, unused advances, corrections/refunds and cash/deposit reconciliation are incomplete. | Finance-approved rules and traceable exact-once settlement; never count transfer and expense twice. |
| Operational handover, F06 | Annual archive omits the rendered withdrawal form. | Include existing renderer output and verify agreed complete manifest; ZIP is not a backup. |
| Maintainability, F07/F08 | Frontend concentration, central routing and formatting-dependent test loaders. | Fix test-loader fragility before formatting; extract one domain at a time with unchanged contracts. |
| Rollout, F09/F10 | Real identity, exact host/engine/renderer, downloads, restore, browser and capacity acceptance remain outstanding. | Controlled staging and representative five-club pilot with recorded expected/actual results. |

Current source anchors and bounded prior verification are documented in [STABILISATION_PLAN.md](STABILISATION_PLAN.md) and [MYSQL_EXABYTES_REVIEW_2026-10-16.md](MYSQL_EXABYTES_REVIEW_2026-10-16.md). Historical intermittent Windows Word/PDF download resets remain unresolved; no new reproduction or clearance is claimed here.

## Missing business outcomes matter more than screen count

1. **Membership → verified payments → semester report → AGM member list:** there is no authoritative membership/payment collection module completing this chain.
2. **Outdoor event → participants → consent/emergency information → participation eligibility:** an approved proposal does not establish indemnity completeness.
3. **Withdrawal → transfer evidence → actual spending → unused return → settlement:** the ordered withdrawal route is not complete financial reconciliation.
4. **Completion evidence + accounts + obligations → event closure:** photos and approved accounts are separate reviews, not a comprehensive closure gate.
5. **Approved-event amendment/cancellation → reapproval/calendar/consent/refunds:** agree downstream effects before implementation.
6. **Staff/template lifecycle and retention → reliable historical access/output/recovery:** administrative settings and an annual ZIP do not settle these responsibilities.
7. **Reporting obligations → overdue tracking; handover → unfinished duties:** missing-report rules require deadlines/exemptions, while tasks spanning officer changes need explicit ownership/reassignment. See the full [workflow/dependency matrix](MYSQL_EXABYTES_REVIEW_2026-10-16.md) and [W01–W18 audit](review/QIU_SLD_Project_Audit_2026-10-15.md); this summary does not supersede either.

Drive provisioning, live Calendar synchronization and email/push are not implied by internal calendar records, ICS links or in-app notices. Optional assistant retrieval/generation is not university-approved external AI use.

## Database and hosting

Official production targets MySQL-compatible storage and rejects SQLite/preview configuration; SQLite remains local preview/migration. Generic JSON records are persisted in database tables, rather than a normalized club/member/payment schema. Many integrity relationships consequently depend on application code.

Database-wide write serialization, broad scans, embedded base64 files and synchronous archives/PDFs deserve measured workloads. They are not observed capacity failures. Do not weaken transactions or redesign schema without evidence and a reversible migration plan.

The actual Exabytes account, database engine and renderer are unverified. MariaDB is not Oracle MySQL. University identity, HTTPS, private storage/secrets, a real MySQL backup restore and named support ownership remain launch gates.

**HOST-002 remains blocked:** obtain the exact Exabytes product/plan/control panel and whether Oracle MySQL specifically is required rather than compatible MariaDB, then collect approved staging evidence. Do not send credentials. **UI-001 remains open:** UI implementation and rendered responsive/keyboard/signing/accessibility acceptance are outstanding; source assessment is not WCAG conformance.

## Recommended sequence

1. Agree pilot scope and a single current feature/status baseline; preserve W01-W18/F01-F10 and existing UI work.
2. Close F01/F02/F04/F06 with focused regression and clean-install evidence; investigate download reliability separately.
3. Strengthen brittle test loaders, establish a fresh regression baseline, then format/extract incrementally. Keep formatting and functional changes separate.
4. Run controlled university staging for identity, host/database/renderer, revoked access, concurrent saves/reviews, exports and restore/rollback.
5. Complete membership, consent/evidence/closure, settlement and administration/integration packages under agreed SLD/Finance/ICT policy.
6. Accept representative five-club end-to-end scenarios, then expand based on measured workload and operational support.

## Evidence for this renewed assessment

COO read the existing project records, full supplied audit context and current stabilisation/MySQL reviews. Focused read-only backend/frontend reviews are integrated below. No application code, templates or operational data is changed by this assessment. No preview restart, installation, deployment or browser-permission workaround was performed. Previous broad Python/MySQL/render results remain dated historical evidence.

### Fresh backend source verification

Read-only backend specialist `ses_ebd3324ecffeyT4OD8W9X02eqN` verified 12/12 selected existing source/sidecar manifest statuses and both SHA256 hashes, then checked corresponding original lines. API1.7 is current (`server.py:636`). Authentication/Origin/CSRF/session revalidation (`server.py:916–986`), per-club/event scope (`server.py:341–354,535–542`), withdrawal signature/version stages (`withdrawals.py:15–32,105–181`), production guards (`storage.py:153–170`) and transactions/shared encrypted sessions (`storage.py:89–147`) were confirmed statically.

F01/F02/F06 and the upload-cap/assertion issues remain present in selected source: `requirements.txt:1–8`, `tools/hosting_check.py:19–22`, `withdrawals.py:135–146,220–222`, `server.py:1174–1186,921–925`, `evidence.py:384–399`. Remote database encryption remains conditional on topology/configuration (`storage.py:16–31`); no actual plaintext connection is established. No backend imports, engine, clean installation or runtime tests were performed by the specialist. These checks do not certify all workflows or security.

### Independent documentary review

QA reviewer `ses_ebd322a9cffeaxAjSnJVAvhVWk` accepted the documentary direction, not application readiness. COO resolved its requested clarifications: explicit UI-001/HOST-002 statuses, opening provenance and links retaining reporting-obligation/handover-duty gaps. Reviewer did not re-audit source, validate hashes or run tests/browser/accessibility checks. Final specialist-result integration is the COO's responsibility.

### Fresh frontend source verification and selected controller checks

Read-only frontend specialist `ses_ebd3305fbffekKl924SpgSSRvU` verified the app.js source/sidecar hashes and complete manifest status. Fresh measurements: **306,232 bytes, 488 physical lines, 301 named function declarations**, longest line **9,868 characters**. Fifteen of the nineteen existing Node suites contain physical-line function extraction. Formatting without fixing those loaders can break the harness even when application behaviour is unchanged.

Additional source findings, retained under F07/F10 rather than renumbering the audit:

| Source | Observation and bounded impact | Next check/fix |
|---|---|---|
| `web/app.js:20,111–120,130` | Shared shell rendering, cross-domain navigation/save coordination and polling concentrate change impact. | Stabilise test seams, then format and extract separately. |
| `web/app.js:327–330,358,456` | Shared signing canvas requires pointer movement; focusability alone is not keyboard signing. Registration offers a typed preview alternative (`:41,149`), so keyboard signing is not universally absent. | Agree university-approved accessible alternative, then verify real keyboard/assistive interaction. |
| `web/app.js:130` | Async ten-second interval has no poll-in-flight/generation guard and swallows failures. Slow overlapping responses create a source-supported stale-state risk, not a reproduced incident. | Single-flight/stale-response regression and visible non-destructive refresh-failure feedback. |
| `web/app.js:316` | Financial queue partial failures are warned only if no events are returned; successful results from another club can conceal an incomplete queue. | Show partial results plus explicit incompleteness/retry; add mixed-success/failure controller regression. |
| `web/app.js:22,371,488` | In-memory navigation/task query links have no pushState/replaceState/popstate contract in this file. | Define Back/refresh/deep-link expectations and verify in browser when permitted. |
| `web/app.js:452` | Extra literal `}` occurs in withdrawal markup after the event date. | Inspect rendered effect when permitted; minor template correction with regression. |

Positive frontend patterns include escaped text/safe error output, same-origin CSRF requests, restricted task links/image URLs, serialized save/recovery guards and explicit final-submission confirmation. Their presence is not universal XSS or accessibility certification.

Fresh commands run by the frontend specialist from the project root, after inspecting the selected suites for side effects:

```text
node --check web/app.js
node tests/test_autosave.js
node tests/test_recovery.js
node tests/test_workspace.js
node tests/test_sld_confirmation.js
```

Syntax and **4/4 selected Node suites passed**, each exit 0. Their DOM/API/storage/timers are mocked; this is not a fresh nineteen-suite run or browser test. CSS lacked a selected Markdown sidecar and was not substantively reassessed; contrast/tokens/layout/mobile/scrolling/actual focus behaviour remain unverified. No files or application data were changed by these checks.

COO documentary checks: ledger parses with original IDs retained, source audit still has 18 workflow headings and 10 finding rows, report sections/explicit blockers are present and all relative Markdown links resolve. These validate the assessment artifact, not application behaviour.

Final independent QA reread the integrated report and accepted it as a bounded documentary assessment with no material issue. No source/runtime checks were rerun by QA. ASSESS-001 is verified for assessment delivery only; UI-001 remains open, HOST-002 blocked and original business/release gates outstanding.
