# Security Policy

## Supported versions

Releases are numbered MAJOR.MINOR.PATCH (see [CHANGELOG.md](CHANGELOG.md)). Only the latest release receives security fixes; there are no maintenance branches for older versions. If you use the claude.ai ZIP, upload the newest one from the [Releases](https://github.com/alexccastilho/principal-secops-dev-token-optimizer/releases/latest) page.

## What counts as a vulnerability here

This project is a skill: instructions Claude follows, plus a scanner script. Besides ordinary bugs in the Python code, these are security issues and should be reported privately:

- **The skill steering Claude toward insecure code**: an instruction or reference example that produces SQL injection, missing access control, a weak password hash, a secret in code, or similar, when followed as written.
- **The scanner leaking a secret**: any case where `scripts/revisar_codigo.py` prints the value of a password, token or key, in text or JSON output.
- **A scanner false negative on a critical pattern** that the skill relies on the scanner to catch (a hardcoded secret, SQL built from user input, unescaped output of user input).
- **Prompt injection that defeats the trust rule**: content in a project file, log or comment that makes the skill ignore its own rules, skip the pre-delivery gate or run a command.
- **Refactor mode removing security code**: a case where following `references/refatoracao-completa.md` deletes an authorization check, deny-on-failure handling or a security test.

A false positive of the scanner, or advice that is merely suboptimal, is a regular bug: open a normal issue.

## Reporting a vulnerability

**Please do not open a public issue for a security vulnerability.**

Use GitHub's private vulnerability reporting instead: on this repository's GitHub page, go to the **Security** tab, then **Report a vulnerability**. This opens a private conversation with the maintainer that stays hidden from the public until it is resolved. No email address is published for this purpose.

If that tab is not available to you, open a regular issue asking for a private reporting channel, without any vulnerability details in the issue itself.

Please include the skill version, where you use it (Claude Code plugin, manual copy or claude.ai), the prompt or file that triggers the problem, and what happened. Replace any real secret or personal data with fake values before sending.

## What to expect

You will get an acknowledgement as soon as the maintainer sees the report. A confirmed issue is fixed in a new release, with credit in the changelog unless you prefer otherwise.

## Automated checks

Every push and pull request runs the test suite on Linux and Windows and is scanned by CodeQL (the Python code and the GitHub Actions workflows, with the `security-and-quality` queries, plus a weekly run). Dependabot keeps the pinned actions current. The only runtime code is the scanner, which uses the Python standard library and makes no network calls.

## Insecure patterns in the references

The files in `skills/principal-secops-dev-token-optimizer/references/` name insecure patterns (`eval` on user data, SQL built from strings, MD5 for passwords and so on), and a few show a short example of what not to do, so Claude can recognize them. Naming a pattern to avoid is not a vulnerability. If a reference recommends something insecure as the right way, that is one: report it as above.
