# Workflows and decision logic

## Public profiles, saved chat and annual tracking

```mermaid
flowchart TD
 L[Google sign-in] --> I[Capture current trusted identity and photo]
 I --> P[My profile: current captured fields and assignments]
 I --> B[Browse approved clubs]
 B --> C[Club logo profile and hierarchy]
 C --> E[Published upcoming events and scheduled next meetings]
 C --> S[Open safe public student profile]
 Q[Floating chat launcher] --> W[Compact chat]
 W --> X[Expand to full assistant]
 W --> R[Fresh permission-filtered query]
 X --> R
 R --> H[Save own question answer and source fingerprints]
 H --> V[History reopened: recheck source access and content]
 V -->|Changed| Z[Hide previous content; ask again or delete]
 V -->|Current| Y[Display escaped answer and trusted task links]
 H --> D[Delete own entry or clear own history]
 A[SLD report follow-up] --> G[Annual AGM by reporting year]
 A --> F[Weekly activities by actual activity week]
 G --> T[Missing draft returned pending or approved per club]
 F --> T
```

AGM uniqueness is per club/reporting year. A stale editable outgoing roster can be explicitly refreshed with a revision guard; historical signed evidence is retained. Public profile viewing and saved source links never grant operational permissions. See PROFILE_CHAT_REPORTS.md for exact API contracts.

## Weekly and AGM reports

```mermaid
flowchart TD
 A[Committee creates partial report for approved club] --> B[Autosave revisioned content]
 B --> C{Actual completed activity and required fields valid?}
 C -->|No| B
 C -->|Yes| P[President signs and submits immutable version]
 P --> S[Assigned Secretary signs same version]
 S --> D[Assigned advisor signs same version]
 D --> L[SLD signs and approves same version]
 P --> R[Current reviewer returns with reason]
 S --> R
 D --> R
 R --> H[Keep history; clear current signatures]
 H --> B
 L --> E[PDF and Word: distinct signer cells and verification log]
 L --> F[Performance records approved actual activity]
 L --> G{Approved AGM needs committee handover?}
 G -->|Yes| V[SLD checks report and club revisions and frozen outgoing roster]
 V --> W{Pending Secretary obligations or stale roster?}
 W -->|Yes| X[Explain conflict; apply nothing]
 W -->|No| Y[Apply new committee once; audit authority and refresh access]
```

Four distinct current role holders sign in order. The AGM template's Prepared by Secretary, Checked by President and Reviewed by Advisor cells retain their original meanings; SLD verification is added separately. A corrected version requires all four fresh signatures. Handover never happens merely because the AGM was approved.

## Operational performance

```mermaid
flowchart TD
 A[Select year month and club] --> B[Server filters current permission]
 B --> C[Approved weekly and AGM actual reports]
 B --> D[Approved event calendar records]
 D --> E{Approved actual accounts prove completion?}
 E -->|Yes| F[Completed event]
 E -->|No| G[Scheduled ongoing or past scheduled]
 C --> H[Daily heatmap and monthly counts]
 F --> H
 G --> H
 H --> I[Choose day; inspect labelled occurrences]
 I --> J[Open authorized report or proposal]
```

SLD can select all clubs. Linked committee/advisor views are scoped; event-only organisers see their events. Finance retains money charts; autosave and administrative actions do not fabricate meetings. Elapsed schedules alone are not proof of attendance or completion.

## Returned form and assistant navigation

```mermaid
flowchart TD
 A[Form returned] --> B[Show reviewer stage reason and server date]
 B --> C[Show current role's next action]
 C --> D[Committee corrects autosaved draft]
 D --> E[Resubmit; required signatures restart]
 Q[Authenticated question] --> P[Build permitted projection before retrieval]
 P --> S[Rank matching source excerpts]
 S --> G{External generation explicitly configured?}
 G -->|No or unavailable| H[Grounded local answer]
 G -->|Yes| I[Strict plain answer and retrieved source IDs]
 H --> R[Recheck current records access and session]
 I --> R
 R --> L[Return trusted internal task links]
 L --> O[Click link; fetch current authorized task]
```

Ordinary students receive only safe published upcoming/ongoing events. Assigned committee/advisors receive their records; SLD receives all current records. The assistant has no mutation tools. Source changes during generation block the response rather than exposing stale private context.

Revision: 2026-10-09. Diagrams describe implemented club/proposal/admin, actual event accounts, signed reports, performance and assistant behavior. Membership collection/payments, financial adjustments, indemnity and Drive processes remain planned in PRD.md. FUNCTION_FLOWS.md maps each implemented feature to controllers, API handlers, permissions and failure paths.

## Event assignment and student work

```mermaid
flowchart TD
 A[Assignment or meaningful workflow transition] --> T[Server transaction and audit]
 T --> R[Identify current linked committee and advisor]
 T --> S{SLD review action required?}
 S -->|Yes| D[Include authorized SLD recipients]
 R --> N[Persist per-recipient notification; exclude actor]
 D --> N
 N --> I[Unread badge and scoped inbox]
 I --> C{Current record access still permitted?}
 C -->|No| H[Hide notification and deny read/open]
 C -->|Yes| O[Read timestamp and open assigned record]
```

```mermaid
flowchart TD
 O[Enter Overview and planned schedule] --> D[Calculate read-only duration]
 D --> C[Choose collaboration or conditional Other]
 C --> V{Required Overview complete?}
 V -->|No| E[Linked summary and field errors; draft retained]
 V -->|Yes| P[Programme and relevant support requests]
 P --> W{Required Programme complete?}
 W -->|No| E
 W -->|Yes| B[Budget and export]
 B --> S[Server checks all required content and deadline on submit]
 P --> O
 B --> P
```

```mermaid
flowchart TD
 A[Club committee or SLD selects directory person] --> B[Server resolves email and identity]
 B --> C[Assign event position and responsibility]
 C --> D[Student signs in]
 D --> E[Overview displays assigned event]
 E --> F[Collaborate on draft content]
 F --> G[One President or Vice President signs and submits]
 G --> H[Advisor endorses then SLD approves]
 H --> I[Assigned organisers prepare actual accounts]
 C --> J[No unrelated club balance or records granted]
```

## Actual accounts and approved club balance

```mermaid
flowchart TD
 A[SLD approves event proposal] --> B[Planned budget remains reference only]
 B --> C[Organiser uploads scoped evidence and actual rows]
 C --> D[Save draft without posting]
 D --> E[Validate evidence and budget variance]
 E --> F[Submit immutable version to SLD]
 F --> G{SLD review}
 G -->|Return with reason| C
 G -->|Approve| H{Event has ended?}
 H -->|No| F
 H -->|Yes| I[Atomically approve report and post ledger rows once]
 I --> J[Approved opening plus income minus expenses]
 J --> K[Balance and approval-period charts update]
 I --> L[Approved report and ledger immutable]
```

## Login and club permissions

```mermaid
flowchart TD
  A[QIU Google sign-in] --> B{Verified email and domain?}
  B -->|No| C[Explain sign-in problem]
  B -->|Yes| D[Capture available identity and directory fields]
  D --> E[Look up explicit SLD authority and club assignments]
  E --> F{SLD?}
  F -->|Yes| G[All clubs and administration]
  F -->|No| H[Only assigned clubs]
  H --> I[Select club context]
  I --> J[Apply committee or advisor permissions for this club]
```

An advisor assignment does not change the user's roles in other clubs. Directory Staff classification does not grant SLD approval privileges.

## One-time club registration

```mermaid
flowchart TD
  A[SLD assigns club, semester, president and advisor] --> B[One-time registration grant]
  B --> C[Assigned president creates registration]
  C --> D[Grant consumed atomically]
  D --> E[Committee enters profile and officers with autosave]
  E --> F[Submit snapshot]
  F --> G[Advisor signs and sends to SLD]
  G --> H[SLD opens submitted registration]
  H --> I[Server records first-open lock]
  I --> J{SLD decision}
  J -->|Return with reason| E
  J -->|Approve| K[Approved club profile]
  K --> L[Profile reused in event proposal]
```

Pending edits before SLD first-open invalidate earlier endorsement and require renewed review. Historical signed snapshots remain. SLD cannot approve before advisor endorsement.

## Proposal autosave and session recovery

```mermaid
flowchart TD
  A[Committee enters draft] --> B[Debounced serialized save]
  B --> C{Save result}
  C -->|Success| D[Update revision and completion without replacing newer text]
  D --> A
  C -->|Conflict| E[Retain entries and show reload/reconcile action]
  C -->|Network error| F[Retain draft and retry]
  C -->|Session expired| G[Show sign-in recovery at the problem]
  G --> H{Same account restored?}
  H -->|No| I[Keep draft isolated; do not upload to other account]
  H -->|Yes| J[Fetch latest server version]
  J --> K{Revision unchanged?}
  K -->|Yes| B
  K -->|No| E
  A --> L[Navigation, export or submission requested]
  L --> M[Flush pending save]
  M --> N{All changes saved?}
  N -->|Yes| O[Continue requested action]
  N -->|No| F
```

The gauge measures required fields, not approval. A forced browser close or network failure can prevent final delivery; the saved indicator is the evidence that the server accepted entries.

## Submission policy and urgent permission

```mermaid
flowchart TD
  A[Submit saved proposal] --> B{Approved club and committee or SLD authority?}
  B -->|No| X[Explain access problem]
  B -->|Yes| C{All required sections complete and valid schedule?}
  C -->|No| Y[Focus missing section and retain draft]
  C -->|Yes| D{Event start is in the future?}
  D -->|No| Z[Reject past or started event]
  D -->|Yes| E{Server now within configured day deadline?}
  E -->|Yes| H[Store immutable submitted snapshot]
  E -->|No| F{SLD club exception enabled and unexpired?}
  F -->|No| G[Explain deadline and request SLD permission]
  F -->|Yes| I[Freeze exception evidence with submission]
  I --> H
  H --> J[Assigned advisor review]
```

SLD configures days and grants/revokes a club permission with reason and expiry. Exceptions do not skip required fields or either approval stage.

## Proposal review and calendar

```mermaid
flowchart TD
  A[Pending advisor] --> B{Assigned advisor decision}
  B -->|Return with reason| C[Returned editable draft]
  C --> D[Correct and autosave]
  D --> E[Resubmit and recheck current deadline]
  E --> A
  B -->|Sign submitted version| F[Pending SLD]
  F --> G{SLD decision}
  G -->|Return with reason| C
  G -->|Approve signed version| H[Atomic approved proposal and calendar entry]
  H --> I[Immutable record and scoped activity]
  H --> J[SLD calendar automatically updated]
  J --> K[Google event link or ICS import]
```

Approval uses the viewed record revision and submitted digest. A stale review is rejected. Google linking requires user confirmation; there is no connected live synchronization.

## Activity and directory

```mermaid
flowchart TD
  A[Choose club] --> B{SLD or currently assigned?}
  B -->|No| C[Exclude inaccessible data]
  B -->|Yes| D[Filter activity before counting]
  D --> E[Group by proposal or registration record]
  E --> F[Show summary and count]
  F --> G[Expand matching record timeline]
  H[SLD imports directory] --> I[Fetch all available Google pages]
  I --> J{Complete import?}
  J -->|No| K[Keep existing contacts and explain issue]
  J -->|Yes| L[Atomic snapshot replacement]
  L --> M[Filter by programme, full ID, intake or club assignments]
```

Photo URLs and missing-photo status are imported. Directory visibility is governed by university Google permissions. Club contact filtering means committee/advisor assignments until membership is implemented.


## Proposal signing and immutable dates

```mermaid
flowchart TD
 A[Committee autosaves draft] --> B[One President or Vice President draws signature]
 B --> C[Server freezes preparer identity date and version]
 C --> D[Assigned advisor signs same submitted version]
 D --> E[SLD signs and approves same version]
 E --> F[Export each signature in its distinct original cell]
 C --> R[Return with reason]
 D --> R
 R --> H[Archive signatures and clear current slots]
 H --> A
```

Proposal signatures now appear in three distinct original-table cells: Prepared by (President OR Vice President), advisor Reviewed by (top right), and SLD Reviewed by (previously blank second-row left). Exactly one preparer signs each submitted version. Names, designations and departments are captured from authenticated/trusted profiles; absent directory job titles use the actual application role (Club Advisor or SLD Officer), while absent departments show Unavailable. Dates come exclusively from server signing time and cannot be edited. Returns clear current signatures; immutable earlier signatures remain in history, and corrected submissions require fresh signatures. Printed registrar, bursar and COO cells remain separate and unsigned.
