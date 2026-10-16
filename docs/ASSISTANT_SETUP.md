# Student Life assistant setup

Grounded record search works locally without an external service. Optional retrieval-augmented generation is implemented but requires university-owned server configuration and operational acceptance. Only currently permitted record excerpts are used. Ordinary students have the published upcoming/ongoing approved-event projection; committees/advisors have assigned records; event-only committees have their event; SLD has all current operational records. The assistant does not sign, approve or edit.

## Enable optional generation

1. QIU chooses an approved OpenAI API account and a model that supports Responses structured JSON output. This guide does not choose or assume a model entitlement.
2. Keep the API key in the hosting secret/environment configuration, outside the public web root, source, MySQL record data and chat.
3. Set OPENAI_API_KEY and SLD_ASSISTANT_MODEL on the Python server.
4. Set SLD_ASSISTANT_GENERATION_ENABLED=true only after QIU authorizes this provider/data use. Default false retains local grounded answers.
5. Restart the Python application and check /api/assistant/capabilities with an authenticated account. generation_configured=true means settings exist; it is not evidence of a successful provider call.
6. Verify staging with ordinary student, event-only organiser, committee, advisor and SLD accounts. Check private-source denial, removed assignments, fallback, citations and record links. Enable production only after university acceptance.

The server uses a fixed HTTPS Responses endpoint, a 20-second timeout, maximum output limit, strict answer/source_ids schema, no provider tools and store:false. It transmits only the permitted retrieved excerpts and the current question, never file bytes, drawn signatures, Google tokens or the full university directory. store:false does not establish zero provider retention; university administrators must confirm their account's data policy. Official references: [Responses migration and JSON output contract](https://developers.openai.com/api/docs/guides/migrate-to-responses?api-mode=responses), [Structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs).

## Observed and pending verification

Local HTTP tests verify scoped retrieval, returned-record evidence, task whitelist, provider timeout fallback, context revocation during generation and per-account 12-question/minute shared throttle. A mocked provider verifies the actual structured request and response parser. No live paid generation call or university key was used. Model factual quality, language coverage, cost and provider account configuration require staging evaluation.

Each question rebuilds a filtered BM25 corpus. There is no shared private search cache, vector service or client-history ingestion. Eight source excerpts per answer keep the payload bounded; matching_count/has_more reveal larger result sets. Exact-count questions use deterministic matching-record counts. Compound and ambiguous natural-language questions may need refinement; links provide direct evidence for the record.

Provider failures show local grounded results rather than inventing an answer. No matching permitted records means no sources, even if another club has matching private data. ASSISTANT_CONTEXT_CHANGED means access/content changed during generation; ask again. Source links are only local task routes and refresh permission before opening.

## Saved chat history
Successful answers persist as account-private assistant_history records with source fingerprints. GET /api/assistant/history lists current-account entries and rechecks sources; changed or revoked sources redact both question and answer. POST /api/assistant/history/delete accepts an owned id or all:true. Compact and full chat share this server history. Saved transcripts are never implicitly sent as provider context; each new query retrieves current permitted evidence. No-source general questions remain private/displayable. Deletion removes the persisted entry, not other accounts' histories.