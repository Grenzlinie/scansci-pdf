# ADR-0003: Keep institutional credentials local

- Status: Accepted
- Date: 2026-07-20

## Context

EZProxy sessions can be reused, but their Cookies represent institutional
access. A leaked Cookie or signed PDF URL can disclose account context or
temporarily grant access beyond the user's machine.

## Decision

The browser loads Cookies from the configured local cache before navigation
and refreshes them after authentication or download. Writes use a temporary
file followed by an atomic replace. On POSIX systems, the resulting file mode
is `0600`. Windows access control is provided by the local account's ACLs;
the POSIX mode bits reported by `stat` are not an access-control guarantee
there and are deliberately not used as a Windows security check.

Cookie values, passwords, signed query strings, and authentication tokens are
prohibited from logs, Git history, CI inputs, artifacts, screenshots, and
failure reports. Logs may include only a redacted URL containing scheme, host,
and path.

HKU live tests use a private self-hosted runner whose local user profile owns
the Cookie cache. GitHub-hosted runners and repository secrets must not carry
the Cookie file. The runner must be dedicated to trusted repository code and
must not accept pull-request jobs from untrusted forks.

## Consequences

Login can survive between local runs without putting institutional credentials
in GitHub. A self-hosted runner requires manual account maintenance and
revocation when access changes. Failed live runs do not upload browser state
or PDFs.
