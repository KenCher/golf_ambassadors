# Changelog

All notable changes to PatchIQ are documented here.
This project follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Pre-commit hooks (ruff lint + format, trailing-whitespace, end-of-file-fixer)
- GitHub Actions CI workflow (Python 3.8–3.12 matrix, lint, test, coverage)
- `pyproject.toml` — PEP 517 packaging, `patchiq` entry-point script
- `requirements.txt` / `requirements-dev.txt`
- `LICENSE` (MIT)
- `CONTRIBUTING.md`

---

## [0.1.0] — 2026-07-14

### Added
- Initial public release for the watsonx Challenge 2026
- Four-stage review pipeline: `parse_diff` → `detect_layer` → `run_rules` → `ai_review`
- 14 style rules: K001–K004 (kernel/KVM), Q001–Q004 (QEMU), L001–L003 (libvirt), U001–U003 (universal)
- 68-test suite covering every rule (positive + negative), diff parser, scoring, end-to-end pipeline
- watsonx Granite 13B AI narrative review (optional, IBM Cloud credentials)
- 0–100 patch quality score (error −20, warning −8, info −2)
- Self-contained HTML report generator
- CLI: `patch` / `commit` / `range` / `pipe` subcommands
- Shell wrapper `run_review.sh` with macOS auto-open

### Fixed
- K004 (`check_kvm_vcpu_lock`) regex `vcpu->(arch|regs|sregs)\s*=` was too narrow;
  missed real kernel patterns like `vcpu->arch.regs[VCPU_REGS_RAX] = val`.
  Broadened to `vcpu->(arch|regs|sregs)[\w.\[\]]*\s*=`.

---

[Unreleased]: https://github.ibm.com/cheruiyo/Watsonx_challenge_2026/compare/v0.1.0...HEAD
[0.1.0]: https://github.ibm.com/cheruiyo/Watsonx_challenge_2026/releases/tag/v0.1.0
