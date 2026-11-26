#!/usr/bin/env python3
"""Detect a newer LibreChat release, classify it, and measure drift.

Reads the upstream release our main is on from .github/upstream.json, the
upstream tags (git ls-remote, no token) and upstream's published security
advisories (GitHub API through `gh`, a public endpoint).

This repository is public, and so are its issues, PRs and workflow logs. What
says which advisories affect us goes only to --sarif, which the workflow
uploads to code scanning (the Security tab, visible to people with write
access). The public outputs are:

  version     the newest upstream release newer than ours, or empty
  drift       ok | overdue (see DRIFT below)
  drift-line  one line, the same wording whatever the reason
  detection   version facts only (no advisories), for issue and PR bodies

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


SEVERITY_SCORE = {"critical": "9.5", "high": "8.0", "medium": "5.5", "low": "2.0"}
SEVERITY_LEVEL = {"critical": "error", "high": "error", "medium": "warning", "low": "note"}


def sarif(repo, current, latest, ours, fixed, old_severe):
    """One code-scanning alert per upstream advisory that affects our version,
    on the version line of .github/upstream.json. An advisory the next upload
    no longer reports (after the upgrade) is closed as fixed by GitHub."""
    pin = os.path.join(ROOT, ".github", "upstream.json")
    line = next((i for i, l in enumerate(open(pin), 1) if '"version"' in l), 1)
    fixed_ids = {h["ghsa"] for h in fixed}
    overdue_ids = {h["ghsa"] for h in old_severe}
    rules, results = [], []
    for h in ours:
        sev = h["severity"]
        rules.append({
            "id": h["ghsa"],
            "name": h["ghsa"],
            "shortDescription": {"text": h["summary"][:1000] or h["ghsa"]},
            "fullDescription": {"text": f"{h['summary']} (upstream advisory {h['ghsa']}, published {h['published']})"},
            "helpUri": h["url"],
            "help": {"text": f"Upstream advisory: {h['url']}"},
            "properties": {"security-severity": SEVERITY_SCORE.get(sev, "5.0"),
                           "tags": ["security", "upstream", sev]},
        })
        how = (f"fixed in {latest}: merge the upstream PR or resolve the upstream merge-conflict issue"
               if h["ghsa"] in fixed_ids else "not fixed in any upstream release yet")
        late = (" It has been public for more than %d days." % SECURITY_DAYS) if h["ghsa"] in overdue_ids else ""
        results.append({
            "ruleId": h["ghsa"],
            "level": SEVERITY_LEVEL.get(sev, "warning"),
            "message": {"text": f"LibreChat {current} is affected by {h['ghsa']} ({sev}): {h['summary']}. "
                                f"It is {how}.{late}"},
            "locations": [{"physicalLocation": {
                "artifactLocation": {"uri": ".github/upstream.json"},
                "region": {"startLine": line},
            }}],
            "partialFingerprints": {"ghsa": h["ghsa"]},
        })
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {
                "name": "upstream-advisories",
                "informationUri": f"https://github.com/{repo}/security/advisories",
                "rules": rules,
            }},
            "automationDetails": {"id": "upstream-advisories/"},
            "results": results,
        }],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--github-output")
    ap.add_argument("--sarif", help="write the advisories that affect us here (SARIF 2.1.0)")
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
        read_ok = True
    except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
        print(f"::warning::could not read upstream advisories: {e}", file=sys.stderr)
        ours, fixed, read_ok = [], [], False

    today = dt.date.today()
    old_severe = [
        h for h in ours
        if h["severity"] in ("critical", "high") and h["published"]
        and (today - dt.date.fromisoformat(h["published"])).days > SECURITY_DAYS
    ]
    # Overdue for either reason reads the same in public: which one it is,
    # and which advisories, is in the Security tab.
    overdue = bool(old_severe) or len(newer) > RELEASES_BEHIND
    drift = "overdue" if overdue else "ok"
    drift_line = (f"LibreChat {current} is overdue for an upstream update ({len(newer)} releases behind {latest})"
                  if overdue else f"LibreChat {current}, {len(newer)} releases behind")
    detection = {
        "repository": repo, "current": current, "version": latest, "behind": newer,
        "drift": drift, "drift_line": drift_line,
    }
    print(f"Upstream {repo}: ours {current}, newest release {latest or '(none newer)'}, "
          f"{len(newer)} behind; drift: {drift}")

    if args.sarif and read_ok:
        with open(args.sarif, "w") as f:
            json.dump(sarif(repo, current, latest, ours, fixed, old_severe), f)

    if args.github_output:
        with open(args.github_output, "a") as f:
            f.write(f"version={latest}\ndrift={drift}\ndrift-line={drift_line}\n")
            f.write(f"sarif={'yes' if args.sarif and read_ok else 'no'}\n")
            f.write(f"detection={json.dumps(detection, separators=(',', ':'))}\n")


if __name__ == "__main__":
    main()
