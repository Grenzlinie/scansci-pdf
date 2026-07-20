# ScanSci PDF maintainer context

This repository is the independently maintained `Grenzlinie/scansci-pdf`
line. It keeps compatibility with the upstream `Rimagination/scansci-pdf`
project where that does not weaken institutional-access reliability or
credential safety.

## What the system does

ScanSci PDF turns a DOI or arXiv identifier into a verified local PDF. A
download can come from an open source, a publisher endpoint, or an
institutional route. Institutional access never grants rights by itself: it
reuses access already granted to the user by their library and publisher.

The successful institutional flow is:

```text
identifier -> institutional access -> browser session -> challenge gate
           -> publisher PDF resolver -> PDF capture -> PDF validation -> file
```

## Domain language

**Institutional access** is a library-managed route, such as HKU EZProxy,
CARSI, Shibboleth, OpenAthens, or WebVPN. It establishes the network and
authentication context in which a publisher may grant full-text access. It
does not contain publisher-specific PDF discovery rules.

**Browser session** is one visible CloakBrowser context plus its pages,
cookies, network responses, and lifetime. A session begins before navigation
to the institutional route and ends only after success, explicit user skip,
non-interactive timeout, or an unrecoverable browser error.

**Challenge gate** is the state that blocks progression while a publisher or
intermediary asks for human verification. Detection does not solve or bypass
the challenge. It keeps the browser available, waits for the user, and then
re-evaluates the current page.

**Publisher PDF resolver** is the module that converts a live publisher page
into a PDF entry point. Its interface is
`PublisherPdfResolver.resolve(page) -> str`: it returns an absolute PDF URL,
or operates the best PDF control and returns an empty string so the caller can
continue polling. Publisher markup, signed URL reconstruction, DOM ranking,
and supplementary-file rejection belong inside this module.

**PDF capture** is the acquisition of bytes from an authenticated browser
network response or a credentialed fetch in the same browser context. A
response is accepted only after its bytes begin with `%PDF-` and meet the
resolver's minimum structural size threshold.

**Source racing** is the ordinary strategy that tries several eligible
sources for speed and coverage. **EZProxy-only** is an explicit strategy that
validates the DOI and local cache, then calls only the configured EZProxy
source. It does not silently fall back to open-access, direct publisher,
Sci-Hub, InstSci, CARSI, or WebVPN sources.

## Module ownership

- `sources/__init__.py` owns source selection, strategy semantics, and result
  aggregation.
- `sources/ezproxy.py` owns the HKU/EZProxy browser-session state machine,
  challenge waiting, cookie persistence, PDF response capture, and browser
  lifetime.
- `publisher_pdf_resolver.py` owns publisher-specific browser-page knowledge.
- `publisher_pdf_router.py` owns non-browser candidate construction used by
  direct and batch publisher paths. Convergence with the browser resolver is
  allowed only when it reduces the caller interface rather than exposing more
  publisher detail.
- `browser_login.py` owns interactive login and initial session persistence.
- `config.py` owns user-visible configuration defaults and validation.

## Invariants

- Passwords, Cookie values, signed PDF queries, and authentication tokens must
  never enter source control, logs, test fixtures, CI artifacts, or failure
  reports.
- Cookie files are local runtime state, written atomically with mode `0600`.
- A loading or verification page is not a download failure.
- Publisher rules preserve the current institutional proxy host.
- Public CI must run without a browser login. HKU acceptance tests run only on
  a private, explicitly labelled self-hosted runner.
- `origin` is `Grenzlinie/scansci-pdf`; `upstream` is
  `Rimagination/scansci-pdf`. Upstream changes are fetched and reviewed, never
  pushed to automatically.

## Verification levels

1. Cross-platform unit tests verify source selection, resolver behavior,
   state transitions, redaction, and Cookie persistence without credentials.
2. A manual HKU live test verifies a known DOI through a private self-hosted
   runner and inspects `%PDF-`, title, and page count.
3. A release build verifies metadata, wheel/sdist contents, and the downstream
   distribution policy before PyPI publication is enabled.

Architecture decisions are indexed in [docs/adr/README.md](docs/adr/README.md).
Operational instructions for the HKU acceptance test are in
[docs/operations/hku-live-test.md](docs/operations/hku-live-test.md).
