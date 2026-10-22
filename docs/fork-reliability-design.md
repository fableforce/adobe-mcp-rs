# Fork reliability milestone

Scope: Illustrator, InDesign, Premiere Pro, and Photoshop. After Effects is a
shared-code regression target. This milestone does not migrate the five apps.

## Existing architecture

`mcp-core` owns host metadata, configuration, script policy and tool schemas.
`bridge-core` owns discovery, per-instance command/result mailboxes and durable
request records. `daemon-core` owns host-neutral TCP dispatch and FIFO scheduling.
The `ai`, `id`, `pr`, `ps`, and `ae` crates supply application tools and runtime
adapters. These shared crates already support a future single MCP entrypoint:
route an explicit application to its HostSpec/configuration, then use the existing
broker. A common frontend would still need tool namespacing, lifecycle ownership
and resource routing. Implementing it now would obscure application reliability.

The graph MCP is unavailable in this session. Codemap located host bridges but
did not index Rust symbols; direct source tracing covered all five stdio adapters,
the common schema, scheduler, registry and bridge contract tests.

## Invariants

1. One deadline starts at admission and includes scheduler waiting. Expired work
   must not be dispatched after its caller has stopped waiting.
2. A wait timeout does not undo, stop, or authorize re-execution of host code.
   Request IDs recover late results. There is no automatic script retry.
3. A stale heartbeat does not prove a script stopped. Preserve its mailbox
   reservation until a matching result arrives. Rediscovery can select a new
   application instance; never silently retarget an uncertain mutation.
4. Host failure, timeout, cancellation and lost contact set MCP `isError` while
   preserving the structured request ID, host/instance and cause.
5. Opt-in `expectedOutputPaths` checks fresh absolute output files for nonzero
   size and readability before success, including late-result recovery. Existing
   outputs are refused before execution. A two-second bounded availability wait
   handles delayed/zero-byte publication without re-exporting. This does not establish format validity,
   complete asynchronous encoding, visual content, or document editability.

## Request states

`queued` -> `dispatched` -> `running` -> `completed` / `failed`.
`timeout` means the queue/execution wait budget elapsed. Before-dispatch timeouts
never submit host code; after-dispatch timeouts can acquire late results.
`lost` means contact is stale and execution outcome is unknown; it is recoverable.
An uncertain reservation can intentionally block that same instance indefinitely
when no result arrives. Recovery must establish what happened; silently freeing
the mailbox or replaying an edit is not a safe fallback.
`cancelRequested` is cooperative; `cancelled` confirms queued work was stopped.
MCP clients must inspect request state after reconnect and never replay a write
merely because `isError` was set. No automatic replay is implemented.

## Preserved local fixes

The six initial dirty files were present before this milestone and are retained
as prior local work, not claimed as newly authored fixes: Illustrator destination
name preservation across mutating ExtendScript File.rename; Photoshop/Premiere
supported asynchronous UXP writes; InDesign doScript error envelopes and await;
the two corresponding UXP package version bumps. The source MIT notices remain.
Original patch/evidence copies are kept outside the repository. No private test
documents, configuration snapshots, credentials or host logs are published.

## Known investigations

The October 22 REPORT.md predates later tests. Actual Premiere logs show one
MOGRT clip before save and zero after save, and reopened/rendered output still
lacks the title. XML title references are not proof of an operational clip.
The After Effects MOGRT attempt produced a nonempty file but returned
`ReferenceError: Object is invalid`; its result also records heartbeat write
failures. These are separate observations, not proof that export itself failed.
Do not retry that mutation against the old document. Use isolated new documents,
save before MOGRT export and reacquire DOM references after host operations.

The follow-up fresh-MOGRT/native-Windows-path save workflow passed: the title
survived a successful saveAs, project reopen and visible video export. Cancelling
the earlier dialog returned `saved:false` even though one clip remained live.
Always check the save return value; live timeline visibility is not persistence.
The earlier failure's sole cause and universal modal handling remain unproven.

## Coverage boundary

All five stdio adapters use the shared MCP result helper and forward the new
output contract. Request recovery covers execution, get-result and busy-instance
collection. Existing legacy dispatch names and host-specific exports remain
outside API migration scope. Arbitrary script bodies must declare expected
outputs; the broker cannot infer their semantics. App runtime scheduling,
permission requirements and existing system installations are unchanged.
