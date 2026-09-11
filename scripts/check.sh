#!/usr/bin/env bash
# Repo-wide check: unit tests -> API tests -> strict docs build -> optional Rhino 8 oracle suite.
# Usage: scripts/check.sh        (RHINO_ORACLE=1 scripts/check.sh to include the oracle suite)
set -euo pipefail
root="$(cd "$(dirname "$0")/.." && pwd)"
py="$root/.venv/Scripts/python.exe"; [ -x "$py" ] || py="$root/.venv/bin/python"

echo "== unit tests (tests/)"
"$py" -m unittest discover -s "$root/tests" -v
echo "== API tests (pyhopper-web/api/test_*.py)"
"$py" -m unittest discover -s "$root/pyhopper-web/api" -p "test_*.py" -v
echo "== docs (mkdocs build --strict)"
DISABLE_MKDOCS_2_WARNING=true "$py" -m mkdocs build --strict -f "$root/mkdocs.yml"
if [ "${RHINO_ORACLE:-0}" = "1" ]; then
  echo "== Rhino 8 oracle suite (rhino-test/oracle)"
  "$root/rhino-test/.venv/Scripts/python.exe" -m unittest discover -s "$root/rhino-test/oracle" -v
fi
echo "== all checks passed"
