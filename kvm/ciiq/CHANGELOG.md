# Changelog

All notable changes to CIIQ are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
Versioning: [Semantic Versioning](https://semver.org/)

---

## [Unreleased]

---

## [0.1.0] — 2026-07-16

### Added
- **Flask backend** (`app.py`) — 12 REST endpoints:
  `GET /`, `/api/config`, `POST /api/token`,
  `/api/analyse/<project>`, `/api/analyse/all`, `/api/correlate`,
  `GET /api/runs`, `/api/run/<date>/suites`,
  `GET|DELETE /api/history`
- **IAM token cache** — auto-refresh, single-process, no duplicate auth calls
- **Per-project AI prompts** — PERSONAS for KVM, QEMU, libvirt (s390x-specific)
- **Cross-project correlation** — minimum fix set, dependency chain, triage order
- **Auto-split flat suite_logs** — `/api/analyse/all` accepts flat or nested format
- **Config** (`config.yaml`) — team-shared: 16 CI suites, model, region, log paths
- **Browser UI** (`templates/ciiq.html`) — git delta panel, suite tables,
  per-project result boxes, correlation, session history
- **`run.sh`** — dev / prod (gunicorn) / stop modes, auto-venv, auto-.env creation
- **`extract_delta.sh`** — tuxmaker helper: git log + diff + package versions → JSON
- **`.env.example`** — credentials template
- **`CONTRIBUTING.md`**, **`CHANGELOG.md`**, **`.gitignore`**
- **GitHub Actions CI** — lint (ruff) + smoke-test on Python 3.10–3.12

### Fixed
- watsonx API version updated to `2024-05-01` (was `2023-05-29`, returned 404)
- Default region fallback corrected from `eu-de` → `us-south`
  (CIIQ project `62f9a86d` and its WML instance are in `us-south`)

---

[Unreleased]: https://github.ibm.com/cheruiyo/Watsonx_challenge_2026/compare/ciiq-v0.1.0...HEAD
[0.1.0]: https://github.ibm.com/cheruiyo/Watsonx_challenge_2026/releases/tag/ciiq-v0.1.0
