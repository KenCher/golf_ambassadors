# Contributing to PatchIQ

Thank you for wanting to improve PatchIQ!
This guide covers the dev setup, coding conventions, and how to add a new rule.

---

## Dev setup

```bash
git clone git@github.ibm.com:cheruiyo/Watsonx_challenge_2026.git
cd Watsonx_challenge_2026/kvm/patchiq

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install runtime + dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

---

## Running the tests

```bash
pytest                        # all 68 tests
pytest -k K004                # run tests matching a keyword
pytest --cov=patchiq          # with coverage report
```

All tests must pass before opening a PR.  No watsonx credentials are required.

---

## Coding standards

- Formatter / linter: **ruff** (configured in `pyproject.toml`)
- Run `ruff check . --fix && ruff format .` before committing, or let pre-commit handle it
- Line length: 100 characters (mirrors the K/L style rule)
- Type hints are encouraged but not mandatory for internal helpers
- Docstrings: one-line for simple helpers, full Google-style for public functions

---

## Adding a new rule

1. **Implement** a `check_*()` function in [`rules.py`](rules.py) following the existing pattern:
   ```python
   def check_my_rule(diff_lines):
       """Layer: brief description."""
       findings = []
       for line in _lines_added(diff_lines):
           if re.search(r'bad_pattern', line):
               findings.append(_finding(
                   "X001", "warning", "layer",
                   f"Human-readable message: {line.strip()}", line
               ))
       return findings
   ```

2. **Register** it in `RULE_SETS[layer]` in `rules.py`.

3. **Test** it — add at least one positive and one negative case in
   [`tests/test_rules.py`](tests/test_rules.py).

4. **Fixture** — add a triggering line to the relevant patch under
   [`tests/fixtures/`](tests/fixtures/).

5. **Document** it in the rule table in [`README.md`](README.md) and in
   [`CHANGELOG.md`](CHANGELOG.md) under `[Unreleased]`.

---

## Commit message format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(rules): add K005 check for missing __user annotation
fix(K004): broaden vcpu lock regex to match array indexing
test: add negative case for Q004 object_ref
docs: update CONTRIBUTING with ruff instructions
chore: bump requests to 2.31
```

Types: `feat`, `fix`, `test`, `docs`, `chore`, `refactor`, `perf`, `ci`

---

## Pull request checklist

- [ ] `pytest` passes (all 68+ tests green)
- [ ] `ruff check . && ruff format --check .` clean
- [ ] New rule has positive + negative unit test
- [ ] `CHANGELOG.md` updated under `[Unreleased]`
- [ ] `README.md` rule table updated if applicable

---

*PatchIQ is part of the IBM KVM & Linux open source team's watsonx Challenge 2026 submission.*
