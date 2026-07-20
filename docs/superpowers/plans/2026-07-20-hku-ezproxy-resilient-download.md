# HKU EZProxy resilient download

## User-visible contract

- `scansci-pdf get DOI --ezproxy-only` maps to `strategy=ezproxy_only`.
- `ezproxy_only` validates the DOI and checks local cache, then calls only EZProxy.
- The EZProxy source reuses cookies saved by `scansci-pdf login --login-type ezproxy`.
- Article and PDF verification pages keep the visible CloakBrowser context alive.
- At timeout an interactive CLI offers another wait window or `skip`; non-interactive callers fail.
- The browser closes only after success, explicit skip, non-interactive timeout, or an unrecoverable error.

## Publisher and PDF behavior

- Elsevier `pdfDownload` metadata preserves an institutional proxy host.
- Springer uses `citation_pdf_url`; ACS and Wiley use ranked DOM PDF controls.
- Generic PDF links remain a fallback.
- PDF bytes come from a captured browser response first and a credentialed in-page fetch second.
- Refreshed browser cookies are saved atomically with owner-only permissions.
- Logs never include cookie values or signed PDF query strings.

## Acceptance

- Unit tests cover challenge pages at article and PDF phases, slow/empty loading pages,
  publisher discovery, in-page fetch, interactive and non-interactive timeout behavior,
  cookie persistence, CLI routing, and EZProxy-only source selection.
- A manual HKU smoke test downloads DOI `10.1016/j.actamat.2026.122519` as a valid 20-page PDF.
