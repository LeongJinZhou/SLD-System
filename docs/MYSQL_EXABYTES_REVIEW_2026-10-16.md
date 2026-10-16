# QIU SLD: MySQL, Exabytes and connected-workflow review

Review date: 16 October 2026. Source root: `C:/Users/QIU/Documents/AI Project/SLD Program`.

## 1. Overall verdict

**Keep and stabilise this project. It is a substantial operational prototype, not yet an accepted university service.** Its useful foundations are server-controlled roles/time, revision conflicts, immutable submitted versions, ordered review and atomic actual-money posting. Do not discard these to get a cleaner interface.

The supplied API1.7 audit is a sound planning baseline. The large frontend and central application create maintenance debt, but separate business modules genuinely exist. “Coupled modular monolith with a frontend monolith” is more precise than either “everything is spaghetti” or “ready for unrestricted growth.” No reliable overall completion percentage follows from screen counts.

This review preserves W01–W18, F01–F10 and UI-001. It supplements, rather than replaces, the [full audit](review/QIU_SLD_Project_Audit_2026-10-15.md), [stabilisation plan](STABILISATION_PLAN.md) and separate concise stakeholder solution.

## 2. Is the database MySQL?

**Production is designed to use a MySQL-compatible database; this review does not establish a live Oracle MySQL connection.** Do not confuse these statements:

| Question | Assessment |
|---|---|
| Does production storage implementation exist? | Yes: `storage.py`, `mysql_schema.sql`, production/session guards and explicit migration tooling exist. |
| Should official deployment use SQLite? | No. SQLite is the local preview/migration source; retain it without importing fictional data into production. |
| Is choosing MySQL enough to prove production mode? | No. Explicitly set `SLD_ENV=production` and `SLD_STORAGE=mysql`; production settings and application identity/HTTPS/session configuration must be checked together. |
| Does this prove the currently running preview or Exabytes account uses MySQL? | No live process/database/account was inspected. |
| Have earlier engine tests been reported? | Project records report isolated MariaDB 10.11.14 checks on 8–9 October. Those are historical, not a fresh engine test here. |
| Is MariaDB exactly Oracle MySQL? | No. MariaDB is a distinct MySQL-compatible product. Exabytes' public cPanel page advertises MariaDB. If Oracle MySQL specifically is mandatory, arrange and test that exact engine; do not relabel MariaDB. |

### What the database structure means

Business information is predominantly serialized JSON in LONGTEXT fields in a generic `records(kind,id,data)` table, alongside audit/log and session tables. That is real database persistence, not a conventional normalized set of club/member/event/payment tables. Many relationships, state rules and uniqueness conditions consequently live in application code rather than foreign keys.

Keep approval and ledger posting in one transaction. The shared mutation lock is a deliberate consistency protection, but serializes writes across clubs; broad record scans, base64 evidence and synchronous archive/PDF work are capacity concerns to measure, not proof of observed overload. Do not replace the locking/schema just to make the architecture diagram look cleaner.

### Production proof still required

On an approved staging account, record the actual engine/version, InnoDB/utf8mb4/schema, transaction rollback, shared-session/revocation behavior, stale/concurrent approvals and exactly-once ledger outcome. Use controlled staging fixtures. **Never run the disposable `tests/test_mysql.py` suite against the university's real database.**

Fresh isolated guard checks in this review rejected production SQLite and production preview. A mocked MySQL initialization failure propagated without falling back to SQLite. No database was opened; these verify fail-closed branches, not a functioning MySQL server. WSGI additionally requires exact production/MySQL settings and returns a redacted 503 if initialization fails (`wsgi.py:24–37,56–65`).

Database TLS is configured only when `MYSQL_SSL_CA` is supplied (`storage.py:27–30`); production mode alone does not require it. Establish local/private versus remote topology; require verified TLS for a remote database and check negotiated encryption privately. Session encryption is not whole-database encryption: business records, receipts and bank information also need protected storage/backups and retention controls.

## 3. Can it run on Exabytes?

**Conditionally feasible; the purchased account is not verified.** A supported Python application host is needed, not merely a place to upload static files or a PHP database.

Public evidence fetched for this review:

- [Exabytes cPanel specification](https://www.exabytes.my/web-hosting/cpanel-web-hosting/features) lists Python 3.12.x and MariaDB 10.11.x, with account resource quotas. This is an advertised offering, not QIU's account specification.
- [cPanel Application Manager documentation](https://docs.cpanel.net/cpanel/software/application-manager/) requires the provider to enable the feature and install Passenger; its environment-variable interface needs the appropriate module. Python language availability alone does not establish WSGI availability.
- Provenance and bounded excerpts: `.agency/exabytes-primary-sources-2026-10-16.md`.

| Exact-account prerequisite | Acceptance evidence / reason |
|---|---|
| Supported Python and dependencies | A clean virtual environment installs/imports the complete runtime requirements; developer-installed libraries must not hide omissions. |
| WSGI hosting | Passenger/Setup Python App or an ICT-managed WSGI service runs `passenger_wsgi:application` / `wsgi:application`; do not expose the development listener as production. |
| Database engine and privileges | Confirm Oracle MySQL versus MariaDB; InnoDB, utf8mb4, required JSON operations, named locks and transactions work with the assigned account. |
| Original-format PDF rendering | Linux LibreOffice/soffice, fonts, subprocess execution and writable temporary space permitted; render real long-text/Unicode/signature templates. This is a major shared-host uncertainty. |
| Dedicated HTTPS origin | Mount at domain/subdomain root, e.g. `https://sld.qiu.edu.my/`; current guide does not support deployment beneath `/sld`. Verify proxy/cookie/OAuth behavior. |
| Private application and secrets | Application/data/config outside public document root; no preview databases, `.agency`, `.tools`, test artifacts or credentials served publicly. |
| Shared encrypted sessions | Stable private session encryption key and production settings identical across workers, with controlled secret backup and revocation tests. |
| University identity/outbound network | Exact Google callback/origin, authorized users, directory scopes/fields/photos and approved outbound endpoints work. |
| Capacity and reliability | Confirm CPU/RAM/process/request/database/packet/time limits; exercise simultaneous autosaves, reviews, uploads, large archives and original-format PDF/Word downloads. |
| Operation and recovery | Named owner, monitoring, logs, rollback and demonstrated MySQL backup restoration; `tools/backup.py` is SQLite-only, not a production MySQL backup. |

If the existing shared plan cannot execute the renderer or host WSGI, use an approved Exabytes VPS/server configuration or an approved compatible rendering service. A VPS offers deployment control but still needs an ICT operator, security updates and measured sizing. No purchase, remote configuration or new external rendering service is authorized by this assessment.

Operator starting point remains [EXABYTES_HOSTING.md](EXABYTES_HOSTING.md). `python tools/hosting_check.py --connect` is for the authorized account after private configuration; it is a bounded diagnostic, not complete launch acceptance. Do not paste passwords, OAuth secrets or encryption keys into chat.

## 4. What is genuinely there, and what is lacking?

These business classifications reconcile the supplied audit and project records. They are not a fresh execution of every route.

| Classification | Areas |
|---|---|
| Substantial local implementation | Registration grants/reviews; per-club/event permissions; proposals/signatures/policy; weekly/AGM reports; handover; completion photos; actual accounts; public/self profiles; internal calendar; in-app notifications; scoped retrieval/history. |
| Partial | Withdrawals as a complete financial process; annual archives; authoritative membership content in AGM; supporting quotations/attendance/survey/post-mortem; event closure; live assistant generation; staff administration; signature consistency. |
| Planned / no complete operational module | QR membership and payment collection/reconciliation; indemnity collection; withdrawal settlement and financial corrections/refunds; automatic Drive; live Calendar synchronization; template administration. |
| External acceptance outstanding | Real QIU Google/directory/photos; exact Exabytes stack and engine; renderer/downloads; backup restoration/rollback; measured load; rendered desktop/mobile/keyboard/signing/recovery; legal/operational signature acceptance. |

In-app notifications are not email/push delivery. ICS/add-event links are not synchronization. A submitted photo is not a complete event-close package. An annual ZIP is not a backup or retention policy. A configured assistant is not approved to send real university records to a provider.

## 5. How the workflows depend on each other

```text
Verified identity + current roles (W01/W18)
  -> one-time registration + approved club (W02)
     -> proposals + review (W04)
        -> internal calendar/public schedule (W11)
        -> participant consent/attendance [missing or partial W16]
        -> completion evidence (W08) + actual accounts (W09)
           + withdrawal settlement [missing link from W10]
           -> comprehensive event closure [not complete]
     -> membership/payments [missing W15]
        -> authoritative AGM member snapshot (W06)
           + semester membership reporting (W15)
        -> collections/deposits reconciliation [missing]
     -> weekly/AGM reporting (W05/W06)
        -> explicit handover (W07) -> current access changes
All workflows -> revision/return/recovery (W03), notifications/audit (W12),
                 permission-safe views/assistant (W13), exports/archive (W14).
Drive/live Calendar (W17) and admin/template/retention/recovery (W18)
remain explicit packages, not implied side effects of approval.
```

### Missing end-to-end links and decisions

These are documented requirements/decision gaps, not newly reproduced defects. Accountable roles below are proposed owners for confirmation.

| Link that must be completed | Why it matters | Owner / observable gate |
|---|---|---|
| Membership → AGM and semester report | A manually entered count is not an authoritative member register. Membership/payment/officer status are different. | SLD + Finance: agreed periods, duplicates/unpaid/waivers/refunds; a dated member snapshot traces to verified records and reconciled collections/deposits. |
| Outdoor proposal → participant permission | Approval of the event does not prove every participant supplied required consent. | SLD + university safety/privacy authority: coverage/guardian/deadline/blocking rules; missing consent and restricted emergency access tested. |
| Withdrawal → expenses → settlement | Received funds can remain unspent, partly spent or returned. A transfer must not become a duplicate expense. | Finance + SLD: request/approval/receipt/expenditure allocation/unused return/variance settle with immutable correction history. |
| Event amendment/cancellation → downstream records | Date/budget/location changes may affect signatures, consent, calendar, costs and refunds. | SLD + Finance + ICT: approved change matrix and scenarios before/after transfer/expenditure; preserve old approvals, update current outcomes without duplication. |
| Evidence + accounts + settlement → closure | “Past scheduled”, “completed with evidence”, “financially approved” and “closed” are different. | SLD + Finance: explicit checklist, due dates, exceptions and missing-item dashboard. |
| Reporting obligation → overdue dashboard | No report does not automatically establish a violation. | SLD: applicability, deadline, exemption and escalation rules for weekly, annual and semester obligations. |
| Handover → unfinished work | Secretary guards do not settle every pending money/review duty or officer vacancy policy. | SLD + Finance: ownership/reassignment matrix; tasks spanning overlap deadline retain valid current authority without changing old signatures. |
| Template revision → historic exports | Uploading a new document cannot safely remap arbitrary fields or change signed output. | SLD template owner: review mapping/rendering before activation and retain version-specific historical exports. |
| Annual archive → records retention/recovery | ZIP completeness depends on what was collected; late corrections and sensitive consent/finance records need policy. | SLD records/privacy + ICT: year cutoff, manifest, access, retention/deletion/holds, size-limit handling and tested recovery. |
| Integration failure → follow-up/retry | Approved event cannot imply a Drive folder/synchronized calendar exists. | ICT + SLD: owned credentials, visible failure, idempotent retry, access removal and create/update/cancel contracts. |

Cross-cutting: every new module must use current authorization, server timestamps, revision guards, reasoned returns, renewed signatures, safe autosave/recovery, scoped notification and access-rechecked links. Assistant answers and public profiles must never become alternative approval/authorization paths.

## 6. Priorities: retain the existing finding IDs

### Additional source-confirmed omissions found in this review

Fold these into F01/F10 rather than silently renumbering the existing audit:

1. **Withdrawal upload limits disagree:** `withdrawals.py:140` accepts up to 3 MiB raw content, while `server.py:921–925` caps the whole JSON request at 4,000,000 bytes. A 3 MiB file becomes 4,194,304 base64 bytes before JSON overhead. Some files permitted by the document-level limit therefore cannot reach validation. Align limits and test real HTTP boundary cases. This is a static arithmetic finding, not a reproduced upload failure.
2. **PDF validation relies on an assertion:** `withdrawals.py:145` uses `assert` to require an unencrypted, nonempty PDF. Python optimization removes assertions. Use explicit rejection and test normal and optimized Python. No unsafe document was uploaded here.
3. **Hosting diagnostics are not schema/renderer certification:** `tools/hosting_check.py:47–50` checks table names, not engine/keys/charset/lock behavior; renderer path detection is not an executed conversion. Its template check covers the proposal, but deployment must retain all report/withdrawal templates. Extend acceptance accordingly.
4. **Migration has narrower guarantees than a full cutover process:** `tools/migrate_mysql.py:16–31` validates/imports records and logs and refuses a nonempty target for those tables, but does not check sessions emptiness, automatically remove fictional data or reconcile source/target hashes. Use a consistent backup/quiesced approved source, dedicated clean target, explicit session invalidation and verified counts/digests. No migration was executed.

Backend source review also reconfirmed F01 (undeclared pypdf), F02 (client-entered registration signing name alongside trusted actor identity) and F06 (archive lacks existing withdrawal PDF renderer output). These remain unfixed. F02 is attribution integrity, not demonstrated role escalation; F01 clean-install failure was not reproduced.

| Gate | Findings / response |
|---|---|
| Before pilot | **F01:** declare/test pypdf and diagnostic coverage in clean install. **F02:** canonical registration signers without rewriting history. **F03:** one current status register. **F04:** fix/retire obsolete document packaging safely. |
| Before financial reliance / complete archive | **F05:** Finance-approved settlement, reconciliation, corrections/refunds. **F06:** include rendered withdrawal form and agreed complete archive manifest. |
| Maintainability | **F07/F08:** repair formatting-dependent test loaders first, then separate formatting from behavior changes and extract one frontend/backend domain at a time. Preserve all authority, signature and transaction contracts. |
| Capacity and rollout | **F09:** measure lock contention/scans/evidence/export workload. **F10:** actual university identity, exact host, engine, renderer, reliable downloads, restore, browser and load acceptance. |

UI-001 remains open: improve the institutional application in place, with action-first dashboards and consistent forms/reviews/tables. Visual renewal is not completion of missing business processes. Historical browser refusal is not silently revoked.

### Recommended delivery sequence

1. Confirm exact host/engine requirements and pilot scope while consolidating the current status baseline.
2. Close isolated F01/F02/F04/F06 defects and establish a fresh reproducible regression baseline; investigate intermittent downloads without speculative networking patches.
3. Establish controlled staging with the actual MySQL engine, university identity, renderer, private deployment and restore/rollback evidence.
4. Deliver membership/payment authority, then consent/supporting evidence/closure and Finance-approved settlement in bounded packages. Agree amendment/cancellation and reporting rules before implementing their enforcement.
5. Complete admin/template/integration lifecycle under university-owned credentials/scopes. Refactor incrementally with regression protection rather than postponing every defect until a rewrite.
6. Accept the five-club pilot with representative current/revoked/incoming/outgoing roles, then scale using measured workload and named support ownership.

No launch date, effort estimate, zero-bug promise or automatic compatibility with every Exabytes plan is asserted.

## 7. Evidence and verification boundary

- COO loaded agency-coo, markdown-ingest and agency-quality-gate, with Project Shepherd/Reality Checker guidance. Read-only backend and product reviews returned evidence. Independent QA accepted the assessment with no material blocker; its minor W06/W15 wording clarification was corrected. This is assessment acceptance, not operational approval.
- Twelve selected source files received fenced Markdown sidecars; their manifest status, source SHA256 and sidecar SHA256 matched. First ingestion stopped on an incorrectly named migration path; rerun used the actual `tools/migrate_mysql.py`. No extraction failure is labelled complete.
- Fresh `node --check web/app.js` passed; 23 application/tool Python files compiled in memory using `python -B` without bytecode output. These establish syntax only, not complete behavior or browser quality.
- Isolated in-process guard checks passed: production rejects SQLite, production rejects preview, and mocked MySQL initialization failure never opens SQLite. No database or network connection was made by these checks.
- Provider/cPanel pages were freshly fetched. No purchased hosting account, production database, Google identity, bank transfer or external AI generation was accessed.
- No application code, templates, operational data or preview service changed. No clean dependency install, full regression run, MySQL engine test, browser rendering or deployment acceptance performed in this assessment. Historical broad test counts remain historical.

### Source anchors and review provenance

| Claim | Current source / evidence |
|---|---|
| SQLite default, fail-closed production selection | `storage.py:153–170` |
| Database TLS, schema, transaction lock and encrypted sessions | `storage.py:16–31,51–62,89–147`; `mysql_schema.sql:1–23` |
| Server mutation/identity checks | `server.py:279–286,665–738,953–976`; `auth.py:118–152` |
| Registration attribution | `server.py:1174–1186`; `exports.py:124–130`; `web/app.js:41` |
| PDF dependency/assertion and request cap | `withdrawals.py:135–146`; `requirements.txt:1–8`; `tools/hosting_check.py:19–22`; `server.py:921–925` |
| Archive form omission | `evidence.py:384–399`; existing `withdrawals.py:220–222` renderer |
| Migration and diagnostic limitations | `tools/migrate_mysql.py:16–31`; `tools/hosting_check.py:31–50` |
| Prior F03/F04 and test-loader evidence | `docs/STABILISATION_PLAN.md:11–34` (prior static review; not a fresh packaging run) |

Native read-only backend reviewer: `ses_ebd61c899ffefGo6Xwrlk3OhEn`; product dependency reviewer: `ses_ebd6162c0ffeO2vV1ylyNgNgpk`. Backend inspected source/sidecars without runtime tests; product review was documentary, not code verification. COO spot-checked original production guards, WSGI, upload/assertion and diagnostic lines and performed the explicitly listed fresh checks.

Independent QA: `ses_ebd5cc567ffeCQjMxR6pIdpvIU` spot-checked raw source/sidecars and requirement coverage; no runtime checks were independently rerun. HOST-001 and MAP-001 assessment criteria are verified within these boundaries; HOST-002 exact-account compatibility remains blocked on account/staging evidence. UI-001 and original delivery gates remain open.

**Next input:** the existing Exabytes product/plan and control panel (or a screenshot with sensitive details hidden), plus whether Oracle MySQL specifically is required rather than compatible MariaDB. No secret credentials are needed to answer this.
