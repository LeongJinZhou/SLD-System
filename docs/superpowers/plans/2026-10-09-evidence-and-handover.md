# Evidence and committee lifecycle Implementation Plan

**Goal:** Complete photo evidence, confirmation, withdrawals and timed annual committee handover with scoped history and archives.
**Architecture:** Existing Python record store/MySQL transactions and server-authoritative role projections; bounded private uploads and standard-library ZIP packages. Existing source-template exports remain intact.
**Tech Stack:** Python, MySQL production/SQLite preview, vanilla JavaScript; existing PDF renderer.
**Spec:** PRD.md current lifecycle acceptance.

## Global constraints
Server timestamps immutable. SLD alone changes7day handover/14day transfer policy. Pending incoming access does not grant current President/Treasurer signature authority. Annual public history excludes private forms/finance/files.

## Review focus
Expired oldaccess, stale revisions, spoofed signer/time, ZIP path traversal and crossclub download, evidence missing at submission, duplicatefinancialposting, absentfinalconfirmation.

- [ ] Implement and test private photo upload/count gate and named ZIPs in evidence.py.
- [ ] Add ended approved-event completion reports independently from financial expense reporting; approvedcompletion may establish performance completion.
- [ ] Implement backend withdrawals, configurable timed handover, publichistory, deficit reason and secondconfirmation.
- [ ] Integrate UI autosaves, uploads, staged signatures, pendingtitles/history/archive and secondconfirmation.
- [ ] SLD annual ZIP orderly proposals/receipts/photos/reports plus signed annual/weekly docs and manifest.
- [ ] Independentreview, HTTP/controller/MySQL/PDF checks; fix materialfindings.
- [ ] Synchronize docs/source inventory, preserve data/restart owned preview, report actual limits.
