# Opt-in governed execution profile

Status: proposed  
Branch: `feature/opt-in-governed-execution-profile`  
Initial consumer: [energration/eudorus#2561](https://github.com/energration/eudorus/issues/2561)

## Decision

Add governance as an explicit configuration profile layered over the existing raw-script-first architecture. Existing behavior remains the default. No current user, configuration, tool, prompt, resource, bridge, daemon, or compatibility dispatch changes behavior unless a governed profile is explicitly enabled.

This feature is a risk policy and audit boundary, not a sandbox. JSX continues to run with the Adobe host's authority.

## Backward-compatibility contract

1. Configuration files without a `[governance]` table retain current semantics.
2. Default `tools/list` remains semantically identical.
3. Existing public tools retain their names, schemas, response shapes, and behavior.
4. Existing prompts and resources remain available.
5. Existing raw `run-jsx` remains public by default.
6. Existing `run-jsx-file` unsafe/trusted behavior remains unchanged by default.
7. Legacy compatibility dispatch remains unchanged.
8. Instance routing, FIFO scheduling, global-exclusive gates, request IDs, retained results, diagnostics, and bridge paths remain unchanged.
9. Other Adobe hosts are unaffected unless separately configured.
10. Removing or disabling the profile restores existing behavior.

## Illustrative configuration

The exact schema is subject to implementation review.

```toml
[governance]
enabled = true
profile = "eudorus-animation"
preserve_default_surface = true
expose_inline_unsafe_jsx = false
require_project_identity = true
project_identity = "EudorusAnimationSuite"
allowed_project_roots = ["/absolute/path/to/eudorus-animation"]
allowed_output_roots = ["/absolute/path/to/eudorus-animation/renders"]
require_operation_manifest = true

[script_files]
allowed_roots = []
max_bytes = 1048576

[[script_files.trusted_scripts]]
path = "/absolute/path/to/approved.jsx"
sha256 = "<exact-sha256>"
```

## Behavioral rules

- `governance.enabled` defaults to `false`.
- Unknown governance keys fail configuration validation only when the table is present.
- Tool filtering occurs only when governance is enabled.
- `preserve_default_surface = true` keeps the current surface even when governance metadata and root checks are enabled.
- `expose_inline_unsafe_jsx = false` may hide `run-jsx` only for the configured host/profile.
- Trusted file execution continues to require canonical path and exact SHA-256.
- An explicitly empty `script_files.allowed_roots` continues to disable unsafe file execution.
- Governed mutations require a matching project identity when configured.
- Governed project and output paths are canonicalized before containment checks.
- Audit records add optional governance fields without removing or renaming existing fields.

## Optional audit fields

- `governanceProfile`
- `modelIdentifier`
- `operationIdentifier`
- `projectIdentifier`
- `compositionIdentifier`
- `sourcePath`
- `sourceSha256`
- `outputPath`
- `outputSha256`

Existing consumers must tolerate their absence when governance is disabled.

## Tool admission

Modeled tools should be thin, validated adapters over existing broker/bridge contracts. A tool is admitted only when it provides stronger validation, auditability, or semantic clarity than raw JSX.

Initial candidates:

- `inspect-host`
- `inspect-project`
- `create-eudorus-project`
- `create-component`
- `create-flow`
- `set-component-state`
- `animate-request-traversal`
- `save-project`
- `save-preview-frame`
- `render-composition`
- `get-operation-result`

Names are provisional until the operation model and compatibility review are complete.

## Implementation sequence

1. Freeze current `tools/list`, configuration, and execution behavior in regression tests.
2. Add optional configuration types with disabled defaults.
3. Add optional audit fields with serialization compatibility tests.
4. Add profile-aware tool filtering behind `governance.enabled`.
5. Add project identity and canonical root guards.
6. Add one proof modeled operation.
7. Run default-mode and governed-mode E2E tests on After Effects 2026 for macOS.
8. Generalize only after the proof operation passes.

## Acceptance tests

### Default mode

- Existing workspace tests pass unchanged.
- Existing configs parse identically.
- Default `tools/list` remains semantically identical.
- Raw `run-jsx` remains public.
- Unsafe and trusted `run-jsx-file` retain existing behavior.
- Existing After Effects bridge tests pass.

### Governed mode

- Profile affects only its configured host.
- Inline unsafe JSX can be hidden.
- Trusted script path and hash are enforced.
- Project identity mismatch fails closed.
- Canonical project/output root escape fails closed.
- Audit records include configured governance identifiers.
- Disabling the profile restores default behavior.

## Non-goals

- Claiming JSX is sandboxed.
- Removing raw-script-first behavior.
- Breaking existing clients to force modeled operations.
- Applying Eudorus-specific policy to other users by default.
- Changing Adobe host architecture unrelated to the opt-in profile.
