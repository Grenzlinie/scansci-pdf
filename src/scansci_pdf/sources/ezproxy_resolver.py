"""Publisher PDF discovery for pages loaded through an institutional proxy."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin, urlparse


ELSEVIER_PDF_RE = re.compile(
    r'"pdfDownload":\{"isPdfFullText":(?:true|false),'
    r'"urlMetadata":\{"queryParams":\{"md5":"([^"]+)",'
    r'"pid":"([^"]+)"\},"pii":"([^"]+)",'
    r'"pdfExtension":"([^"]+)","path":"([^"]+)"\}\}'
)

CITATION_PDF_RE = re.compile(
    r'<meta[^>]+name=["\']citation_pdf_url["\'][^>]+content=["\']([^"\']+)["\']',
    flags=re.IGNORECASE,
)
CITATION_PDF_RE_REVERSED = re.compile(
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']citation_pdf_url["\']',
    flags=re.IGNORECASE,
)

DOM_PDF_CANDIDATES_JS = r"""
() => Array.from(document.querySelectorAll("a[href], button, [role='button']"))
  .map(el => ({
    text: (el.innerText || el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 200),
    href: el.href || el.getAttribute('href') || '',
    aria: el.getAttribute('aria-label') || '',
    onclick: el.getAttribute('onclick') || '',
    dataUrl: el.getAttribute('data-url') || el.getAttribute('data-pdf-url') || '',
    cls: typeof el.className === 'string' ? el.className : '',
    id: el.id || ''
  }))
  .filter(item => /pdf|download|full text|read/i.test(Object.values(item).join(' ')))
""".strip()

DOM_PDF_CONTROL_CLICK_JS = r"""
() => {
  const controls = Array.from(document.querySelectorAll("a[href], button, [role='button']"));
  const ranked = controls
    .filter(el => !el.hasAttribute('data-scansci-pdf-clicked'))
    .map(el => {
      const text = [
        el.innerText || el.textContent || '',
        el.getAttribute('aria-label') || '',
        el.getAttribute('title') || '',
        el.id || '',
        typeof el.className === 'string' ? el.className : ''
      ].join(' ').replace(/\s+/g, ' ').trim();
      let score = 99;
      if (/download pdf/i.test(text)) score = 0;
      else if (/open pdf|view pdf/i.test(text)) score = 1;
      else if (/full text.*pdf|pdf.*full text/i.test(text)) score = 2;
      else if (/pdf/i.test(text)) score = 3;
      if (/supporting|supplement|appendix/i.test(text)) score += 50;
      if (/purchase|buy now|add to cart/i.test(text)) score += 100;
      return {el, score};
    })
    .filter(item => item.score < 50)
    .sort((left, right) => left.score - right.score);
  if (!ranked.length) return false;
  const control = ranked[0].el;
  control.setAttribute('data-scansci-pdf-clicked', 'true');
  if (control.tagName === 'A') control.setAttribute('target', '_self');
  control.click();
  return true;
}
""".strip()


def _publisher(article_url: str) -> str:
    host = urlparse(article_url).netloc.lower()
    if "sciencedirect" in host:
        return "elsevier"
    if "springer" in host or "nature" in host:
        return "springer"
    if "acs.org" in host or "pubs-acs-org" in host:
        return "acs"
    if "wiley" in host or "onlinelibrary" in host:
        return "wiley"
    return "generic"


def discover_pdf_url_from_html(article_url: str, html: str) -> str:
    """Return a publisher PDF URL encoded in article HTML, if present."""
    match = ELSEVIER_PDF_RE.search(html)
    if match:
        md5, pid, pii, extension, path = match.groups()
        parsed = urlparse(article_url)
        host = parsed.netloc if "sciencedirect" in parsed.netloc.lower() else "www.sciencedirect.com"
        scheme = parsed.scheme or "https"
        return f"{scheme}://{host}/{path.strip('/')}/{pii}{extension}?md5={md5}&pid={pid}"

    for regex in (CITATION_PDF_RE, CITATION_PDF_RE_REVERSED):
        citation = regex.search(html)
        if citation:
            return urljoin(article_url, citation.group(1))
    return ""


def _candidate_values(candidate: dict[str, Any]) -> list[str]:
    return [
        str(candidate.get(key, ""))
        for key in ("href", "dataUrl", "onclick", "text", "aria", "cls", "id")
        if candidate.get(key)
    ]


def _accepted_pdf_url(url: str, publisher: str) -> bool:
    lowered = url.lower()
    if not lowered.startswith(("http://", "https://")):
        return False
    if any(token in lowered for token in ("/purchase", "buy-now", "add-to-cart")):
        return False
    if ".pdf" in lowered:
        return True
    if any(token in lowered for token in ("/doi/pdf/", "/doi/epdf/", "/doi/pdfdirect/", "/pdfft")):
        return True
    return publisher == "springer" and "/content/pdf/" in lowered


def discover_pdf_url_from_candidates(article_url: str, candidates: Any) -> str:
    """Rank DOM controls and return the most likely full-article PDF URL."""
    if not isinstance(candidates, list):
        return ""
    publisher = _publisher(article_url)
    ranked: list[tuple[tuple[int, int], str]] = []
    text_patterns = ("download pdf", "open pdf", "view pdf", "full text", "pdf")

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        values = _candidate_values(candidate)
        combined = " ".join(values).lower()
        text_score = next(
            (index for index, pattern in enumerate(text_patterns) if pattern in combined),
            len(text_patterns),
        )
        for raw in values:
            resolved = urljoin(article_url, raw)
            if _accepted_pdf_url(resolved, publisher):
                supplementary_penalty = 1 if any(
                    marker in combined for marker in ("supporting", "supplement", "appendix")
                ) else 0
                ranked.append(((supplementary_penalty, text_score), resolved))

    if not ranked:
        return ""
    ranked.sort(key=lambda item: item[0])
    return ranked[0][1]
