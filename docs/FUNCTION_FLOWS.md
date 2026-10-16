# Function flows and acceptance contracts

This reference connects each implemented feature to the user action, server logic, output and failure handling. SOURCE_REFERENCE.md lists individual functions and source lines. This document describes the complete feature flows rather than suggesting that every helper is a separate product feature. Membership payment intake, indemnity collection, Google Drive folder automation and later ledger corrections remain unimplemented requirements in PRD.md.

## Identity and role navigation

Sign in → validate Google identity and @qiu.edu.my domain → capture available trusted directory fields → establish explicit SLD authority and current club/event assignments → load role dashboard. Directory job title does not confer administrative rights. An ordinary student gets public upcoming/ongoing approved events and the assistant; assigned committee/advisor gets permitted operational work; SLD gets all clubs and administration. Fictional preview personas are separate and do not establish university identity.

Source: auth.py, Handler.session/require_user/verify_mutation_session, App.bootstrap, workspaceNavigation/dashboardPage. Failure: invalid or expired identity returns an actionable sign-in problem; preserve only sanitized same-account draft fields. No Google token or signature drawing enters recovery. Sessions are encrypted/shared in MySQL and revoked/expired state is checked before mutations and after an unlocked assistant generation call.

## Club registration and reusable profile

SLD authorizes club/semester/President/advisor → assigned President creates one draft consuming the grant → committee completes bio/logo/four officers → autosave with revision → submit → advisor signs → SLD explicitly opens submitted record and locks fields → SLD approves → approved reusable club profile. A pending registration edit before SLD first-open invalidates earlier acknowledgement and requires renewed review. A returned registration reopens authorized editing, with the return reason and next action visible. Approval preserves immutable submission evidence.

Source: registration-grant and club branches in server.py; clubForm/flushClub/reviewControls in web/app.js; exports.club_pdf. Every export shows status. After an SLD-applied approved AGM handover, the profile explicitly cites the AGM authority and distinguishes old registration signatures from current committee authority.

## Event proposal authoring and conditional logic

Select an approved assigned club → website defaults club identity → enter planned schedule → duration derives automatically → select nature/SDGs/collaborating approved clubs or Other → fill at least two ordered distinct objectives → choose directory event committee → enter relevant ICT/logistics and budget rows → progress gauge and forward section validation → autosave incomplete drafts without blocking backward navigation → Word/PDF/Excel export or sign/submit.

Source: canonical_proposal, committee_identities, derived_duration, proposal_progress, proposalForm/flushProposal/wizard helpers. A virtual event clears physical logistics; unchecked requests export Not applicable. Collaboration names do not grant record permissions. Client timestamps, status, signing metadata and duration are ignored. Blank/incomplete drafts remain saved; invalid forward movement links to missing inputs without discarding them.

## Event proposal signing and return

One President OR Vice President draws and submits → server checks future event start and inclusive configured lead days/valid club exception → freeze preparer identity, PNG and server time → hash a submitted snapshot without a self-referential digest → pending_advisor → assigned advisor draws/signs same version → pending_sld → SLD draws/signs same version → approved proposal and one calendar event.

Any current-stage reviewer may return with a required reason → returned → current signatures clear → committee sees who/when/why and corrects draft → one allowed preparer signs a fresh submitted version → advisor and SLD sign again. Historical versions and signature records remain immutable. A second preparer, stale revision, self-review or cross-slot signature cannot change the submission. Legacy unsigned submissions require correction/re-signing before approval.

Exports map preparer top-left, advisor top-right and SLD previously blank second-row left, with read-only captured identity and immutable signing dates. Other printed named university signatory slots remain unsigned template text. Source: proposal submit/review branches, preparer_profile/reviewer_profile, proposalSignerBlocks/showPreparedSignature and exports._signature_cells/_audit_appendix.

## Weekly report

Current committee creates weekly draft → enter semester/title, completed date/time, venue, purpose and activity kind → sports requires present/absent attendance; non-sports requires minutes → optional complete decisions and next-meeting plan → autosave/progress → President signs and submits → assigned Secretary signs → assigned advisor signs → SLD signs → approved activity appears on operational calendar.

President, Secretary, advisor and SLD must be distinct signers for each submitted version. Secretary/advisor assignments are frozen at submission and must still be current before signing. Current-stage return requires a reason and sends the record to committee correction; all four signatures must be renewed. Future or nonpositive actual schedules cannot be submitted. Optional action deadlines/agenda/next meeting must be logically valid; incomplete drafts are still accepted.

Source: club_reports.canonical/progress/signing_slot/signer_profile/handle_post, report autosave/signing controllers, exports.club_report_docx/club_report_pdf. Minutes use the retained source sections; sports PDF uses supplied attendance columns. No funds are posted by a weekly report.

## AGM report and handover

Committee creates a semester AGM report → outgoing committee and advisor captured → enter completed AGM schedule/objectives/present-and-absent attendance/opening speech/agenda/outgoing accomplishments/election summary/new officers/adjournment → President, Secretary, advisor and SLD sign in order → approved report is retained and recorded as an AGM activity.

Approval alone does not change assignments. SLD separately selects Apply approved handover with current report and club revisions → verify the frozen outgoing roster still matches → verify mandatory new officers are distinct directory identities → ensure handover will not strand a report awaiting an outgoing Secretary → apply once atomically → update current committee/President ownership → record the approved AGM reference/time/actor → new members gain current access and old assignments lose it. If the outgoing roster changed, create a fresh AGM report; refreshing a revision cannot replace a newer handover.

Source: club_reports.handle_post apply-handover, notifications, App.visible/current assignment checks. Source AGM Secretary Prepared by/President Checked by/Advisor Reviewed by meanings are preserved in export; SLD verification is separate. Attendance status is explicitly labelled under the name and never substituted for POSITION.

## Financial actual accounts and balance

Approved event → authorised organisers upload scoped receipts/supporting evidence → enter actual income/expenses against proposed budget → evidence and variance validation → submit immutable report → SLD returns with reason or approves after event end → approved actual rows post exactly once → approved balance/charts update. Opening balance is SLD-approved once with reason. A proposal budget remains planning data. Event-only organisers cannot inspect club-wide balance or unrelated records.

Source: finance.context/canonical_report/review/club_view/event_view; finance autosave/review controllers and exports.finance_pdf. Ledger posting failure rolls back report approval and entries together. Stale/duplicate review returns conflict. Administrative/audit counts and operational heatmap are not displayed as financial activity.

## Performance calendar and event catalog

SLD selects all clubs or one club and year/month → fetch /api/performance → show approved weekly/AGM occurrences and approved event schedules → day heatmap and monthly counts → choose a day → expand records → open respective scoped task. Committee/advisor views contain current assigned clubs; event-only views contain only assigned events. Ordinary student does not receive private performance records.

Completed weekly/AGM entries have approved report evidence. An elapsed approved event proposal is past_scheduled, not proof it happened. Approved actual event accounts can supply completion evidence. Future schedules and ongoing events remain separate statuses. Multi-day records appear on every spanned day; summary.total is unique records, while monthly totals count one occurrence in every spanned month. The ending midnight is exclusive. Administrative autosave dates and finance totals do not create operational occurrences.

Authenticated /api/public-events and /api/public-events/{id} expose only safe published approved events whose end is still future, including ongoing events. Projection: ID, club name, title, schedule, venue and description. No internal committee, history, signature, cost, receipt or review note. The assistant uses exactly this public projection.

Source: performance.public_events/year_calendar/handle_get, performancePage/public event controllers, safeTaskHref/openTaskHref. Scoped ICS and Google Add-event links remain available; live Google calendar synchronization is not connected.

## Notifications and activity history

A meaningful workflow transition or new assignment → choose linked current recipients and actionable SLD recipients → persist recipient-specific alert → unread badge and inbox → recheck current access on list/read/open → mark read using server time → open scoped record. An unchanged autosave does not generate repeated notifications.

Activity lists group by club/proposal/report with expandable history. SLD sees all operational records; committee/advisor sees assigned club records; event-only identities see only their event. Historical actor identity does not create access after assignment removal. The export logbook lists chronological recorded actions and per-version integrity evidence, separate from current signature cards.

Source: App.log/activity, notifications.emit/permitted/list_for/mark_read, activityPage/notificationsPage and exports._audit_appendix. Alerts and task links do not confer new permissions.

## Settings, deadline exception and contacts

SLD changes lead days (1–365, default 14) with revision → server audits policy/time → next proposal submission uses current policy. SLD may grant/revoke a reasoned future-expiring exception for a club; exact used permission version is frozen with late submission. Exception never approves a proposal, authorizes a past event or bypasses required fields/signatures.

SLD imports all visible Google directory pages outside mutation lock → confirm complete fetch → recheck session/admin permission under lock → atomically replace contact snapshot. Failure retains previous contacts. Search filters include programme, full ID, club and intake; all six serial digits stay authoritative. Last four are a display/search convenience. Photo URLs use approved Google hosts and missing fields remain explicit. Live provider permission/configuration remains a university prerequisite.

## Assistant and internal task links

Question → shared per-account rate guard → build current permitted record projection → tokenize/rank excerpts → deterministic grounded response or explicitly configured generation → validate structured source IDs/plain output → recheck unchanged permitted source projection and session after generation → return whitelisted source links → frontend safely escapes response → task route refreshes permission and opens club/proposal/report/event/finance.

Source: assistant.documents/retrieve/grounded_answer/generate/query, assistantPage/assistantAnswerMarkup/safeTaskHref/openTaskHref. The assistant cannot approve, edit, sign or execute a record. No client transcript is reused as evidence. Unknown/private club filters reject access; no hits are honest; provider failures fall back to grounded records. Provider source IDs must match retrieved IDs and model-generated arbitrary URLs/HTML are rejected. Exact counts remain deterministic. An assignment or source change during generation returns ASSISTANT_CONTEXT_CHANGED rather than delivering stale private content. A logged-out/revoked/expired session blocks the final response.

## API additions

| Method | Path | Permission and result |
|---|---|---|
| GET | /api/club-reports | Current club committee/advisor or SLD; decorated reports |
| POST | /api/club-reports | Current committee of approved club; revisioned partial autosave |
| GET | /api/club-reports/{id} | Current assigned club access; decorated report |
| POST | /api/club-reports/{id}/submit | Current President; completed report and drawn PNG; new immutable version |
| POST | /api/club-reports/{id}/review | Current designated next-stage signer; approve/sign or reasoned return |
| POST | /api/club-reports/{id}/apply-handover | SLD, approved AGM, report/club revisions, matching old roster, once only |
| GET | /api/club-reports/{id}/export?format=pdf or docx | Current scoped report access; source-format or sports PDF |
| GET | /api/performance?year=YYYY&month=M&club_id=ID | SLD all / linked club or assigned event only |
| GET | /api/public-events and /api/public-events/{id} | Authenticated university account; public approved upcoming/ongoing projection |
| GET | /api/assistant/capabilities | Current account scope and truthful generation availability |
| POST | /api/assistant/query | Current account; bounded question/optional assigned club, sources and server links |

Existing API contracts remain in SPECIFICATION.md; SOURCE_REFERENCE.md supplies source locations and dispatch context for all observed API literals.

## Failure handling

| Condition | Outcome | User next action |
|---|---|---|
| Required fields missing | VALIDATION_ERROR and field links; partial draft remains | Complete highlighted fields |
| Stale save/sign/review | Revision conflict; no overwrite or approval | Load current record and review changes |
| Returned form | Reason/stage/time shown, committee correction enabled | Correct and obtain fresh required signatures |
| Stage belongs to another person | No signing capability; server denies mutation | Wait for named next stage or contact SLD |
| Session expired/revoked | Sign-in problem, current private response withheld | Sign in again, same-account draft recovery checks apply |
| Deadline inside policy without exception | Proposal submission blocked | SLD can issue a club-specific expiring exception |
| No PDF renderer for source Word form | Explicit unavailable error; Word alternative | Administrator configures renderer |
| No assistant matches/provider unavailable | Honest no-source or grounded fallback | Refine question/open source records |
| Handover roster/report conflict | Nothing applied | Resolve pending report or prepare current AGM version |

## Verification navigation

- HTTP/permissions and workflow: test_system.py, test_registration.py, test_events.py, test_deadlines.py, test_administration.py, test_event_access.py, test_signatures.py, test_reports.py.
- Operational activity/public projection: test_performance.py; frontend test_operations.js.
- Money/evidence/atomic posting: test_finance.py; actual MySQL integration test_mysql.py.
- Scoped assistant/provider payload/revocation/fallback: test_assistant.py; frontend task routing in test_operations.js.
- Autosave/recovery/signing: corresponding test_*autosave.js, test_recovery.js, test_proposal_signatures.js, test_report_signing.js.
- Export integrity/rendering: test_signature_exports.py, test_report_exports.py, test_portable_pdf.py.
- Infrastructure: test_notifications.py, test_wsgi.py, test_workspace.js and compilation/syntax checks.

A passing regression is evidence for its checked paths, not a promise that every browser, hosting plan, user input or future module has zero defects.

## Profiles, compact chat and annual reports — 2026-10-09
See [Profiles, chat and annual reporting](PROFILE_CHAT_REPORTS.md) for current profile/public projections, assistant history/deletion, annual AGM tracker/rebase, contextual signatures, per-item receipts and auto-applied filter contracts. This supersedes earlier semester-only AGM assumptions. Public club browsing does not grant private operational access. Browser/live Google/provider/hosting acceptance remains pending.