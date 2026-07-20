from scansci_pdf.sources.ezproxy_resolver import (
    DOM_PDF_CONTROL_CLICK_JS,
    discover_pdf_url_from_candidates,
    discover_pdf_url_from_html,
)


def test_elsevier_metadata_preserves_hku_proxy_host():
    html = (
        '<script>"pdfDownload":{"isPdfFullText":true,'
        '"urlMetadata":{"queryParams":{"md5":"abc123","pid":"pid456"},'
        '"pii":"S1359645426006208","pdfExtension":".pdf",'
        '"path":"science/article/pii"}}</script>'
    )

    assert discover_pdf_url_from_html(
        "https://www-sciencedirect-com.eproxy.lib.hku.hk/science/article/pii/S1359645426006208",
        html,
    ) == (
        "https://www-sciencedirect-com.eproxy.lib.hku.hk/"
        "science/article/pii/S1359645426006208.pdf?md5=abc123&pid=pid456"
    )


def test_springer_uses_citation_pdf_url():
    html = '<meta name="citation_pdf_url" content="/content/pdf/article.pdf">'
    assert discover_pdf_url_from_html(
        "https://link-springer-com.eproxy.lib.hku.hk/article/10.1007/example",
        html,
    ) == "https://link-springer-com.eproxy.lib.hku.hk/content/pdf/article.pdf"


def test_acs_and_wiley_rank_dom_pdf_candidates():
    candidates = [
        {"text": "Purchase", "href": "/purchase"},
        {"text": "Open PDF", "href": "/doi/pdf/10.1021/example", "aria": "Open PDF"},
        {"text": "Supporting information", "href": "/support.pdf"},
    ]
    assert discover_pdf_url_from_candidates(
        "https://pubs-acs-org.eproxy.lib.hku.hk/doi/10.1021/example",
        candidates,
    ) == "https://pubs-acs-org.eproxy.lib.hku.hk/doi/pdf/10.1021/example"

    assert discover_pdf_url_from_candidates(
        "https://onlinelibrary-wiley-com.eproxy.lib.hku.hk/doi/10.1002/example",
        [{"text": "Download PDF", "href": "/doi/pdfdirect/10.1002/example"}],
    ) == "https://onlinelibrary-wiley-com.eproxy.lib.hku.hk/doi/pdfdirect/10.1002/example"


def test_dom_control_click_script_clicks_ranked_pdf_buttons():
    assert "data-scansci-pdf-clicked" in DOM_PDF_CONTROL_CLICK_JS
    assert ".click()" in DOM_PDF_CONTROL_CLICK_JS
    assert "supporting|supplement|appendix" in DOM_PDF_CONTROL_CLICK_JS
