# Interface and form-logic audit

## Operational workflow increment — 2026-10-09

| Observed defect | Correction and evidence |
|---|---|
| Financial screens mixed money with a decorative activity heatmap | Operational occurrences moved to Performance; financial views retain approved balances and transaction charts. Controller tests verify separation. |
| Returned forms did not explain who returned them or what to do | Persistent reason, review stage, server date and role-aware next action across registration, proposals, finance and reports. |
| Signature controls hid the ordered reviewer and current version | Explicit signer stages and captured identity, one actionable stage, current versus historical signatures separated; drawings excluded from recovery/autosave. |
| New reports could lose edits during save/navigation | Serialized autosave, stale-version detection, in-flight edits retained and submission flush; report controller regression checks. |
| Long report tables lost context across pages | Repeated data-table headers and surplus placeholder-row removal; signature rows kept intact. Actual PDF rendering and independent visual review. |
| An elapsed event plan could look like evidence of a completed activity | Explicit scheduled/ongoing/past-scheduled labels; completion uses approved actual accounts, weekly/AGM occurrences use approved reports. |
| Generic chatbot answers or arbitrary model URLs could obscure evidence | Permission-filtered source excerpts, honest fallback, escaped answer text and whitelisted clickable task links. Ordinary student preview role exercises public-event scope. |

The remaining visual acceptance gap is the rendered browser: scroll behavior, responsive sizing, focus and keyboard interaction are not certified by controller tests. Existing browser refusal is respected. Export pages have been rendered separately and visually inspected.

2026-10-08. Lead: agency-coo. Backend, frontend and independent review passes inspect actual source and regression behavior. Hallmark supplies targeted anti-slop criteria; UI UX Pro Max supplies field-error/focus guidance. Existing institutional typography/colour tokens remain the design direction. This is a source and behavior audit, not a rendered-browser visual certification. Previous browser inspection was declined; no alternate browser workaround was used.

## Concrete bugs and usability defects

| Finding | Evidence / affected location | Correction |
|---|---|---|
| Editable duration could disagree with the event dates | `web/app.js` proposal duration input; `server.py` previously accepted client duration | Read-only live calculation; server derives seconds and readable duration; exports recalculate legacy schedules. Overnight/multiday and forged-duration regression added. |
| Users could jump to later pages with missing mandatory content | `web/app.js` previous `step()` unconditionally changed steps | Validate preceding sections before Next/tab navigation, show a linked error summary and inline messages, keep backward navigation and partial autosave. Submission repeats required checks on the server. |
| Unstructured collaboration required unnecessary typing | Proposal free-text collaboration field | Minimal approved-club selector, None and conditional Other partner text; server verifies IDs and resolves display names. Selection grants no permissions. |
| Irrelevant transport inputs remained available after declining logistics | Proposal Programme support section | Hide/clear physical transport details when logistics is inactive or event is virtual. Optional ICT remains relevant to virtual streaming/platform support. |
| Activity analysis omitted historical registration actions | `finance.py` filtered only explicit `club_id` | Attribute legacy registration/proposal/grant log IDs to their club, before counting. Unrelated account/global actions are not invented as club activity. |
| Draft/reviewing scheduled events were omitted from progress charts | `finance.py` originally counted only approved scheduled proposals | Include all valid scheduled proposal dates with status labels; keep approved-event subset explicit and financial postings approved-only. |
| Conditional required fields and budget rows could appear complete too early | `server.py` proposal checklist | Require selected support/Other descriptions and complete budget rows when present. Empty budgets remain valid for a free event. |
| Client date calculations can normalize impossible dates | JavaScript Date accepts some invalid calendar dates | Validate actual date/time components so the wizard agrees with strict server schedule rules. |
| Hidden Other nature text could remain printed | `exports.py` unconditionally printed the previous description | Server clears inactive Other; exporter also checks the selected nature for legacy records. |
| The club selector remained active after first proposal autosave | First create returned an ID without rerendering the select | Lock the organizing-club select while first creation runs and once its ID is assigned. |
| Retrying a lost first-create response could duplicate a draft | No stable key for proposal creation | Add a stable per-draft creation key, scoped to actor/club; store mapping atomically and replay safely without treating old content as saved edits. |

## AI-slop patterns found in the existing source

| Pattern | Where | Why it does not help this operational system | Adjustment |
|---|---|---|---|
| Generic promotional slogans | Login “Your club. Your campus.”; proposal empty state “Your next event starts here” | An official portal should explain the task and account access directly | Use university/task-specific headings and useful next actions. |
| Repeated informational panels | Proposal header, status notice, completion panel and context panel | Repeating workflow instructions obscures the current action and field requirements | Keep concise state-specific guidance and progressive sections. |
| Decorative completion without navigation enforcement | Proposal progress display alongside unrestricted tabs | A progress bar feels like polish while the underlying task flow remains inconsistent | Connect navigation to real validation and show missing fields. |
| Raw technical status strings | Financial `not_started` fallback | Internal codes make a staff-facing interface feel unfinished | Translate statuses into readable labels and distinguish proposal status from account status. |
| Dense fields shown regardless of relevance | Transport/support fields and unchecked sections | More fields look feature-rich but collect unnecessary or silently discarded information | Reveal only applicable fields; explain Not applicable and preserve useful virtual ICT. |

These are observed copy/structure/logic issues, not claims that every card, blue accent or standard form is AI slop. No invented engagement metrics, testimonials, visual scores or performance claims are used.

## Verification and remaining limits

Latest revamp: role-grouped navigation and a review-first advisor dashboard replace the common undifferentiated menu. SLD has operations, records/calendar and administration groups; students prioritize assigned work. Notification inbox/badges use current scoped server data. Source scroll causes found: full-shell replacement, dashboard rebuilds during polling, focus-induced scroll, account layout stretched by sidebar height, and budget grids wider than the viewport. Same-record rendering restores position/focus/selection/disclosures; polling updates queues/counts in place; record/page navigation explicitly resets; budget overflow stays inside its editor. `tests/test_workspace.js` exercises actual helpers and role/inbox controllers. These corrections are source/controller evidence, not a browser guarantee that all scrolling bugs are absent.

`tests/test_proposal_logic.py` checks actual HTTP duration/collaboration/conditional submissions and original-template output. `tests/test_wizard.js` checks the real pure wizard rules. `tests/test_finance.py` checks all-status scheduled activity, legacy log attribution, permissions and unchanged financial posting rules. Existing autosave, recovery, signing, calendar and export suites guard previous functionality.

Final integration result: all eight Python HTTP/export suites and seven Node controller/helper suites passed, plus Python compilation and JavaScript syntax checks. The independent reviewer reran proposal autosave/replay, wizard and finance-view checks and found no remaining material defect in the changed source. Safe creation retries and inactive Other export text have explicit regression coverage.

Rendered desktop/mobile density, contrast, touch targets, actual focus movement, keyboard signing and responsive layout remain unverified in a browser. Source inspection and mocked HTML cannot close those checks. Live Google identity/directory, production hosting and load acceptance remain separate prerequisites. Membership and indemnity modules remain unimplemented; their activity is not fabricated. AGM and weekly reports now create performance occurrences only after approval.
