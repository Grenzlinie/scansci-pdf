# Independent development foundation

## Originating request

Establish the repository for independent development after the HKU EZProxy
feature merge:

1. Create `CONTEXT.md` and ADRs that define institutional access, publisher
   resolution, browser sessions, challenge gates, Cookie lifecycle/security,
   and the responsibility split between EZProxy-only and source racing.
2. Extract publisher-page discovery into one `PublisherPdfResolver` deep
   module so Elsevier, Springer, ACS, and Wiley rules do not accumulate in the
   EZProxy state-machine file.
3. Keep `origin` pointed at `Grenzlinie/scansci-pdf` and `upstream` pointed at
   `Rimagination/scansci-pdf`.
4. Keep cross-platform tests credential-free. Run HKU live acceptance only on
   a private self-hosted runner, without putting accounts, Cookies, signed
   URLs, or PDFs in GitHub.
5. Add security controls for Cookie permissions, ignored cache paths, redacted
   output, and non-sensitive failure handling.
6. Decide the independent distribution name, version strategy, upstream
   compatibility statement, and short-term GitHub/uv installation path.

## Acceptance criteria

- A new maintainer can identify module ownership, invariants, and verification
  levels from the repository root.
- Architecture decisions are explicit and indexed.
- EZProxy calls one public publisher resolver interface; resolver tests cover
  the four named publishers and JavaScript-only controls.
- Public CI requires no institutional credential.
- The HKU workflow is manual, targets a protected private runner label, uses a
  runner-local mode-`0600` Cookie, uploads no PDF, and cleans temporary state.
- PyPI cannot publish accidentally under the upstream distribution identity.
- Full tests and syntax/format checks pass without committing local Cookie,
  PDF, signed URL, or the local mirror rewrite in `uv.lock`.
