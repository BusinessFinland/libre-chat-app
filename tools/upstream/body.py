#!/usr/bin/env python3
"""Titles and bodies for the upstream autopilot's issues and PRs.

This repository is public, so these say nothing about which upstream
advisories affect us: that is in the Security tab (code scanning, tool
upstream-advisories), visible to people with write access. Every body carries
the same pointer to it, whatever the release, so its presence tells nothing.

  body.py <kind> --detection FILE [--run-url URL] [--owner LOGIN]
          [--conflicts FILE] [--branch NAME] [--issue N] [--draft true|false]

kinds: issue-title issue pr-title pr conflict-title conflict drift-title drift
"""
import argparse
import json


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kind")
    ap.add_argument("--detection", required=True)
    ap.add_argument("--run-url", default="")
    ap.add_argument("--owner", default="")
    ap.add_argument("--conflicts", default="")
    ap.add_argument("--branch", default="")
    ap.add_argument("--issue", default="")
    ap.add_argument("--draft", default="false")
    ap.add_argument("--repo", default="")
    a = ap.parse_args()
    d = json.load(open(a.detection))
    v, cur, upstream = d["version"], d["current"], d["repository"]
    mention = f"@{a.owner} " if a.owner else ""
    run = f"[run]({a.run_url})" if a.run_url else "the upstream workflow"
    compare = f"https://github.com/{upstream}/compare/{cur}...{v}"
    notes = f"https://github.com/{upstream}/releases/tag/{v}"
    security = ("Upstream security advisories that affect our version are in this repository's "
                "**Security** tab (code scanning, tool `upstream-advisories`), for people with write access.")

    if a.kind == "issue-title":
        print(f"LibreChat {v} released")
    elif a.kind == "issue":
        print(f"""{mention}LibreChat **{v}** is out; `main` is on **{cur}** ({len(d['behind'])} releases behind).

[Release notes]({notes}) · [changes {cur}...{v}]({compare}) · detected by {run}

{security}

The autopilot merges {v} into `main` on a branch. A clean merge becomes a PR that CI tests; conflicts become a triage issue listing the files. Either one links back here.
""")
    elif a.kind == "pr-title":
        print(f"upstream: LibreChat {v}")
    elif a.kind == "pr":
        draft = a.draft == "true"
        print(f"""Merges upstream LibreChat **{v}** into `main` (from **{cur}**). Opened by the upstream autopilot (`.github/workflows/upstream.yml`) from {run}.{(' Closes #' + a.issue + '.') if a.issue else ''}

[Release notes]({notes}) · [upstream changes {cur}...{v}]({compare})

{security}

## Review

- The merge applied without conflicts, but our changes can still interact with upstream's. Read the release notes for **breaking changes**, especially:
  - a new `librechat.yaml` `version`: update the config in the deployment (libre-chat-infra: `librechat/manifests/base/librechat.yaml` for AKS, the root `librechat-<env>.yaml` for Container Apps)
  - new required environment variables
  - database migrations (`config/` scripts named in the notes)
- CI runs the tests and the image build on this branch.{' This PR was opened with `GITHUB_TOKEN`, which starts no workflows: close and reopen it, or push an empty commit, to run CI. Setting up the upstream App (README "Upstream autopilot") removes this step.' if draft else ''}
- **Merge with "Create a merge commit", never squash.** A squash drops upstream's history from `main`, so the next upstream merge conflicts on everything this one already resolved.

After the merge, `main` deploys to AKS dev (aks-dev-image.yml); test and prod are promoted from the manifests repository.
""")
    elif a.kind == "conflict-title":
        print(f"LibreChat {v}: upstream merge conflicts")
    elif a.kind == "conflict":
        files = [l.strip() for l in open(a.conflicts) if l.strip()] if a.conflicts else []
        listing = "\n".join(f"- `{f}`" for f in files[:200]) or "- (none listed)"
        if len(files) > 200:
            listing += f"\n- … and {len(files) - 200} more"
        print(f"""{mention}Merging upstream LibreChat **{v}** into `main` (on **{cur}**) conflicts in **{len(files)}** files, so the autopilot opened no PR. A person, or a coding agent, resolves them on a branch. Found by {run}.{(' Tracking issue: #' + a.issue + '.') if a.issue else ''}

{security}

### Conflicting files

{listing}

### Resolve

```bash
git switch -c upstream/librechat-{v} origin/main
git remote add upstream https://github.com/{upstream}.git 2>/dev/null; git fetch upstream tag {v} --no-tags
git merge --no-ff {v}
# resolve, keeping our changes (README "Upgrading LibreChat", Confluence lists each one and why)
# set .github/upstream.json "version" to "{v}"
git commit && git push -u origin upstream/librechat-{v}
```

Open the PR against `main` and merge it with **"Create a merge commit"**, not squash. A squash drops upstream's history, so every later upstream merge would conflict on these same files again.

Each conflict is a place where we changed upstream code. Where the change can be configuration instead (`librechat.yaml`, environment), or can be sent upstream, doing that removes the conflict for good.
""")
    elif a.kind == "drift-title":
        print(f"LibreChat {cur} is overdue for an upstream update")
    elif a.kind == "drift":
        print(f"""{mention}{d['drift_line']}. Detected by {run}.

The newest release is **{v or cur}**. This issue stays open, and the upstream workflow fails, until `main` is updated. The tracking issue, and the PR or conflict issue for {v or 'the release'}, say what is in the way.

{security}
""")
    else:
        raise SystemExit(f"unknown kind {a.kind}")


if __name__ == "__main__":
    main()
