# Profiles, chat and annual reporting

This increment extends the existing Python/MySQL operational system. Original form templates remain the export sources. Public browsing uses separate projections and never grants edit/sign/finance permission.

## Personal and club profiles

Each authenticated person has My profile: captured name, Google photo and available university fields, with club positions and published event assignments. Login refreshes the Google-provided photo; a missing photo uses a neutral fallback. A directory snapshot cannot override the more recent captured login identity. Live university Google field/photo completeness still requires staging verification.

Browse clubs lists approved registered clubs with logo, category and description. Opening a club shows its public profile, committee hierarchy and advisor, published upcoming/ongoing events and approved weekly activity summaries. Selecting a person opens a distinct public personal profile with suitable identity, programme and public club/event associations. Public responses exclude email, full student ID, internal review history, signatures, attachments and financial balances. They do not expose unapproved club registrations or private event proposals.

Weekly summaries record completed activity; they are not invented future meetings. Upcoming weekly meetings derive only from a future next-meeting date/time entered in an approved weekly report and are labelled scheduled. Future club events come from the existing approved calendar. A committee member uses their assigned operational workspace to edit documents or see accounts; browsing a club does not confer those rights.

## Floating assistant and saved history

The bottom-right launcher opens compact chat; Expand opens the full assistant page. Both views use the same account-private server history. A successful answer is saved with server time, question, response and fingerprints of the permitted source excerpts. Existing scope still applies: ordinary students ask about public upcoming events; committee/advisor uses assigned records; SLD uses all current operational records.

History is persistent across server restart and is not stored as provider conversation memory. Every question retrieves fresh permitted records. Opening history rechecks every source fingerprint; changed records or removed access hide the previous question, answer and links and prompt a fresh question. The ID/time remain so the entry can be deleted. This conservative rule favours current access and evidence over displaying a stale answer. General no-source questions remain account-private and displayable.

Delete removes one owned entry; Clear history removes only the current account's entries. A foreign entry ID returns the same not-found response as a missing entry. No client-held transcript is forwarded to generation. Optional external generation remains separately configured as documented in ASSISTANT_SETUP.md.

| API | Contract |
|---|---|
| GET /api/profile | Current user's full captured profile and public associations |
| GET /api/public-clubs?q=text | Approved club list with safe hierarchy/photos |
| GET /api/public-clubs/{id} | Safe club detail, upcoming events and weekly summaries |
| GET /api/public-students/{profile_id} | Published participant identity and public associations; opaque ID |
| GET /api/assistant/history?offset=0&limit=30 | Own entries, total and pagination; response availability rechecked |
| POST /api/assistant/query | Existing question contract; successful response includes history_id |
| POST /api/assistant/history/delete | Own id or all:true; returns deleted count |

## Annual AGM and weekly activities

AGM reports are annual, with an explicit report_year from 1900 to 2100. The actual meeting date remains separate: a delayed annual report can refer to an earlier reporting year. Semester metadata is retained for other forms. Legacy AGM year derives from its actual date without rewriting signed evidence. The generated AGM SESSION field uses the annual year when present, with legacy semester fallback.

Only one AGM record per club/reporting year may exist. Continue a returned/draft record rather than create a duplicate. The SLD annual tracker lists all current approved clubs for the selected year, distinguishing Missing, Draft, Returned, Pending signature stages and Approved. A draft is not a submitted report, and a signed submission is not final approval. Current approved-club tracking is not a reconstruction of historical club existence.

Weekly activities have a separate workspace and no annual report year. AGM and weekly reports retain the same President → Secretary → Advisor → SLD four-person signature chain. An approved AGM requires a separate SLD handover action to change committee authority.

SLD's weekly tracker shows current approved clubs for the selected Monday-to-Sunday week, actual report count, approved count and the most actionable report status. No report recorded means missing evidence for that period, not an invented attendance or overdue obligation. Multiple approved weekly activities remain separate records. Proposal/finance follow-up uses existing event review/account queues because those obligations are per event rather than one report per club/year.

If an editable AGM's frozen outgoing roster becomes stale, the current committee can explicitly Refresh committee snapshot. The server checks the viewed revision and draft/returned status, updates the current snapshot, and retains prior history and immutable signed versions. Submitted/approved records cannot be rebased. This allows one annual record to recover without creating a duplicate or rewriting earlier attestations.

| API | Contract |
|---|---|
| GET /api/agm-tracker?year=YYYY | SLD only; approved clubs, per-club report status and aggregate counts |
| GET /api/weekly-tracker?week_start=YYYY-MM-DD | SLD only; normalized weekly period, club report counts and actionable status |
| POST /api/club-reports/{id}/rebase | Current committee, stale editable AGM, viewed revision; refreshed decorated report |

## Signer identity and dates

Student committee designation is Club name · Position. For proposal preparers with an event committee assignment, designation uses that event's position. This display context never grants signing rights: President or Vice President remains the sole eligible proposal preparer; weekly/AGM submission remains President only. Advisor and SLD metadata use their authenticated/trusted role and department. Name/designation/department are filled by the server, not retyped by the signer. Recorded date/time is assigned when signing and cannot be edited; the UI shows readable Malaysia time. Earlier signed identities remain frozen after later profile or assignment changes.

## Financial items and filters

Actual event accounts list income/expense items with description, amount, proposed-budget reference and supporting receipt links. Upload receipts against their respective item and retain the scoped evidence ID in that row. Draft changes autosave. Submission still validates receipts, totals and variance explanations; SLD approval after the event alone updates the club balance. Proposed budgets never post money. Uploaded receipt bytes remain private and retain upload actor/server time/hash.

Filter selections apply immediately. Text inputs debounce to avoid excessive requests; older responses must not replace newer selections. Filtering/navigation must preserve outstanding form edits and wait for pinned receipt operations and autosave rather than losing an evidence association.

## Verification boundary

HTTP tests cover public projection privacy, distinct profile access, photo refresh from stored login identity, contextual signing, annual duplicate/legacy tracking and stale-roster recovery. Chat tests cover restart persistence, cross-account denial, own deletion/pagination and changed-source redaction. Node controller tests cover widget/full-page sharing, safe history rendering, filter changes, role navigation and receipt save races. MySQL integration verifies cross-worker history persistence/deletion as well as existing storage/session/finance guarantees. These checks do not establish live Google directory completeness, rendered browser behaviour or Exabytes deployment readiness.
