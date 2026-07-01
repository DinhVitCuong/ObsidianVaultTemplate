#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"
if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  PYTHON_BIN="python"
fi

if command -v graphify >/dev/null 2>&1; then
  echo "Running Graphify CLI..."
  graphify_args=()
  if [ -n "${GRAPHIFY_BACKEND:-}" ]; then
    graphify_args+=(--backend "${GRAPHIFY_BACKEND}")
  fi
  if [ -n "${GRAPHIFY_EXTRA_ARGS:-}" ]; then
    # Intentionally split extra args so operators can pass simple CLI flags.
    # Avoid shell metacharacters in GRAPHIFY_EXTRA_ARGS.
    read -r -a extra_args <<< "${GRAPHIFY_EXTRA_ARGS}"
    graphify_args+=("${extra_args[@]}")
  fi

  if [ -f "graphify-out/graph.json" ]; then
    graphify . --update --wiki "${graphify_args[@]}" || true
  else
    graphify . --wiki "${graphify_args[@]}" || true
  fi
else
  echo "Graphify CLI is not available. Install it once with: uv tool install graphifyy --force"
  echo "Continuing with local graph normalizer."
fi

echo "Building Codex retrieval graph outputs..."
"${PYTHON_BIN}" scripts/build_graphify_index.py
