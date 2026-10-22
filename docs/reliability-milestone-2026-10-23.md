# Reliability milestone

Fork: https://github.com/fableforce/adobe-mcp-rs

Branch: `harden/adobe-app-reliability`. Source baseline:
`0c4561effba2f6070914f7d4dbd8cf226e863a99`. The original source remains the
`upstream` remote. MIT notices and full history are retained.

This is a reviewable first hardening milestone for Illustrator, InDesign,
Premiere Pro and Photoshop, with After Effects regression coverage. It is not a
production-readiness claim. Premiere's title workflow remains unresolved.

## Verified scope

All live calls used real stdio MCP clients, separately built binaries, existing
Adobe adapters, isolated broker registries/ports and dedicated synthetic test
documents. No client projects were opened, saved or replaced. The prior evidence
REPORT predates its later test logs and is not treated as the current result.

V = verified on the stated Windows version; P = partial; U = untested.

| Application | Native document / reopen | Export and visual check | Error then next request | Timeout / broker restart, one edit | Application cold restart |
|---|---|---|---|---|---|
| Illustrator 30.8.2 | V: AI, three editable vector shapes, one 900 x 500 artboard | V: SVG and PNG, square/circle/triangle inspected | V | V: one marker layer | U |
| InDesign 21.6.0.57 | V: INDD, one page, two editable stories and rectangle | V: PDF/IDML; PDF rendered and title/layout inspected | V | V: one document-label mutation | U |
| Photoshop 27.11.0 | V: layered PSD, editable text and fill, 1200 x 800 | V: PNG inspected | V | V: one marker layer | U |
| Premiere Pro 26.5.2 | P: project saved, one main sequence created; initial creation required user dialogs | V: baseline H.264 MP4 decoded, 1920 x 1080, five seconds; title not certified | V | V: one additional test sequence | U |
| After Effects 26.5x89 | V: AEP saved/reopened; 1920 x 1080, five seconds, editable title, two opacity and two position keys | V: four PNG previews; fade and movement inspected | V | V: one invisible null marker | U |

Each timeout test submitted the mutation once, stopped the validation broker,
started a fresh broker, recovered the same request ID and read back exactly one
mutation. Discovery/ping and real script execution passed for all five adapters.
This establishes broker recovery, not full application-restart certification.
Synthetic contract tests additionally cover stale/malformed discovery, reconnect,
late results, multiple instances, FIFO/global exclusion and expired queued work.

## Changes

1. The scheduler and worker share the admission deadline. Expired queued scripts
   never start later. Running scripts are never replayed after a wait timeout.
2. Stale contact remains recoverable and retains the instance reservation, so an
   uncertain script's mailbox is not overwritten by another edit.
3. Every host uses a common MCP JSON result helper. Execution failure, timeout,
   lost contact and cancellation set `isError` and retain request evidence.
4. Canonical script tools accept `expectedOutputPaths`: fresh absolute paths,
   verified as nonempty/readable before success, including late results. A
   bounded two-second file-publication wait handles transient zero-byte files.
5. Existing adapter fixes are preserved in their own attributed commit. Bounded
   MCP validation scripts, an MOGRT recipe and architecture/recovery notes are
   included without migrating the five app entrypoints.

File checks are opt-in for arbitrary scripts. They do not validate a complete
media encoding, document editability, visual content, overwritten outputs or
undeclared script side effects. Tests separately reopened native documents,
rendered the PDF, decoded the MP4 and inspected images.

## MOGRT findings

The old After Effects request created a MOGRT but returned `ReferenceError:
Object is invalid` and recorded heartbeat errors. A fresh dedicated composition
exported a fresh MOGRT successfully after saving controller/name changes,
disabling the optional undo group and avoiding cached DOM access after export.
The next MCP request succeeded without restarting the bridge. These simultaneous
recipe changes do not isolate one root cause or prove the scheduler universally
fixed. The shared transport changes do not change Adobe's MOGRT implementation.

Premiere's old evidence records one title clip before save and zero afterward;
the reopened/rendered output lacks it. XML references are not proof of a live
clip. A new insertion/save test using the freshly exported MOGRT timed out on
request `req-18e0e7be9cf91988-42772-1`. Its reservation is preserved and the
mutation was not retried. The result must be recovered before continuing that
project. Baseline media export success does not certify the title workflow.

## Checks

Workspace tests: 112 passed, zero failed after the hardening changes. All five
debug binaries build. Rust formatting, Python syntax compilation and diff
whitespace checks pass. Strict all-target Clippy is blocked by the pre-existing
`field_reassign_with_default` warning in `script_contract.rs`'s test fixture;
that same initialization exists in the baseline. It is not reported as passing.

Earlier timeout tests assumed dispatch within 20-30 ms and excluded admission
I/O. They now separate expired-queue checks from a host-observed late-result test;
the daemon test uses an explicit completion barrier instead of a short sleep.

## Configuration

The Codex configuration and active release binaries were not replaced. No new
system-wide package, security preference, autostart registration or service was
installed. Existing UXP packages/CEP/Startup scripts were reused unchanged during
live tests; the source adapter fixes had already been installed previously.

Validation configurations use loopback ports 47755-47759. Their own registries,
logs and PID files reside in the dedicated evidence directory. A discovery-only
directory junction links each validation `instances` directory to the existing
bridge instances, whose heartbeat paths identify the real command mailboxes.
Run only one validation process per app, and do not issue simultaneous commands
from another MCP client. Validation brokers are stopped after each bounded call;
Adobe applications are left open. The user resolved Premiere scratch-disk/save
dialogs during initial project creation; no security change was requested.

Rollback: continue using the existing release binaries/configuration. There is
no configuration deployment to undo. Retain the evidence directory for review;
do not recursively delete its discovery junctions. To remove source changes
later, revert the milestone commit on a separate branch, preserving unrelated
work; do not hard-reset the user's checkout. Git remote changes are reversible
by renaming this fork remote and restoring upstream as origin.

## Evidence and next work

Local evidence is under `Documents/Adobe-MCP-Hardening-2026-10-23`, including
the original dirty patch, request JSON, scripts, native files, previews,
`timeout-summary.json`, `final-tests.log`, `build.log` and `clippy.log`. Private
configuration backups and original test documents are not committed or pushed.

Next milestone: resolve Premiere's title persistence and modal save behavior,
then test genuine application/panel restarts and reconnect across the four main
apps. Keep a single Codex-facing entrypoint as a later composition of existing
shared crates, after these adapter lifecycle paths are dependable.

References: [Premiere SequenceEditor API](https://developer.adobe.com/premiere-pro/uxp/ppro-reference/classes/sequenceeditor),
[Premiere official samples](https://github.com/AdobeDocs/uxp-premiere-pro-samples),
[Photoshop modal execution](https://developer.adobe.com/photoshop/uxp/2022/ps-reference/media/executeasmodal),
[CEP resources](https://github.com/Adobe-CEP/CEP-Resources),
[community-maintained AE CompItem reference](https://ae-scripting.docsforadobe.dev/item/compitem/).
