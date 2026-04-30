# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

Streamlit app at [src/main.py](src/main.py) that estimates how many chip-molds are needed to craft a target chip in a gacha-style upgrade system. [tests/](tests/) and [README.md](README.md) are still empty.

Run the app: `uv run streamlit run src/main.py`

## Domain rules (encoded in [src/main.py](src/main.py))

- **5 chip types**, **levels 1–8**.
- **Combining is 3:1 everywhere _except_ the final step into the target chip, which is 2:1.** This is a per-craft rule, not a per-level rule — a lvl7 made as an intermediate (target=lvl8) costs `3 × lvl6 = 729` lvl1, but a lvl7 made as a final target costs `2 × lvl6 = 486` lvl1. So sub-target inventory is valued at `3^(K-1)`; target cost is `2 × 3^(N-2)`.
- **Per-mold roll:** lvl1 16.7% per type, lvl2 3% per type, lvl3 0.3% per type → 5 types sum to 100%.
- **Blessing pity:** counter 0–79 (the user never sees 80). Any natural lvl3 (any type) resets it. On the pull where the counter would tick from 79 to 80, a lvl3 of random type is forced instead and the counter resets to 0 — so a fully-unlucky cycle is exactly 80 pulls long.
- Three Monte-Carlo scenarios are reported (median of 1000 sims each); type roll is always random (1/5 target):
  - **Lucky:** every mold rolls lvl3.
  - **Real:** actual per-tier probabilities.
  - **Unlucky:** every mold rolls lvl1, blessing fires every 80 pulls (forced lvl3, random type).

## Toolchain

- **Package manager:** `uv` (see [uv.lock](uv.lock)). Do not use `pip` or `poetry`.
- **Python:** 3.14 (pinned via [.python-version](.python-version) and `requires-python = ">=3.14"` in [pyproject.toml](pyproject.toml)).
- **Lint/format:** `ruff` configured in [ruff.toml](ruff.toml) — note that lint rules are an explicit allow-list (`I`, `F401`, `PL`), not the ruff default. `target-version = "py314"`, line length 120.

## Common commands

```bash
# Install / sync deps (creates .venv if missing)
uv sync

# Add a runtime dep / dev dep
uv add <pkg>
uv add --dev <pkg>

# Run the entry point
uv run python src/main.py

# Tests
uv run pytest                                 # all tests
uv run pytest tests/path/to/test_x.py::test_y # single test
uv run pytest --cov --cov-report=xml          # coverage (pytest-cov is installed)

# Lint / format
uv run ruff check .
uv run ruff format .

# Pre-commit (config in .pre-commit-config.yaml runs ruff-check + ruff-format)
uv run pre-commit install
uv run pre-commit run --all-files
```

Note: the `ruff-check` pre-commit hook uses `--fix --exit-zero`, so it auto-fixes but never blocks the commit. Lint failures will only surface when you run `ruff check` manually or in CI.
