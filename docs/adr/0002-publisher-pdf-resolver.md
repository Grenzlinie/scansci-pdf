# ADR-0002: Resolve browser publisher pages through one deep module

- Status: Accepted
- Date: 2026-07-20

## Context

Elsevier exposes signed metadata, Springer exposes citation metadata, and ACS
or Wiley may expose JavaScript-driven controls. Keeping these rules in the
EZProxy state machine mixes publisher knowledge with authentication and
browser lifetime decisions.

## Decision

`PublisherPdfResolver` is the seam for publisher-specific discovery on a live
browser page. Its interface is one method:

```python
PublisherPdfResolver.resolve(page) -> str
```

The method returns an absolute PDF URL when one is available. If the page
offers only a ranked PDF control, the resolver operates that control and
returns an empty string; the browser-session state machine continues polling.

The module owns signed metadata reconstruction, institutional proxy-host
preservation, DOM candidate ranking, purchase/supplement rejection, and PDF
control operation. The caller owns challenge detection, waiting, navigation,
response capture, and file validation.

## Consequences

Adding publisher markup rules does not enlarge the EZProxy interface. Tests
exercise the resolver through the same method used by the browser state
machine. The older EZProxy-specific resolver functions are removed rather
than retained as a second shallow interface.
