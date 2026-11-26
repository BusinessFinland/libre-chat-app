#!/usr/bin/env python3
"""Detect a newer LibreChat release, classify it, and measure drift.

Reads the upstream release our main is on from .github/upstream.json, the
upstream tags (git ls-remote, no token) and upstream's published security
advisories (GitHub API through `gh`, a public endpoint), and writes:

  version     the newest upstream release newer than ours, or empty
  security    true when a published advisory affects our version and is
              fixed by `version`; "unknown" when the advisories could not be
              read (treated as security until they can)
  labels      upstream[,security]
  drift       ok | overdue (see DRIFT below)
  drift-line  one line saying why
  detection   everything above as JSON, for the issue and PR bodies

Upstream marks every GitHub release as a prerelease, final versions included,
so releases are the tags vX.Y.Z; -rcN tags are ignored.

DRIFT: overdue when a critical or high advisory affecting our version has been
public for more than SECURITY_DAYS days, or when we are more than
RELEASES_BEHIND releases behind.

  tools/upstream/detect.py [--github-output FILE]
"""
import argparse
import datetime as dt
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from versions import in_range, is_release, parse  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SECURITY_DAYS = 14
RELEASES_BEHIND = 3


def upstream_tags(repo):
    out = subprocess.run(
        ["git", "ls-remote", "--tags", "--refs", f"https://github.com/{repo}.git"],
        check=True, capture_output=True, text=True,
    ).stdout
    tags = [line.split("refs/tags/", 1)[1] for line in out.splitlines() if "refs/tags/" in line]
    return sorted((t for t in tags if is_release(t)), key=parse)


def advisories(repo):
    out = subprocess.run(
        ["gh", "api", "--paginate", "--slurp",
         f"repos/{repo}/security-advisories?state=published&per_page=100"],
        check=True, capture_output=True, text=True,
    ).stdout
    return [a for page in json.loads(out) for a in page]


def affecting(advs, version, fixed_by=None):
    """Advisories whose vulnerable range contains `version` (and, given
    fixed_by, that `fixed_by` is outside of)."""
    hits = {}
    for a in advs:
        for v in a.get("vulnerabilities") or []:
            spec = v.get("vulnerable_version_range")
            if not spec:
                continue
            try:
                if in_range(version, spec) and (fixed_by is None or not in_range(fixed_by, spec)):
                    hits[a["ghsa_id"]] = {
                        "ghsa": a["ghsa_id"],
                        "severity": a.get("severity") or "unknown",
                        "summary": a.get("summary", ""),
                        "published": (a.get("published_at") or "")[:10],
                        "url": a.get("html_url", ""),
                    }
            except ValueError as e:
                print(f"::warning::{a['ghsa_id']}: {e}", file=sys.stderr)
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return sorted(hits.values(), key=lambda h: (order.get(h["severity"], 9), h["ghsa"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--github-output")
    args = ap.parse_args()

    pin = json.load(open(os.path.join(ROOT, ".github", "upstream.json")))
    repo, current = pin["repository"], pin["version"]

    tags = upstream_tags(repo)
    newer = [t for t in tags if parse(t) > parse(current)]
    latest = newer[-1] if newer else ""

    try:
        advs = advisories(repo)
        ours = affecting(advs, current)
        fixed = affecting(advs, current, fixed_by=latest) if latest else []
        security = "true" if fixed else "false"
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"::warning::could not read upstream advisories: {e}", file=sys.stderr)
        ours, fixed, security = [], [], "unknown"

    today = dt.date.today()
    old_severe = [
        h for h in ours
        if h["severity"] in ("critical", "high") and h["published"]
        and (today - dt.date.fromisoformat(h["published"])).days > SECURITY_DAYS
    ]
    if old_severe:
        drift = "overdue"
        drift_line = (f"LibreChat {current} has {len(old_severe)} critical/high advisories public for "
                      f"more than {SECURITY_DAYS} days (fixed in {latest or 'a newer release'})")
    elif len(newer) > RELEASES_BEHIND:
        drift = "overdue"
        drift_line = f"LibreChat {current} is {len(newer)} releases behind {latest} (limit {RELEASES_BEHIND})"
    else:
        drift, drift_line = "ok", f"LibreChat {current}, {len(newer)} releases behind"

    labels = "upstream" + (",security" if security != "false" else "")
    detection = {
        "repository": repo, "current": current, "version": latest, "behind": newer,
        "security": security, "fixed": fixed, "affecting": ours,
        "drift": drift, "drift_line": drift_line,
    }

    severities = {}
    for h in fixed:
        severities[h["severity"]] = severities.get(h["severity"], 0) + 1
    print(f"Upstream {repo}: ours {current}, newest release {latest or '(none newer)'}, "
          f"{len(newer)} behind; advisories fixed by it: {severities or 'none'}; drift: {drift_line}")

    if args.github_output:
        with open(args.github_output, "a") as f:
            f.write(f"version={latest}\nsecurity={security}\nlabels={labels}\n")
            f.write(f"drift={drift}\ndrift-line={drift_line}\n")
            f.write(f"detection={json.dumps(detection, separators=(',', ':'))}\n")


if __name__ == "__main__":
    main()
