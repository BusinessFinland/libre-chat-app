#!/usr/bin/env python3
"""Titles and bodies for the upstream autopilot's issues and PRs.

  body.py <kind> --detection FILE [--run-url URL] [--owner LOGIN]
          [--conflicts FILE] [--branch NAME] [--issue N] [--draft true|false]

kinds: issue-title issue pr-title pr conflict-title conflict drift-title drift
"""
import argparse
import json

SEV_ICON = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "⚪"}


def advisory_table(items, limit=60):
    if not items:
        return "_None._\n"
    rows = ["| | Advisory | Severity | Published | Summary |", "|---|---|---|---|---|"]
    for h in items[:limit]:
        summary = h["summary"].replace("|", "\\|")
        rows.append(f"| {SEV_ICON.get(h['severity'], '')} | [{h['ghsa']}]({h['url']}) | {h['severity']} "
                    f"| {h['published']} | {summary} |")
    if len(items) > limit:
        rows.append(f"| | … and {len(items) - limit} more | | | |")
    return "\n".join(rows) + "\n"


def counts(items):
    c = {}
    for h in items:
        c[h["severity"]] = c.get(h["severity"], 0) + 1
    order = ["critical", "high", "medium", "low"]
    return ", ".join(f"{c[s]} {s}" for s in order if s in c) or "none"


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
    a = ap.parse_args()
    d = json.load(open(a.detection))
    v, cur, repo = d["version"], d["current"], d["repository"]
    sec = d["security"] != "false"
    mention = f"@{a.owner} " if a.owner else ""
    run = f"[run]({a.run_url})" if a.run_url else "the upstream workflow"
    compare = f"https://github.com/{repo}/compare/{cur}...{v}"
    notes = f"https://github.com/{repo}/releases/tag/{v}"

    if a.kind == "issue-title":
        print(f"LibreChat {v} released")
    elif a.kind == "issue":
        print(f"""{mention}LibreChat **{v}** is out; `main` is on **{cur}** ({len(d['behind'])} releases behind).

{'**Security release**: it fixes ' + counts(d['fixed']) + ' advisories that affect our version. Upgrade within days.' if d['security'] == 'true' else ''}{'The advisories could not be read, so this counts as a security release until they can.' if d['security'] == 'unknown' else ''}

[Release notes]({notes}) · [changes {cur}...{v}]({compare}) · detected by {run}

### Advisories that affect {cur} and are fixed in {v}

{advisory_table(d['fixed'])}
The autopilot merges {v} into `main` on a branch. A clean merge becomes a PR that CI tests; conflicts become a triage issue listing the files. Either one links back here.
""")
    elif a.kind == "pr-title":
        print(f"upstream: LibreChat {v}" + (" (security)" if sec else ""))
    elif a.kind == "pr":
        draft = a.draft == "true"
        print(f"""Merges upstream LibreChat **{v}** into `main` (from **{cur}**). Opened by the upstream autopilot (`.github/workflows/upstream.yml`) from {run}.{(' Closes #' + a.issue + '.') if a.issue else ''}

{'**Security release**: fixes ' + counts(d['fixed']) + ' advisories that affect ' + cur + '.' if sec else ''}

[Release notes]({notes}) · [upstream changes {cur}...{v}]({compare})

## Review

- The merge applied without conflicts, but our changes can still interact with upstream's. Read the release notes for **breaking changes**, especially:
  - a new `librechat.yaml` `version`: update the config in the deployment (aks-librechat-manifests `librechat/manifests/base/librechat.yaml`; libre-chat-infra for Container Apps)
  - new required environment variables
  - database migrations (`config/` scripts named in the notes)
- CI runs the tests and the image build on this branch.{' This PR was opened with `GITHUB_TOKEN`, which starts no workflows: close and reopen it, or push an empty commit, to run CI. Setting up the upstream App (README "Upstream autopilot") removes this step.' if draft else ''}
- **Merge with "Create a merge commit", never squash.** A squash drops upstream's history from `main`, so the next upstream merge conflicts on everything this one already resolved.

After the merge, `main` deploys to AKS dev (aks-dev-image.yml); test and prod are promoted from the manifests repository.

### Advisories fixed

{advisory_table(d['fixed'])}""")
    elif a.kind == "conflict-title":
        print(f"LibreChat {v}: upstream merge conflicts")
    elif a.kind == "conflict":
        files = [l.strip() for l in open(a.conflicts) if l.strip()] if a.conflicts else []
        listing = "\n".join(f"- `{f}`" for f in files[:200]) or "- (none listed)"
        if len(files) > 200:
            listing += f"\n- … and {len(files) - 200} more"
        print(f"""{mention}Merging upstream LibreChat **{v}** into `main` (on **{cur}**) conflicts in **{len(files)}** files, so the autopilot opened no PR. A person, or a coding agent, resolves them on a branch. Found by {run}.{(' Tracking issue: #' + a.issue + '.') if a.issue else ''}

{'**Security release**: it fixes ' + counts(d['fixed']) + ' advisories that affect ' + cur + '. Prioritise this.' if sec else ''}

### Conflicting files

{listing}

### Resolve

```bash
git switch -c upstream/librechat-{v} origin/main
git remote add upstream https://github.com/{repo}.git 2>/dev/null; git fetch upstream tag {v} --no-tags
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

### Advisories that affect {cur}

{advisory_table(d['affecting'])}""")
    else:
        raise SystemExit(f"unknown kind {a.kind}")


if __name__ == "__main__":
    main()
