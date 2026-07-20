# ADR-0004: Publish under a downstream distribution identity

- Status: Accepted; publication not yet enabled
- Date: 2026-07-20

## Context

The upstream project already owns the `scansci-pdf` distribution identity.
Publishing independent code under that name would confuse provenance and may
not be authorized. The fork should remain installable from GitHub until its
own release metadata and PyPI trusted publisher are configured.

## Decision

The intended downstream PyPI distribution is `scansci-pdf-hku`. PyPI returned
404 for that project name on 2026-07-20; this observation is not a reservation
and must be checked again immediately before first publication.

The import package remains `scansci_pdf`, and the primary executable remains
`scansci-pdf`, providing drop-in compatibility. Therefore the upstream and
downstream distributions must not be installed in the same environment.

Downstream versions use `<upstream-version>.postN`. The first planned release
based on upstream 1.9.0 is `1.9.0.post1`. Importing a later upstream release
resets the base version and downstream counter. A deliberately incompatible
public interface starts the next major version instead.

PyPI publication remains gated until all of these conditions are true:

1. `pyproject.toml` uses the downstream distribution name and selected
   version.
2. README badges and installation commands refer to the downstream project.
3. A PyPI trusted publisher targets this repository and the `pypi`
   environment.
4. Repository variable `PYPI_PUBLISH_ENABLED` is set to `true`.
5. The release workflow passes metadata, build, and package checks.

## Consequences

GitHub/uv installation is the supported short-term channel. The repository
cannot accidentally publish over the upstream identity because the workflow
checks the intended name before upload. Activating PyPI is a separate reviewable
change rather than an incidental tag push.
