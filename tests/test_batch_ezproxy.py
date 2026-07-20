from __future__ import annotations

from typer.testing import CliRunner

from scansci_pdf import main
from scansci_pdf import sources


def test_batch_ezproxy_cli_uses_free_sources_then_ezproxy(monkeypatch, tmp_path):
    calls = []
    input_file = tmp_path / "dois.txt"
    input_file.write_text("10.1234/example\n", encoding="utf-8")

    monkeypatch.setattr(
        sources,
        "batch_download",
        lambda identifiers, output_dir, **kwargs: calls.append(
            (identifiers, output_dir, kwargs)
        )
        or {"results": [], "succeeded": 0, "failed": 0},
    )

    result = CliRunner().invoke(
        main.app,
        ["batch", str(input_file), "--output", str(tmp_path), "--ezproxy"],
    )

    assert result.exit_code == 0, result.output
    assert calls == [
        (
            ["10.1234/example"],
            str(tmp_path),
            {"scihub_enabled": True, "use_ezproxy": True},
        )
    ]


def test_batch_ezproxy_falls_back_only_after_free_sources_fail(monkeypatch, tmp_path):
    config = {
        "output_dir": str(tmp_path),
        "cache_dir": str(tmp_path / "cache"),
        "batch_workers": 1,
        "batch_stagger_seconds": 0,
        "ezproxy_enabled": True,
        "ezproxy_login_url": "https://proxy.example.edu/login?url={url}",
    }
    calls = []

    monkeypatch.setattr(sources, "load_config", lambda: config.copy())
    monkeypatch.setattr("scansci_pdf.identifiers.validate_doi", lambda _doi: (True, ""))
    monkeypatch.setattr(sources, "_load_progress", lambda _batch_id: {})
    monkeypatch.setattr(sources, "_save_progress", lambda *_args: None)
    monkeypatch.setattr(sources, "_clear_progress", lambda *_args: None)

    def fake_download(identifier, _output_dir, **kwargs):
        calls.append((identifier, kwargs))
        if kwargs.get("strategy") == "ezproxy_only":
            return {"success": True, "identifier": identifier, "source": "EZProxy"}
        return {"success": False, "identifier": identifier, "source": "none"}

    monkeypatch.setattr(sources, "download", fake_download)

    result = sources.batch_download(
        ["10.1234/example"],
        tmp_path,
        use_ezproxy=True,
        resume=False,
    )

    assert result["succeeded"] == 1
    assert calls == [
        (
            "10.1234/example",
            {
                "scihub_enabled": True,
                "use_tor": False,
                "use_vpnsci": False,
                "_institutional": False,
                "strategy": "fastest",
            },
        ),
        (
            "10.1234/example",
            {
                "scihub_enabled": True,
                "strategy": "ezproxy_only",
                "rename": True,
                "ezproxy_interactive": True,
            },
        ),
    ]
