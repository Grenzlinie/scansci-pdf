"""Resolve publisher PDF entry points from a live browser page.

The module owns publisher markup knowledge and DOM-control operation so
institutional access sources only need to poll one small interface.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urljoin, urlparse


_ELSEVIER_PDF_RE = re.compile(
    r'"pdfDownload":\{"isPdfFullText":(?:true|false),'
    r'"urlMetadata":\{"queryParams":\{"md5":"([^"]+)",'
    r'"pid":"([^"]+)"\},"pii":"([^"]+)",'
    r'"pdfExtension":"([^"]+)","path":"([^"]+)"\}\}'
)
_CITATION_PDF_RE = re.compile(
    r'<meta[^>]+name=["\']citation_pdf_url["\'][^>]+content=["\']([^"\']+)["\']',
    flags=re.IGNORECASE,
)
_CITATION_PDF_RE_REVERSED = re.compile(
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']citation_pdf_url["\']',
    flags=re.IGNORECASE,
)

_DOM_PDF_CANDIDATES_JS = r"""
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

_DOM_PDF_CONTROL_CLICK_JS = r"""
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


class PublisherPdfResolver:
    """Discover or operate the best publisher PDF entry point on a page.

    ``resolve`` returns an absolute URL when markup exposes one. When the
    publisher only exposes a JavaScript-driven control, it clicks the best
    non-supplementary control and returns an empty string so the caller can
    continue polling the same browser page.
    """

    def resolve(self, page: Any) -> str:
        article_url = self._page_url(page)
        html = self._page_html(page)
        discovered = self._from_html(article_url, html)
        if discovered:
            return discovered

        try:
            candidates = page.evaluate(_DOM_PDF_CANDIDATES_JS)
        except Exception:
            return ""
        if isinstance(candidates, str) and candidates.startswith(("http://", "https://")):
            return candidates

        discovered = self._from_candidates(article_url, candidates)
        if discovered:
            return discovered

        try:
            page.evaluate(_DOM_PDF_CONTROL_CLICK_JS)
        except Exception:
            pass
        return ""

    @staticmethod
    def _page_url(page: Any) -> str:
        try:
            return str(page.url)
        except Exception:
            return ""

    @staticmethod
    def _page_html(page: Any) -> str:
        try:
            return str(page.content())
        except Exception:
            return ""

    @staticmethod
    def _from_html(article_url: str, html: str) -> str:
        match = _ELSEVIER_PDF_RE.search(html)
        if match:
            md5, pid, pii, extension, path = match.groups()
            parsed = urlparse(article_url)
            host = (
                parsed.netloc
                if "sciencedirect" in parsed.netloc.lower()
                else "www.sciencedirect.com"
            )
            scheme = parsed.scheme or "https"
            return (
                f"{scheme}://{host}/{path.strip('/')}/{pii}{extension}"
                f"?md5={md5}&pid={pid}"
            )

        for regex in (_CITATION_PDF_RE, _CITATION_PDF_RE_REVERSED):
            citation = regex.search(html)
            if citation:
                return urljoin(article_url, citation.group(1))
        return ""

    @classmethod
    def _from_candidates(cls, article_url: str, candidates: Any) -> str:
        if not isinstance(candidates, list):
            return ""
        publisher = cls._publisher(article_url)
        ranked: list[tuple[tuple[int, int], str]] = []
        text_patterns = ("download pdf", "open pdf", "view pdf", "full text", "pdf")

        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            values = cls._candidate_values(candidate)
            combined = " ".join(values).lower()
            text_score = next(
                (
                    index
                    for index, pattern in enumerate(text_patterns)
                    if pattern in combined
                ),
                len(text_patterns),
            )
            for raw in values:
                resolved = urljoin(article_url, raw)
                if cls._accepted_pdf_url(resolved, publisher):
                    supplementary_penalty = int(
                        any(
                            marker in combined
                            for marker in ("supporting", "supplement", "appendix")
                        )
                    )
                    ranked.append(((supplementary_penalty, text_score), resolved))

        if not ranked:
            return ""
        ranked.sort(key=lambda item: item[0])
        return ranked[0][1]

    @staticmethod
    def _publisher(article_url: str) -> str:
        host = urlparse(article_url).netloc.lower()
        if "springer" in host or "nature" in host:
            return "springer"
        return "generic"

    @staticmethod
    def _candidate_values(candidate: dict[str, Any]) -> list[str]:
        return [
            str(candidate.get(key, ""))
            for key in ("href", "dataUrl", "onclick", "text", "aria", "cls", "id")
            if candidate.get(key)
        ]

    @staticmethod
    def _accepted_pdf_url(url: str, publisher: str) -> bool:
        lowered = url.lower()
        if not lowered.startswith(("http://", "https://")):
            return False
        if any(token in lowered for token in ("/purchase", "buy-now", "add-to-cart")):
            return False
        if ".pdf" in lowered:
            return True
        if any(
            token in lowered
            for token in ("/doi/pdf/", "/doi/epdf/", "/doi/pdfdirect/", "/pdfft")
        ):
            return True
        return publisher == "springer" and "/content/pdf/" in lowered
