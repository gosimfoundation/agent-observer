#!/usr/bin/env bash
# Describes the shape of each configured secret without revealing it: length,
# line count, expected prefix, stray whitespace/quotes, and short SHA-256
# fingerprints (of the whole value and of each non-empty line) for comparison.
set -euo pipefail
python3 - <<'PY'
import hashlib
import os

def fp(text):
    return hashlib.sha256(text.encode()).hexdigest()[:8]

for name in ("SUPABASE_ACCESS_TOKEN", "KIMI_API_KEY", "GLM_API_KEY"):
    value = os.environ.get(name, "")
    lines = [line.strip() for line in value.splitlines()]
    stripped = value.strip()
    print(name, {
        "length": len(value),
        "lines": len(lines),
        "nonempty_lines": sum(1 for line in lines if line),
        "bare_dash_line": any(line == "-" for line in lines),
        "has_cr": "\r" in value,
        "inner_whitespace": any(c.isspace() for c in stripped),
        "quotes": any(c in stripped for c in "\"'`"),
        "non_ascii": any(ord(c) > 127 for c in value),
        "prefix_sbp": stripped.startswith("sbp_"),
        "prefix_sk": stripped.startswith("sk" + chr(45)),
        "dots": stripped.count("."),
        "fp_value": fp(stripped),
        "fp_lines": [fp(line) for line in lines if line][:12],
    })
PY
