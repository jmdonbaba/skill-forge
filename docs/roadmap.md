# From captured experience to validated learning

Current scope: generate environment-aware skills, validate their structure,
install complete bundles, retain every input item and protect existing work
with explicit replacement backups. Human review and real task evidence remain
necessary. Claude Code already has memory features; this project's intended
distinction is evidence, applicability and measured avoidance of repeated
failures, rather than automatic memory alone.

The supplied review proposes the following future work. None of these features
is advertised as implemented by the current generator.

| Stage | Deliverable | Acceptance evidence |
| --- | --- | --- |
| P1: Experience records | Stable IDs, deduplication, reviewable incremental merges, evidence and revision history with rollback | A second observation updates an existing skill without losing prior evidence; reverting restores the prior revision |
| P1: Applicability | Minimal per-skill environment fingerprints and relevant version/proxy/transport checks | A changed proxy port or remote protocol marks the experience for revalidation and downgrades it to advice |
| P1: Routing | Suggest skill, project rule, knowledge note or script based on experience type | A pnpm project rule stays project-scoped; a repeatable multi-step workflow becomes a skill |
| P2: Friction Radar | Opt-in local failure/stop hook signals, redaction, candidate cards | Repeated failures followed by an evidenced recovery yield one candidate; user can save, merge or ignore; nothing is persisted as trusted experience without review |
| P2: Rescue Mode | Retrieve applicable historical solutions after similar repeated failures | Present the matching evidence and current applicability check; do not blindly execute or recommend deprecated records |
| P3: Trust and expiry | Candidate, Verified, Revalidated, Stale and Deprecated lifecycle | Verification requires observed task evidence; age/environment drift marks records stale; deprecated records cannot be automatically recommended |
| P3: Proof of Learning | Fresh-session with/without-skill trials and regression reports | Publish task success, retry count, time and tool calls with environment/model context, including negative and failed trials |
| P4: Experience graph | Local JSON relationships between causes, tools and fixes | Git/npm/Docker failures can share a cause without being conflated with the same solution |
| P4: Self-healing candidates | Detect drift or failure, propose a revision and preserve old versions | Candidate changes remain separate until reviewed and revalidated; previous skill is recoverable |
| P4: Portability | Cross-tool exports, redacted sharing and experience packs | Private data is excluded and imported experience retains its provenance, scope and verification state |

The smallest next product increment is a local Friction Radar candidate card:
failed commands, redacted error summaries, final approach, applicable environment
and verification evidence, with save/merge/ignore decisions. Hooks only collect
signals; they do not prove a problem was solved. Validate exact hook contracts
against the Claude Code version used before implementation.
