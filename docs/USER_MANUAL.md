# QIU Student Life — user manual

Updated: 2026-10-09. This manual covers the implemented local prototype, including actual event accounts. Membership/payment collection, Drive and indemnity collection remain planned.

## Role workspaces and notifications

Students start with assigned clubs/events and financial records they can access. Advisors start with their endorsement queue, followed by assigned clubs/events. SLD navigation groups operational review/inbox, club/event records/calendar, and contacts/activity/settings. One identity may still have committee and advisor duties in different clubs; screens and actions retain each club's permission checks.

Open Notifications from the header or navigation. Its badge shows your current unread count. Notifications cover new assignments and meaningful submissions, reviews, corrections and deadline permissions; routine draft autosaves do not send repeated notices. SLD receives review items that need its action. Use Mark as read or Open record; read time comes from the server. Opening a submitted registration as SLD starts the existing review lock. Removed assignments stop access to related historical notifications. Inbox counts and records refresh; pagination applies only to your permitted notifications. Email or phone push delivery is not implemented.

The interface uses document scrolling. Background updates and row additions retain position/focus; opening another page or record deliberately starts at the top. Wide budget tables have their own horizontal scrolling area. Long content should wrap within the page. Browser/mobile/keyboard behavior still needs rendered acceptance; controller tests do not certify every viewport.

## Access and account profile

Open the Student Life website and choose Continue with Google once university sign-in is configured. Use your @qiu.edu.my account. Your name, email and available Google photo refresh at login; directory fields depend on university access and maintained data. Your profile shows where the information came from. Missing fields are labelled rather than invented. Staff use department rather than student programme.

If Google setup is pending, open the setup guide below the Google button. Follow [GOOGLE_SETUP.md](GOOGLE_SETUP.md), then use tools/start_google.ps1 with your privately downloaded Web-client JSON and actual SLD email allowlist. No secret belongs in chat or the website. The default launcher keeps seven fictional test roles below Google and uses the test database; it does not turn the prototype into an official deployed service.

For local testing, the preview sign-in screen provides these fictional accounts without passwords:

| Button/persona | University email | Intended test role |
|---|---|---|
| President / Student | demo.student@qiu.edu.my | Assigned president |
| Vice President | demo.vice@qiu.edu.my | Assigned vice-president |
| Secretary | demo.secretary@qiu.edu.my | Assigned secretary |
| Treasurer | demo.treasurer@qiu.edu.my | Assigned treasurer |
| Advisor | demo.advisor@qiu.edu.my | Assigned advisor |
| SLD staff | demo.sld@qiu.edu.my | All-club administrator |
| Student / visitor | demo.visitor@qiu.edu.my | Unassigned student; public events and assistant only |

These are not real Google accounts or production credentials. Officers receive committee access only when their email is actually assigned to a club. If no clubs are shown, SLD must create the registration assignment or the president must include that officer in the club committee. One person may have different roles in different clubs; use the club selector and role badges to check your current role.

## President: register a club once

1. SLD first assigns the club name, semester, president and advisor.
2. Sign in as that president and open the available registration assignment.
3. Enter the biography, logo and committee. President, Vice President, Secretary and Treasurer are mandatory and must be different officers. Extra positions are allowed.
4. Check the save indicator and completion gauge. Registration changes save automatically. Allow the logo to finish reading/uploading before leaving.
5. Submit the completed registration. The advisor reviews and signs, then SLD reviews.
6. Before SLD first opens a submitted registration, committee edits remain possible but require renewed advisor review. Once SLD opens it, the record is locked. A return for correction reopens it; approval opens the reusable club profile.
7. Use Export registration PDF to download the current report. An unapproved export remains an unapproved record.

Creating the first record consumes the one-time permission. It does not allow creating additional clubs. The assigned club identity is not editable by the student.

## Committee: prepare an event proposal

Required fields have a red asterisk and accessible required labels. Complete the current section before Next or a later section tab will advance; Back remains available. A validation summary links to missing fields and retains your entries. Draft autosave still accepts incomplete work. A recovered editor with incomplete earlier sections returns to the first incomplete section.

Start/end dates and times automatically calculate the event duration in Malaysia time, including overnight and multi-day events. Duration cannot be edited directly. Collaboration can be None, one or more registered approved clubs, or Other with its partner name. Collaboration does not give the partner access to the record.

Select ICT/Maintenance only when requested and describe the request. This can include virtual streaming/platform support. Physical logistics and transport details appear only when relevant; unchecking logistics or switching to Virtual clears those inactive details. If you select Others for event nature, explain it. Budget rows need descriptions, nonnegative unit prices and positive quantities; an event without income/expenses can leave both tables empty.

1. Select your approved club and open Event proposals, then Create proposal.
2. Complete Overview, Programme and Budget/export sections. Club information is reused automatically.
3. When applicable, choose SDGs from the named list of 17 goals; no SDG numbers need to be typed. SDGs are optional.
4. Enter future event dates and start/end times in Malaysia time. Recorded creation, submission and signature times cannot be edited.
5. Enter activities, itinerary, audience and expected participants. Add at least two distinct objectives in their numbered order. Search the directory to select event committee members, then assign positions and responsibilities. Names/IDs are resolved from available trusted data. Uncheck ICT/Maintenance or logistics when unnecessary; the original-format export shows Not applicable. Use the checklist to find incomplete sections and remove unused empty rows.
6. Changes save automatically; no Save button is required. Wait for All changes saved before closing the browser. Navigating within the website, exporting or submitting flushes pending changes first.
7. The 0–100% gauge describes required fields. Reaching 100% does not mean SLD approval or a deadline exception.
8. The President or Vice President selects Sign & submit, draws a signature and confirms the read-only identity. Other committee members can prepare drafts but cannot sign this slot. The server checks the current day policy, required fields and your club authority. Normally submission must be at least 14 days before the event; SLD can change that policy.
9. If an urgent event is inside the deadline, ask SLD to issue an expiring permission for your club. SLD permission allows submission while valid; advisor and SLD review still follow.
10. A submitted proposal is read-only. If returned, correct it and submit again. The deadline is checked again. An approved proposal remains immutable.

Use Word/PDF exports for the original proposal layout and Excel for the budget. Review the final document: long entries can expand tables and move page breaks. Submitted exports include an approval evidence appendix and signatures in their respective original approval cells. Outdoor events require indemnity, but collection and completion tracking are not implemented yet.

## Advisor: review and sign

1. Sign in as the advisor and select an assigned club.
2. Open a registration or proposal labelled Advisor review.
3. Read the saved record. Use export if a document is needed.
4. For proposals, verify the automatically captured name, designation and department, then draw your signature. These identity fields are read-only. Registration uses its separate signing controls.
5. Choose Sign & send to SLD. Signing applies to that submitted revision, with a server-recorded date.
6. To request changes, give a clear reason and choose Return for correction. Committee access reopens.

Advisor-only access allows reviewing rather than editing a committee's proposal content. If you are also a committee member in another club, choose that club to use its committee functions. You cannot endorse your own committee club as its advisor. If another person changes the record, reload and review the latest version before signing again.

The reported proposal review Not found issue was traced to an older running server process. Use the current running API version 1.5; an old preview process must be restarted after backend changes. A genuinely missing record or removed assignment can still produce an access/problem message; the system explains it rather than fabricating a successful review.

## Assigned student dashboard and event access

Overview shows your manageable clubs and assigned event work. A university account can hold different positions in different clubs and events. Select the relevant club or event before acting. Club committees can draft their club proposals; the President or Vice President signs and submits. An event-only committee member can collaborate on its draft and prepare its approved event's actual accounts, but cannot change event assignments, submit the proposal or see the club's other records and balance. Advisors see their assigned clubs and review submitted proposals. SLD can switch all clubs. Removing an assignment removes access immediately on the server.

## Club finances and activity

Open Club finances for an assigned club. The displayed balance is its SLD-approved opening balance plus approved actual income minus approved actual expenses. If no opening balance is recorded, the interface states that; it does not invent existing funds. Proposal approval alone never changes the balance. Expand an event to see planned versus actual totals and its approved ledger transactions.

Monthly and yearly financial graphs use the month/year when SLD approved actual transactions. Finance contains money and expandable event transactions. Operational activity heatmaps are in Performance and the club calendar, separate from finance. Event-only members see their event accounts without a club-wide balance.

## Organiser: reconcile actual event accounts

1. Open an approved event's financial report. Proposed budget items remain visible as reference.
2. Upload a receipt or supporting file for the event: PDF, PNG, JPEG or WebP, maximum 2 MB each. Online income can use payment/deposit evidence; cash income can use a collection record. These are reviewed evidence, not automated bank verification. Downloads require current event access.
3. Add actual income/expense rows, descriptions, MYR amounts with at most two decimal places, matching budget items (or Unplanned), and evidence references for every transaction.
4. Explain any variance, including changed budget items and unplanned spending. Financial reports currently use an explicit Save draft button; proposal forms continue to autosave. Draft evidence and amounts do not affect the balance.
5. Submit the report to SLD. It becomes read-only while awaiting review; a correction return reopens it. A stale version requires loading the current saved version rather than overwriting another organiser's edits.
6. SLD reviews and either returns it with a reason or approves it with a typed name. Approval is blocked until the event's scheduled end, and posts the actual transactions once. Server records actor, time and submitted-version digest. Approved reports and postings cannot be edited or approved again.
7. Export the financial report PDF from the report. It contains planned/actual totals, variance, transactions, evidence references and actual review history. This is a system report; no original template for this actual-account workflow was supplied.

SLD records a club's opening balance once with its amount and source/reason. SLD should verify this amount first. The current prototype has no correction, refund, transfer, bank integration, membership fee collection or zero-transaction closure workflow. Cash deposits must not be re-entered as fresh income if the collection was already recorded. Existing immutable approvals must be corrected through a later controlled adjustment workflow, not deletion.

## SLD: dashboard, policy, permissions and calendar

1. Use the dashboard to follow available registration assignments, incomplete records and pending review queues. Select a club to narrow the context; SLD can select all clubs.
2. Issue a registration assignment using university emails for the president and advisor. Only that assigned president can create the registration once.
3. Open submitted registration review to record the first-open lock. Approve only after the advisor endorsement, or return with a reason.
4. Review proposals in SLD review. Signing approval freezes the record and automatically creates its event in the system calendar.
5. In Settings, enter the minimum proposal lead time in days, from 1 to 365. The default is 14. Changes affect new submissions and resubmissions; historical submissions retain their recorded policy.
6. Select a club for urgent permission, enter a reason and future expiry, then enable it. Revoke it with a reason when no longer needed. The permission does not authorize past events or final approval.
7. Open the calendar for approved events. Use the Google event link to add one event or export the ICS file for import. These actions do not establish live synchronization with your Google account.

Created/submitted/reviewed/signed/audit dates remain server-only even for SLD. Administrative settings are intentionally distinct from immutable evidence. Privileged-account lifecycle and editing already-approved committee terms still need their separate administration module; the current system does not expose arbitrary historical edits as settings.

## SLD: contacts and profile pictures

Open Contacts to browse available university-directory data. Import fetches all available pages before updating the snapshot. A failed import retains the previous list. In preview mode only fictional contacts are imported.

Filter by programme, full student ID, club assignments, intake year or month. For QIU-202404-007157, the intake is April 2024 and the complete serial is 007157. The last four digits are 7157; use the full student ID for an exact identity match. General search can help locate names, emails or ID fragments.

Photo URLs are imported when Google exposes them. Initials appear when a photo is unavailable. Hidden or missing directory photos cannot be recovered by this website. Club filtering currently lists registered officers/advisors, not an unimplemented general membership list. Live importing requires configured Google credentials, directory scope, and university permission.

## Activity without a long flat list

Choose the dedicated club in Activity. Committee/advisor access is restricted to currently assigned clubs. SLD can select any club or the all-club view. Each proposal appears as a summary group with a count and last action; expand it to see only that proposal's timeline. Registration activity is a separate group. Use pagination inside a long timeline.

Old activity rows that recorded only a club ID remain club-level history because their particular proposal cannot be identified reliably. Timestamps, actor and action are recorded by the server; no signed images or sensitive form payloads are dumped into activity rows.

## Problem recovery

| Problem | Action |
|---|---|
| Field incomplete | Follow the error to its section/field; draft stays on screen |
| Save failed / offline | Keep the tab open, restore connectivity and retry; check saved status before leaving |
| Session expired | Use the recovery action, sign back into the same account and resume; local changes remain isolated until identity and server revision are checked |
| Different account during recovery | Return to the original account; the draft is not uploaded under another person's identity |
| Another member saved first | Keep/copy your edits and reload/reconcile the latest version; stale changes must not overwrite theirs |
| Record missing / access changed | Return to the club list and reopen an available assigned record; SLD can check the assignment/history |
| Deadline passed | Ask SLD about a reasoned, expiring club permission; do not change the recorded timestamp |
| Google directory unavailable | SLD checks directory permission/configuration and signs in again if the token expired |
| PDF generation unavailable | SLD checks the renderer; no fake PDF is returned |

Website autosave is not guaranteed to survive a forced browser/process crash. Keep the tab open until the save indicator confirms delivery. Recovery state contains draft data only, never Google access tokens or drawn review signatures; follow the on-screen account isolation controls.

## Operator: backup and release

Use the configured Python executable to run `tools/backup.py source.sqlite3 new-backup.sqlite3`. This creates a consistent SQLite backup, checks integrity and refuses to overwrite an existing file. Run `tools/backup.py new-backup.sqlite3 --verify-restore` to restore temporarily and check table counts. Schedule and secure backups through the university's hosting operations; scheduling is not configured by this local build.

Read PRODUCTION_READINESS.md before moving from fictional preview to the official service. Tests use isolated databases and do not create real university approvals. See SPECIFICATION.md for API/data logic and WORKFLOWS.md for flowcharts.


## Proposal signing dates and correction

Proposal signatures now appear in three distinct original-table cells: Prepared by (President OR Vice President), advisor Reviewed by (top right), and SLD Reviewed by (previously blank second-row left). Exactly one preparer signs each submitted version. Names, designations and departments are captured from authenticated/trusted profiles; absent directory job titles use the actual application role (Club Advisor or SLD Officer), while absent departments show Unavailable. Dates come exclusively from server signing time and cannot be edited. Returns clear current signatures; immutable earlier signatures remain in history, and corrected submissions require fresh signatures. Printed registrar, bursar and COO cells remain separate and unsigned. If your profile details are unavailable, ask SLD/IT to correct the trusted directory source before signing. Signatures cannot be moved between approval cells. A returned proposal needs a new preparer signature and renewed advisor/SLD review; the prior signed version remains visible in its historical activity.


## Weekly and AGM reports

1. Open Club reports for a current assigned approved club and create Weekly activity or AGM report. Other clubs are not available to committee/advisor accounts.
2. Enter semester, title, completed activity date/start/end, venue and purpose. Future activity reporting is blocked at submission; these are completed reports, unlike planned proposals. Changes autosave and the progress gauge identifies missing fields.
3. For sports weekly activities, enter the attendance list with QIU identities and Present/Absent. For other clubs, enter the minutes/discussion. Optional action rows must be complete; leave decisions or next meeting empty when not applicable. A planned next meeting must follow the reported activity.
4. For AGM, enter objectives, present-and-absent attendance, opening speech, agenda, outgoing committee accomplishments, election results and the new mandatory President/Vice President/Secretary/Treasurer using directory selection. Outgoing committee attribution is captured rather than overwritten.
5. The current President draws and submits. The assigned Secretary signs next, then advisor, then SLD. Each signature card shows its stage, captured identity and immutable server date. A person cannot fill two signatory slots.
6. A reviewer can return with a reason. The correction banner shows who returned it, when, why, and what your role should do next. Committee corrects content; the President signs a new submission and all reviewers sign again. Previous signatures stay in historical evidence.
7. Export Word/PDF at any stage. Unsigned/draft dates remain blank and current signatures only occupy their assigned cells. The professional logbook lists actions, actors, server times, versions and integrity hashes. An unapproved export is not an approval.
8. After AGM approval, SLD separately applies the approved handover. Approval does not silently replace club roles. Current club/report revisions and outgoing roster must match, and pending Secretary work must be resolved before its assigned officer loses access. Handover applies once; new officers receive current permissions and old assignments lose them.

Sports PDF can be generated directly. AGM and meeting-minute PDF use the original Word templates and need the configured converter; Word remains the alternative when unavailable. Long entries can expand tables/pages, so review the final export.

## Performance and club activity calendar

SLD uses Performance to switch all clubs or a dedicated club, year and month. Committee/advisor sees linked clubs; event-only organiser sees only its event. The year heatmap records approved weekly meetings/activities, AGMs and event schedules; select a day to see records and open the task. Monthly totals and active days use actual activity/schedule dates, not autosave timestamps or financial approval dates.

Completed weekly/AGM records have approved reports. A past approved event schedule is labelled unverified/past scheduled until completion evidence exists; passing the end time does not prove it happened. Future, ongoing and completed states remain distinct. Multi-day events appear on each occupied day. An event spanning months counts in each month but only once in the unique record total.

## Student Life assistant and public events

Unassigned students use Upcoming events to browse published approved future/ongoing events, open their public detail and ask the assistant. They cannot see private proposals, reports, finances or signature history. The new Student test button demonstrates this public-only scope.

Committee/advisor questions can use assigned club/event information; an event-only committee member gets its event and accounts rather than the whole club. SLD can ask across clubs. Questions use current permissions; ask again if access or record content changes while answering.

Type a club/event name or question, such as What events are upcoming?, Which reports are returned?, or Show weekly activity reports. Answers show source cards; Open source takes you directly to the permitted club, proposal, report, public event or actual accounts. These links do not grant access. No matching permitted record produces an honest no-results message.

Local grounded search is available immediately. Optional RAG generation is clearly labelled and requires university server configuration; provider failure falls back to grounded results. Up to eight matching excerpts appear and larger matching counts are disclosed. Exact counts are deterministic. The assistant cannot sign, approve or change a record. See ASSISTANT_SETUP.md for administrator configuration and ARCHITECTURE.md for its permission logic.

## Profiles, compact chat and annual reports — 2026-10-09
See [Profiles, chat and annual reporting](PROFILE_CHAT_REPORTS.md) for current profile/public projections, assistant history/deletion, annual AGM tracker/rebase, contextual signatures, per-item receipts and auto-applied filter contracts. This supersedes earlier semester-only AGM assumptions. Public club browsing does not grant private operational access. Browser/live Google/provider/hosting acceptance remains pending.
## Photos, event completion, withdrawals and handover — 2026-10-09

Draft club, proposal, weekly/AGM, completion, withdrawal and actual-account forms save automatically. Check the save status before leaving. A connection or version error retains your entries and blocks navigation until resolved. Drawn signatures remain outside draft autosave and browser recovery.

Weekly activities need at least two distinct photographs; an AGM needs at least one. Open the saved report, upload photographs in **Activity photographs**, then follow President → Secretary → Advisor → SLD signing. Photographs lock during review and reopen after a correction return. SLD can download the photographs as a private ZIP.

Open **Event completion** separately from the proposal and actual accounts. After the approved event ends, enter the completion summary and upload at least two photographs. Submit the completion to SLD using the two confirmation steps; SLD reviews and signs the submitted version. Actual receipts and accounts remain separate, and an approved actual financial report posts the club balance only once. Required event photographs cannot be bypassed by financial approval.

Open **Fund withdrawals** for an approved assigned club. Enter the purpose, amount, optional event context, requested items and payee bank accounts. Item totals and payee totals must match the withdrawal amount. The Treasurer signs preparation, followed by President, Advisor and SLD. SLD uploads the actual Finance-signed PDF/PNG/JPEG, then signs **All Approve**. The server records the transfer deadline (default 14 days). The Treasurer uploads the actual funds-received receipt and signs its linked evidence; SLD acknowledges receipt. A signature alone is not proof of transfer. Withdrawal approval does not itself post money into the actual club ledger.

Before an advisor forwards a club, proposal, report or withdrawal to SLD, or an actual account/completion/received-funds record is sent to SLD, the website shows **Review your submission**, followed by **Confirm submission to SLD**. **Keep editing** or Escape cancels sending. Signer identity and dates come from the authenticated profile and server; users cannot type an approval date.

After SLD applies an approved AGM handover, outgoing and incoming committee access overlaps for the configured period (default seven days). Incoming officers display Pending positions during overlap. The server determines active committee authority after the period ends. Club profiles show the handover deadline and public club profiles offer annual committee history. SLD's annual AGM tracker provides a club/year ZIP download of the retained records and evidence.

SLD manages proposal lead time, AGM handover days and withdrawal transfer days in **Settings**. Proposed deficits need an explicit SLD approval reason; student committees cannot approve their own deficit.

These screens and controllers have local source/Node checks. Rendered mobile/keyboard acceptance remains unverified under the existing browser-access refusal. Production Google identity, live university deployment and external Finance transfer execution are not claimed by these local workflow checks.
