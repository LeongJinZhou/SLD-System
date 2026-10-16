# Profiles, chat and annual reports Implementation Plan

> For agentic workers: use bounded specialist implementation and Superpowers executing-plans; verify each task before delivery.

**Goal:** Deliver distinct public club/personal profiles, reusable chat history, clear annual reporting and concise role-aware operational forms.

**Architecture:** Retain Python/MySQL record storage and vanilla UI. Add safe public projections rather than weakening private access. Chat history is per-account server storage and never implicitly reused as provider context.

**Tech Stack:** Python, MySQL production/SQLite preview, vanilla JavaScript/CSS, retained OOXML/PDF exporters.

**Spec:** Latest Profiles, browsing and conversational UI section in PRD.md.

## Global constraints
- All recorded timestamps and signer identity remain server-owned; MYT display is human-readable.
- Preserve original supplied template layout and immutable earlier signatures.
- Public views contain approved profiles/published summaries, never internal documents or balances.
- Existing browser refusal persists; no browser workaround or invented rendering claim.

## Review focus
- Removed assignments must revoke private chat source access, even in saved history.
- Profile images/names refresh from trusted Google login and cannot grant roles.
- Annual AGM counting must separate report status from signed/approved completion.
- Filter refresh cannot erase finance/report edits or defeat autosave ordering.
- Floating chat must share history with full-page chat and safely render text/links.

## Task 1: Backend public profiles and annual report semantics
Owner backend: server.py, auth.py, club_reports.py, profiles.py, tests/test_profiles.py and report/signature fixtures.
- [x] Inspect current public/private projections and signing profile logic.
- [x] Add failing authorization/projection, annual tracking and contextual identity checks.
- [x] Implement authenticated public clubs and student profiles, refreshed photos, annual AGM report year and SLD tracking.
- [x] Preserve ordered distinct signature permissions and source exports; run affected HTTP checks.
API contracts communicated directly to frontend/root before UI implementation.

## Task 2: Interface profiles, floating chat and operational forms
Owner frontend: web/* and Node tests.
- [x] Inspect current shell/filter/report/receipt controllers.
- [x] Separate AGM/weekly pages and implement public profile hierarchy with logos/photos.
- [x] Implement shared compact/full assistant, history/list/delete and keyboard labelled launcher.
- [x] Auto-apply all filters safely; simplify copy/date display and item receipt autosave.
- [x] Verify controllers, role navigation, stale saves and safe source links.

## Task 3: Persistent private chat and integration
Owner root: assistant.py, tests/test_assistant.py, exports.py if mapping correction needed, docs and task files.
- [x] Add per-account saved answers/questions/source references with list/delete APIs.
- [x] Recheck original current source scope before returning saved answers; do not leak revoked information.
- [x] Test cross-account list/delete denial, restart persistence and no implicit model conversation reuse.
- [x] Update manuals, architecture/function flows and regenerate static source reference.

## Task 4: Independent acceptance
Owner review: read-only source/test/export inspection.
- [x] Review privacy, annual semantics, receipts, contextual signatures and source-format preservation.
- [x] Run full meaningful regression suites sequentially for Python exports, Node controllers and actual isolated MySQL when available.
- [x] Resolve findings; refresh preserved-data preview and record remaining live/browser prerequisites.
