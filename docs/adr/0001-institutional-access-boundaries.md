# ADR-0001: Separate institutional access from source selection

- Status: Accepted
- Date: 2026-07-20

## Context

Ordinary downloads benefit from trying several legal and configured sources.
An HKU user may instead need deterministic EZProxy behavior so that time is
not spent on unrelated sources and a visible verification browser is not
closed by another source's result.

## Decision

Source selection and institutional access remain separate modules.

- Ordinary strategies may race eligible sources and may reach EZProxy as an
  institutional fallback.
- `ezproxy_only` validates the DOI and local cache, then calls exactly one
  EZProxy source.
- EZProxy owns authentication navigation and the browser-session lifecycle.
- EZProxy does not fall back to another institutional or public source.
- Both paths use the same success/failure result contract.

## Consequences

The direct mode is predictable and testable by asserting that no other source
builder executes. Ordinary downloads retain broader coverage. Any future
institution-only strategy must state whether it participates in source racing
or is exclusive; it may not infer that choice from login configuration.
