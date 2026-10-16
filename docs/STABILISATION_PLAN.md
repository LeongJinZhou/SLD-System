# SLD source-backed stabilisation plan

Prepared 16 October 2026. Scope: document-only discovery following the supplied project path. No application code changed, tests executed, preview restarted, data inspected or live university service accessed. This is a bounded static review, not a full re-audit or pilot approval.

## Baseline and evidence

The original business baseline remains PRD.md and the dated audit at `docs/review/QIU_SLD_Project_Audit_2026-10-15.md`. Preserve W01-W18 and F01-F10, including planned membership, indemnity, settlement, administration and integrations. The separate concise QIU_SLD_Solution remains intact. Historical test results remain historical.

A read-only backend specialist inspected current source and returned these findings to the COO (native task session `ses_ebd92fdbdffeLv1J9I7J4FYKG3`). This is source evidence, not an independent runtime verification.

| ID | Current source evidence | Bounded conclusion |
|---|---|---|
| F01 | withdrawals.py:135-146 imports pypdf inside upload validation; requirements.txt:1-8 omits it; tools/hosting_check.py:19-22 omits its check | Dependency/diagnostic gap confirmed. Clean-install failure not reproduced. |
| F02 | web/app.js:41,149 supplies signing_name; server.py:1174-1186 accepts name; exports.py:124-130 displays recorded name; canonical reviewer_profile exists at server.py:601-603 | Registration attribution remains client-supplied beside trusted actor metadata. Not demonstrated role escalation. |
| F03 | server.py:636-637 identifies API1.7; PRD.md:2-4 and readiness header identify1.6; SPECIFICATION.md:3 identifies1.4 | Conflicting current-facing status confirmed. Old counts do not certify current behaviour. |
| F04 | tools/package_review_docs.py:10-24 targets old requirements pack, asserts R01-R73/18 pages/five images and copies QA PDF before validation; current requirements Markdown opens as concise solution | Obsolete packaging assumptions confirmed. Existing binary page counts and a runtime failure were not rechecked. Do not execute blindly: it can overwrite output before failing. |
| F06 | evidence.py:384-399 includes withdrawal JSON/support/history but no rendered form; withdrawals.py:220-222 provides withdrawal_pdf | Source omission confirmed. Actual ZIP/renderer not exercised. |

## Ordered implementation packages — proposed, not executed

| Order / IDs | Intended owner and files | Acceptance evidence required |
|---|---|---|
| 1 / F03,F04 | COO/document tooling: PRD.md, PLAN.md, MEMORY.md, docs/SPECIFICATION.md, docs/PRODUCTION_READINESS.md, tools/package_review_docs.py and document entry points | One current status register with explicit source/local/external evidence; dated historical sections retained. Choose/retire old packager without replacing concise solution or audit. Build and validate in isolated output before publication; verify final documents and manifest, not just source text. |
| 2 / F01 | Backend: requirements.txt, tools/hosting_check.py, withdrawals.py, focused dependency/upload tests | Select compatible pypdf version from actual runtime testing, not an invented pin. Clean isolated installation; hosting diagnostic detects missing dependency; valid Finance/receipt PDFs accepted; malformed/encrypted/empty and oversize uploads rejected appropriately. Keep access gates. |
| 3 / F02 | Backend + frontend, disjoint ownership: server.py canonical registration review; web/app.js read-only identity; tests/test_registration.py and export regression | Forged/omitted client name/title/department/date cannot alter new trusted signer. Correct advisor/SLD stages, revisions, first-open lock, returns and export attribution pass. Do not rewrite historical signed records. Confirm drawn-signature handling without silently inventing legal policy. |
| 4 / F06 | Evidence/export owner: evidence.py and archive/export tests | Reuse withdrawal_pdf through existing archive add() size/hash accounting. Deterministic tests cover form PDF, supporting evidence/history, manifest integrity, foreign-club/year exclusion, permissions and size limits. Separate real-render long-text/Unicode/signature check; missing collected modules remain explicit. |
| 5 / F07,F08 prerequisite | Test tooling then frontend/backend domain owners | Repair line-based JavaScript function extraction before formatting. Establish current regression baseline; formatting-only change separate from behaviour changes; extract one domain at a time with unchanged contracts. No schema/locking redesign in this package. |

### Existing regression anchors (inspected, not run)
- F01: tests/test_withdrawals.py:29-37 upload fixtures and access boundaries.
- F02: tests/test_registration.py:63-94 review/edit/lock/return checks; tests/test_events.py:61 export fixture. Add explicit canonical signer spoofing assertions.
- F03: tests/test_profiles.py:65 expects API1.7. Add current-status consistency checks rather than downgrading the API.
- F06: tests/test_evidence.py:54-61 deterministic archive assembly/privacy and tests/test_lifecycle_review.py:49-59 immutable version inclusion; add withdrawal fixture. Real render anchor tests/test_withdrawals.py:47-52 currently writes QA artifacts, so isolate execution output.
- Formatting risk: test_login.js:5, test_finance_controller.js:5, test_proposal_signatures.js:5, test_report_signing.js:3, test_operation_signing.js:1 and test_photo_controller.js:1 extract individual physical lines. Other marker/block loaders also need stable boundaries. No formatter before these contracts are addressed.

## Remaining scope and gates

- F05 / W09-W10,W15: Finance-approved settlements, cash/bank custody, reconciliation, refunds and corrections before financial reliance. Withdrawal cash movement is not an additional expense.
- F07-F08: preserve access, stale-write handling, autosave recovery, server timestamps, immutable signed versions and atomic exact-once posting during incremental extraction.
- F09: measure realistic autosave/review/export workloads before altering global mutation guarantees, base64 storage or synchronous archive/PDF processing. Population targets are not capacity measurements.
- F10: real authorised Google fields/session/revocation, chosen Exabytes runtime/MySQL/HTTPS/renderer, reliable downloads, backup restore, rollback and named operational owners remain separate staging gates.
- W15-W18 remain distinct policy-led packages. Membership, indemnity and external integration credentials/scopes must not be invented to fill gaps.
- Prior browser refusal remains in force. No alternate browser/tool workaround; rendered keyboard/mobile/signing acceptance is still unverified.
- Intermittent Windows document-download resets remain unresolved; use an isolated reproducible diagnostic before a networking patch. Source/controller checks cannot clear this observation.

## Next action

Independent QA reviewed this plan against the intake/current scope and accepted documentary consistency with no material finding (native task `ses_ebd904bb5ffeiXKzrgRtuL4F7a`). That review did not independently re-audit application source or execute tests, and is not operational acceptance.

Proceed with the smallest bounded implementation package when implementation is requested: F01 dependency/diagnostic closure is independent of Finance/ICT policy. Keep F03/F04 baseline cleanup separate from application changes; never run the destructive legacy packager as a discovery command. No deployment, full rewrite or blanket production-readiness claim follows from this plan.
