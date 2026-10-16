# Withdrawal and committee handover backend contracts

API version1.7; all recorded dates/signatures use trusted server time. MySQL mutation scope encloses role checks, revisions, signatures and record writes. SQLite is local preview.

## Withdrawal

`POST /api/withdrawals` accepts `{withdrawal:{club_id,id?,revision?,creation_key?,purpose,amount,event_title,event_date,items,recipients,bank_name,account_name,account_number,contact_name,contact_email,contact_phone}}`. Club committee may autosave editable drafts; only the actual Treasurer signs/submits. Stable UUID creation key retries recover revision1, later changed revision conflicts.

Items: `{description,price,quantity,payment_method}`; nonnegative finite price, positive quantity on submission, exact cents and total equals requested amount. Recipient rows: `{name,email,contact,bank_name,account_name,account_number,amount}`; complete bank account/name and positive amount, sums equal request amount. Legacy single top-level bank account remains supported. Vendor email is not restricted to the university domain. Private bank/contact details never enter public profiles.

Ordered routes, each requires current `revision`:

1. `/id/submit` `{signature}` Treasurer ->pending_president.
2. `/id/review` `{action,signature,comment,confirm_submission}` assigned President ->pending_advisor; advisor ->pending_sld; SLD ->pending_finance. Advisor requires `confirm_submission:true`. Return requires reason and clears current signatures while preserving signed versions/history.
3. `/id/finance-document` SLD `{filename,content_base64}` readable unencrypted PDF or verified PNG/JPEG up to3MB. Stores immutable document bytes/SHA/server actor/time, moves to pending_all_approve. This records a Finance-signed file; there is no Finance login or invented Finance electronic signature.
4. `/id/all-approve` SLD `{signature}` verifies complete package ->waiting_transfer. Server `transfer_due_at` freezes the configured transfer_days default14.
5. `/id/receipt-document` actual current Treasurer uploads the bank-in/transfer receipt PDF or PNG/JPEG, retaining server SHA and submitted-version binding; then `/id/receive` actual current Treasurer `{signature,confirm_submission:true,receipt_document_id}` records actual receipt ->pending_acknowledgement. The deadline never automatically asserts a transfer or receipt.
6. `/id/acknowledge` SLD ->acknowledged.

GET list/detail return `{withdrawals}` / `{withdrawal}`. GET `/id/finance-document` scoped binary; `/id/export?format=pdf|docx` fills unchanged copied original withdrawal template. Captured role identity replaces original printed officers, source account/item sections repeat, drawn signatures bind version/digest. PDF uses configured LibreOffice. No withdrawal status posts a provisional or duplicate financial ledger balance.

Records: withdrawal, withdrawal_version, withdrawal_signature, withdrawal_document (base64 bytes plusSHA/metadata), withdrawal_creation. Bootstrap exposes scoped withdrawals and club.can_create_withdrawals; decorated state capabilities identify the current step. Meaningful transitions notify currently assigned club members/advisor and actionable SLD; revoked assignments cannot read old notices.

## Handover

Approved AGM requires explicit SLD `/api/club-reports/id/apply-handover` with report revision and club_revision. Pending Secretary reports cannot be orphaned by the change. Server creates committee_handover starts_at/ends_at/outgoing/incoming/report_id, with handover_days default7 (SLD settings1..90). Before deadline outgoing officers keep current titles; incoming newly assigned people have Pending position access and draft rights, without President/Treasurer/Secretary signature authority. At exact server deadline App.get/all apply the incoming current roster and new owner for every access check, including direct endpoints before polling. Previously submitted signatures and version records stay historical. Pending incoming lists/overlap deadline are exposed explicitly.

Yearly club_hierarchy retains outgoing/incoming names and positions, approved/effective dates. Public hierarchy history uses frozen names/positions and safe current photos, no email/ID. Public activity_history exposes approved actual weekly/AGM dates and past event schedules, distinguishing evidenced completion from elapsed schedules.

## Policies and submission integrity

SLD-only revisioned settings add handover_days/transfer_days. Changing settings affects future starts/approvals, not previously frozen deadlines. All advisor approvals entering pending_sld require a second explicit confirm_submission=true with the current revision. A proposal whose planned expenses exceed revenue requires SLD deficit_approval_reason; server freezes amount/reason/actor/time/version/digest. A deficit is never approved by an advisor or student.

Report submission requires server-associated photos: AGM>=1, weekly>=2, exact-target distinctSHA evidence. Draft saves preserve server photo_evidence. Related event photos/completion and archives are delegated to evidence.py; bytes and metadata remain private and currently scoped.

## Observed checks

HTTP withdrawal suite covers trusted signature order, absent confirmation, Finance upload permission, exact document download, all-approval deadline, trusted receipt timestamp, concurrent acknowledgement one winner, immutable version, multiple recipients/source DOCX signatures, no ledger posting and direct access revocation at deadline. Broader reports/legacy workflow suites are updated with explicit confirmation and required photo fixtures. Live Finance verification, university credentials, rendered web/mobile and external deployment remain unverified.

Readiness limit: intermittent Windows ConnectionResetError10054 was observed during local DOCX/PDF response reads, including a withdrawal download. Instrumented transfer runs completed with correct Content-Length and clean handler finish, but the cause is not confirmed. Keep this as an ICT transport investigation and do not claim the local HTTP implementation is stable or production-ready. The same workflow and file checks passed in successful runs; failures are not silently retried.
