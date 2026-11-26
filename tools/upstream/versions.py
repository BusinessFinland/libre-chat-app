"""Version parsing and advisory range matching for LibreChat's upstream tags.

Stdlib only: the upstream workflow runs this before any npm install.
"""
import re

TAG = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:-rc(\d+))?$")


def parse(v):
    """'v0.8.9' -> (0, 8, 9, inf); '0.8.9-rc1' -> (0, 8, 9, 1). A release sorts after its rcs."""
    m = TAG.match(v.strip())
    if not m:
        raise ValueError(f"not a LibreChat version: {v!r}")
    major, minor, patch, rc = m.groups()
    return (int(major), int(minor), int(patch), float("inf") if rc is None else int(rc))


def is_release(tag):
    m = TAG.match(tag)
    return bool(m) and m.group(4) is None


OPS = {
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "=": lambda a, b: a == b,
}


def in_range(version, spec):
    """GitHub advisory range: '>= 0.7.9, <= 0.8.8, < 0.8.9' (every clause must
    hold), 'v0.0.6 - v0.7.7' (inclusive), or alternatives joined by '||'."""
    if "||" in spec:
        return any(in_range(version, part) for part in spec.split("||"))
    hyphen = re.match(r"^\s*(\S+)\s+-\s+(\S+)\s*$", spec)
    if hyphen:
        spec = f">= {hyphen.group(1)}, <= {hyphen.group(2)}"
    v = parse(version)
    for clause in spec.split(","):
        clause = clause.strip()
        if not clause:
            continue
        m = re.match(r"^(<=|>=|<|>|=)?\s*(\S+)$", clause)
        if not m:
            raise ValueError(f"unknown range clause {clause!r}")
        op, bound = m.group(1) or "=", m.group(2)
        if not OPS[op](v, parse(bound)):
            return False
    return True
