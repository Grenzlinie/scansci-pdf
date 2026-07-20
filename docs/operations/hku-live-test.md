# Run the HKU live acceptance test

This procedure verifies institutional access without putting HKU credentials
or downloaded PDFs in GitHub. It is for a trusted maintainer operating a
private self-hosted macOS runner with a visible desktop session.

## Prepare the runner

1. Register a dedicated self-hosted runner for this repository with labels
   `self-hosted`, `macOS`, and `hku-ezproxy`.
2. Create the protected GitHub environment `hku-live` and restrict deployment
   approval to trusted maintainers.
3. On the runner, install CloakBrowser and complete login locally:

   ```bash
   scansci-pdf login --login-type ezproxy --manual-confirm
   ```

4. Confirm `~/.scansci-pdf/cache/ezproxy_cookies.json` is owned by the runner
   account and has mode `0600`.
5. Disable pull-request workflows on this runner. It must execute only trusted
   branches from this repository.

Do not copy the Cookie into GitHub Secrets. Do not add it to runner diagnostic
bundles or backups shared outside the account boundary.

## Run the workflow

Open **Actions → HKU EZProxy live acceptance → Run workflow**. Keep the default
DOI or enter another DOI that the institution is authorized to access. Approve
the `hku-live` environment deployment, then complete any publisher challenge
in the visible browser.

The run passes when exactly one PDF is saved, its first five bytes are
`%PDF-`, it has at least one readable page, and its title metadata is printed
without any signed URL or Cookie value. The temporary PDF is deleted in the
workflow's final step and is never uploaded as an artifact.

## Handle failures

- Missing Cookie: log in locally again; do not upload the Cookie.
- Verification timeout: rerun with an attended desktop session.
- Invalid PDF: retain only redacted logs and reproduce locally.
- Runner compromise or accidental secret output: remove the runner, revoke the
  institutional session, delete affected logs, and authenticate again.
