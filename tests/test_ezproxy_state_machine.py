from __future__ import annotations

import base64
import json
import stat
import sys
import types

from scansci_pdf.sources import ezproxy


PDF_BYTES = b"%PDF-1.7\n" + (b"full article\n" * 600)


class SlowArticlePage:
    def __init__(self) -> None:
        self.url = ""
        self.ticks = 0
        self.on_pdf_page = False
        self._response_handler = None

    def on(self, event, handler) -> None:
        if event == "response":
            self._response_handler = handler

    def goto(self, url, **_kwargs) -> None:
        if "/login?" in url:
            self.url = "https://link-springer-com.eproxy.lib.hku.hk/article/example"
        else:
            self.url = url
            self.on_pdf_page = True

    def title(self) -> str:
        return "Loading article" if not self.on_pdf_page else "PDF viewer"

    def content(self) -> str:
        if self.on_pdf_page:
            return "<html><body>PDF viewer</body></html>"
        if self.ticks < 4:
            return "<html><body>Loading article</body></html>"
        return '<meta name="citation_pdf_url" content="/content/pdf/article.pdf">'

    def evaluate(self, script, *args):
        if "querySelectorAll" in script:
            return []
        if "arrayBuffer" in script and self.on_pdf_page:
            return base64.b64encode(PDF_BYTES).decode("ascii")
        return ""

    def tick(self) -> None:
        self.ticks += 1


class FakeContext:
    def __init__(self, page: SlowArticlePage) -> None:
        self.page = page
        self.loaded_cookies = []

    def new_page(self) -> SlowArticlePage:
        return self.page

    def add_cookies(self, cookies) -> None:
        self.loaded_cookies = cookies

    def cookies(self):
        return [
            {
                "name": "ezproxy",
                "value": "refreshed-cookie",
                "domain": ".eproxy.lib.hku.hk",
                "path": "/",
            }
        ]


class FakeBrowser:
    def __init__(self, page: SlowArticlePage) -> None:
        self.context = FakeContext(page)
        self.closed = False

    def new_context(self) -> FakeContext:
        return self.context

    def close(self) -> None:
        self.closed = True


def test_slow_article_uses_in_page_fetch_and_refreshes_cookie_cache(monkeypatch, tmp_path):
    page = SlowArticlePage()
    browser = FakeBrowser(page)
    monkeypatch.setitem(
        sys.modules,
        "cloakbrowser",
        types.SimpleNamespace(launch=lambda **_kwargs: browser),
    )
    monkeypatch.setattr(
        ezproxy.requests,
        "head",
        lambda *_args, **_kwargs: types.SimpleNamespace(
            url="https://link.springer.com/article/example"
        ),
    )
    monkeypatch.setattr(ezproxy.time, "sleep", lambda _seconds: page.tick())

    cookie_dir = tmp_path / "cache"
    cookie_dir.mkdir()
    cookie_file = cookie_dir / "ezproxy_cookies.json"
    cookie_file.write_text(
        json.dumps(
            [
                {
                    "name": "ezproxy",
                    "value": "cached-cookie",
                    "domain": ".eproxy.lib.hku.hk",
                    "path": "/",
                }
            ]
        ),
        encoding="utf-8",
    )

    output_path = tmp_path / "paper.pdf"
    result = ezproxy.try_ezproxy(
        "10.1007/example",
        output_path,
        {
            "ezproxy_enabled": True,
            "ezproxy_login_url": "https://proxy.example.edu/login?url={url}",
            "cache_dir": str(cookie_dir),
            "ezproxy_challenge_timeout": 15,
        },
    )

    assert result is not None and result["success"] is True
    assert output_path.read_bytes() == PDF_BYTES
    assert browser.context.loaded_cookies[0]["value"] == "cached-cookie"
    assert json.loads(cookie_file.read_text(encoding="utf-8"))[0]["value"] == "refreshed-cookie"
    assert stat.S_IMODE(cookie_file.stat().st_mode) == 0o600
    assert browser.closed is True


class BlankPage:
    url = "https://publisher-com.eproxy.lib.hku.hk/loading"

    @staticmethod
    def title() -> str:
        return "Loading"

    @staticmethod
    def content() -> str:
        return "<html><body>Loading</body></html>"

    @staticmethod
    def evaluate(_script):
        return []


class TtyInput:
    @staticmethod
    def isatty() -> bool:
        return True


def test_interactive_timeout_can_continue_then_skip(monkeypatch):
    answers = iter(["", "skip"])
    prompts = []
    monkeypatch.setattr(ezproxy.sys, "stdin", TtyInput())
    monkeypatch.setattr(
        "builtins.input",
        lambda prompt: prompts.append(prompt) or next(answers),
    )
    monkeypatch.setattr(ezproxy.time, "sleep", lambda _seconds: None)

    result = ezproxy._wait_for_pdf_link(
        BlankPage(),
        [],
        {"ezproxy_challenge_timeout": 2, "_ezproxy_interactive": True},
    )

    assert result == ""
    assert len(prompts) == 2


def test_noninteractive_timeout_does_not_prompt(monkeypatch):
    monkeypatch.setattr(ezproxy.time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(
        "builtins.input",
        lambda _prompt: (_ for _ in ()).throw(AssertionError("must not prompt")),
    )

    result = ezproxy._wait_for_pdf_link(
        BlankPage(),
        [],
        {"ezproxy_challenge_timeout": 2, "_ezproxy_interactive": False},
    )

    assert result == ""
