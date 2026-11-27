# Contributing

Contributions that make the detector more honest or more accurate are welcome.

## Setup

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"
.venv/bin/pytest
```

A `Makefile` wraps the common commands: `make install`, `make test`, `make lint`, `make typecheck`, `make train` and `make serve` (`make help` lists them). Code is linted with [ruff](https://docs.astral.sh/ruff/) (`make lint`) and type-checked with [mypy](https://mypy.readthedocs.io/) (`make typecheck`); to run it before every commit, use `pip install pre-commit && pre-commit install`.

Tests that need the training data skip themselves when it is missing, so the suite runs on a clean clone. CI runs lint, the type check and tests on Python 3.10 and 3.12, and builds the web app in `web/`.

## What helps most

1. **Real, consented messages**, especially genuine bank, salary, premium and refund notices, and Hinglish. This is the model's weakest area (see "Limits" in the README).
2. **Evaluation on unseen templates.** Do not report random-split scores: the dataset is built from templates, so random splits leak and inflate results.
3. **Tests** for anything that changes scoring, thresholds or the API contract.

## Rules

- Do not commit datasets you do not have the right to redistribute. Check the licence first and document the source in `data/external/README.md`.
- Never commit real personal messages, phone numbers or account details.
- Keep claims in the README tied to a number in `reports/`.

## Pull requests

Keep them small and focused. State what changed, how you measured it, and what got worse, if anything. Add a line under "Unreleased" in `CHANGELOG.md` for any change a user or contributor would notice.
