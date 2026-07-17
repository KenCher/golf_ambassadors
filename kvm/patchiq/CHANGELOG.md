# Changelog

All notable changes to PatchIQ are documented here.
This project follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.2.0] — 2026-07-18

### Added
- **Local heuristic engine** (`analyzer.py`) — fully offline patch review with no external API or credentials required
  - `local_review()` analyses added lines with 6 pattern banks (security, locking, memory, error-path, ioctl, test)
  - Generates contextual summary (patch size, layer, focus areas) and up to 5 targeted suggestions
  - Pattern co-occurrence logic: allocation-without-error-path, TOCTOU locking, large-patch-without-tests, pure-addition smell
- **`run_review.sh`** — updated shell wrapper for local engine (no `.env` sourcing, no credential warnings)
- **Dual-mode design**: original watsonx engine preserved as `analyzer-wx.py` / `run_review-wx.sh`
- `requirements.txt` now empty for local mode (stdlib only, no `requests` needed)

### Changed
- `analyzer.py` now uses `local_review()` instead of `ai_review()` — zero external dependencies
- Module docstring updated to reflect local pipeline
- `run_review.sh` banner updated: "Local Patch Reviewer (no API required)"
- `README.md` updated to document both editions, local engine patterns, and swap instructions

### Preserved (with `-wx` suffix)
- `analyzer-wx.py` — original watsonx Granite 3.8B edition
- `run_review-wx.sh` — original shell wrapper with `.env` auto-load

---

## [0.1.0] — 2026-07-14

### Added
- Initial public release for the watsonx Challenge 2026
- Four-stage review pipeline: `parse_diff` → `detect_layer` → `run_rules` → `ai_review`
- 14 style rules: K001–K004 (kernel/KVM), Q001–Q004 (QEMU), L001–L003 (libvirt), U001–U003 (universal)
- 68-test suite covering every rule (positive + negative), diff parser, scoring, end-to-end pipeline
- watsonx Granite 3.8B AI narrative review (optional, IBM Cloud credentials)
- 0–100 patch quality score (error −20, warning −8, info −2)
- Self-contained HTML report generator
- CLI: `patch` / `commit` / `range` / `pipe` subcommands
- Shell wrapper `run_review.sh` with macOS auto-open
- `.env.example` — credentials template
- Best-practice scaffolding: `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, `.gitignore`, `LICENSE` (MIT), `CONTRIBUTING.md`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`

### Fixed
- K004 (`check_kvm_vcpu_lock`) regex broadened from `vcpu->(arch|regs|sregs)\s*=` to `vcpu->(arch|regs|sregs)[\w.\[\]]*\s*=` to catch real kernel patterns like `vcpu->arch.regs[VCPU_REGS_RAX] = val`
- `analyzer.py`: upgrade default model from deprecated `granite-13b-chat-v2` to `ibm/granite-3-8b-instruct`
- `analyzer.py`: update watsonx API version `2023-05-29` → `2024-05-01`
- `analyzer.py`: fix Granite 3.x prompt format (`<|start_of_role|>system<|end_of_role|>` tokens)

---

[Unreleased]: https://github.ibm.com/cheruiyo/us-kvm-status/compare/v0.2.0...HEAD
[0.2.0]: https://github.ibm.com/cheruiyo/us-kvm-status/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.ibm.com/cheruiyo/us-kvm-status/releases/tag/v0.1.0
