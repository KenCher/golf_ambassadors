# Changelog

All notable changes to CIIQ are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
Versioning: [Semantic Versioning](https://semver.org/)

---

## [Unreleased]

---

## [0.2.0] — 2026-07-18

### Added
- **Local heuristic analysis engine** — fully offline, no IBM Cloud credentials required
  - `_scan_log()` — 20 error-signature regex patterns + 10 subsystem-attribution patterns
  - `_extract_commits()` — parses `git log --oneline` output into structured `[{sha, subject}]`
  - `analyse_project()` — generates 6-section Markdown report per project (introducing commits, root cause, subsystems, why affected, recommended fix, verification command)
  - `correlate_projects()` — cross-project cascade map, minimum revert set, triage order, tuxmaker reproducer
- **Dual-mode design**: watsonx edition fully preserved as `app-wx.py`, `run-wx.sh`, `config-wx.yaml`
- `/api/config` now returns `"engine": "local"` to distinguish editions
- All analysis responses include `"engine": "local"` field
- `config.yaml` — `watsonx:` block removed; clean minimal config

### Changed
- `app.py` — watsonx integration (IAM token, `wx_generate`, `WX_CFG`) replaced with local engine
- `run.sh` — credential check removed, timeout reduced from 180s → 60s (local calls are instant), banner updated
- `README.md` — fully rewritten to document local edition, dual-mode swap, API examples with local engine responses

### Removed (moved to `-wx` variants)
- `requests` dependency for IAM token exchange (no longer needed in local mode)
- All `WATSONX_API_KEY` / `WATSONX_PROJECT_ID` resolution logic

### Preserved (with `-wx` suffix)
- `app-wx.py` — original watsonx Granite 3.8B edition with IAM cache
- `run-wx.sh` — original run script with credential check
- `config-wx.yaml` — config with `watsonx:` block

---

## [0.1.0] — 2026-07-16

### Added
- **Flask backend** (`app.py`) — 12 REST endpoints with watsonx Granite integration
- **IAM token cache** — auto-refresh, single-process
- **Per-project AI prompts** — PERSONAS for KVM, QEMU, libvirt (s390x-specific)
- **Cross-project correlation** — minimum fix set, dependency chain, triage order
- **Auto-split flat suite_logs** — `/api/analyse/all` accepts flat or nested format
- **Config** (`config.yaml`) — team-shared: 16 CI suites, model, region, log paths
- **Browser UI** (`templates/ciiq.html`)
- **`run.sh`** — dev / prod / stop modes, auto-venv
- **`extract_delta.sh`** — tuxmaker git delta extractor
- **GitHub Actions CI** — lint + smoke-test on Python 3.10–3.12

### Fixed
- watsonx API version `2023-05-29` → `2024-05-01`
- Default region `eu-de` → `us-south` (CIIQ WML instance is in us-south)

---

[Unreleased]: https://github.ibm.com/cheruiyo/us-kvm-status/compare/ciiq-v0.2.0...HEAD
[0.2.0]: https://github.ibm.com/cheruiyo/us-kvm-status/compare/ciiq-v0.1.0...ciiq-v0.2.0
[0.1.0]: https://github.ibm.com/cheruiyo/us-kvm-status/releases/tag/ciiq-v0.1.0
