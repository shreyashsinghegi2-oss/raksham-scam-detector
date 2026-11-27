# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). The package version in
`pyproject.toml` is 0.1.0 and no release has been tagged yet, so everything
below is listed by date under "Unreleased".

## [Unreleased]

### 2026-11-26

- Added issue forms (bug report, misclassified message, feature request), disabled blank issues, pointed security reports to private advisories and added a pull request template.

### 2026-11-25

- Added a Mermaid architecture diagram to the README covering training, the two serving paths and the CLI.

### 2026-11-24

- Added mypy type checking (config, `make typecheck`, CI step) and type hints for the package.
- Fixed the findings mypy raised in `export` and `predict`. No behaviour change.

### 2026-11-23

- Added ruff linting, a pre-commit config and a Makefile (install, train, test, lint, format, serve, clean).
- Fixed the lint findings ruff raised. No behaviour change.

### 2026-11-21

- Added a model card (`docs/MODEL_CARD.md`) covering intended use, data, metrics and limits.
- Added tests for empty, very long, emoji and mixed-script inputs for the scorer and the API.
- Added the MIT licence and CI badges to the README.
- Added a contributing guide and a security policy.
- CI now runs tests on Python 3.10 and 3.12 and builds the web app.

### 2026-10-24

- Trained on real Indian SMS and scam reports and deployed the new model.
- Added the v2 architecture design (`docs/ARCHITECTURE_V2.md`) and refreshed metrics in `reports/`.

### 2026-10-23

- Added the Raksham scam detector: training code, API and Vercel app.
- Redesigned the web page several times, ending with a React and Tailwind page with a risk meter, link checks, telemetry and history.
- The scorer now reads fancy-font letters as plain text before scoring.
- Added a new-message test set.
- Deployed the model fitted with the SMS Spam Collection; the page starts in strict mode.
