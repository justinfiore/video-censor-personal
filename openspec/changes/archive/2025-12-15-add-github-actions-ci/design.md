# Design: GitHub Actions CI/CD

## Context
The project uses pytest for unit and integration testing with pytest-cov for coverage analysis. Python 3.13+ is required. Tests are currently run manually via run-tests.sh. The project is on GitHub and needs automated CI/CD to validate all commits and PRs.

## Goals
- Automate test execution on every push and PR
- Enforce minimum 80% code coverage (per project.md)
- Provide visible test status in GitHub UI and README
- Fail builds when tests fail or coverage drops
- Make test results easily discoverable for contributors

## Non-Goals
- Multi-version Python testing (currently only 3.13+ required)
- GPU/CUDA testing (users configure via environment)
- Model-dependent tests on CI (use mock detectors only)

## Decisions

### Workflow Strategy
- **Trigger**: Push to main/feature branches + all PRs
- **Python version**: 3.13 (per project requirements)
- **Coverage threshold**: 80% (per project.md conventions)
- **Coverage tool**: pytest-cov (already in requirements.txt)
- **Artifact storage**: GitHub Actions built-in test reporting

### Coverage Report Format
- Use `pytest --cov=video_censor_personal --cov-report=xml --cov-report=term` to generate coverage
- XML report enables integration with third-party badge services
- Terminal report visible in CI logs

### Badge Implementation
- Status badge: GitHub Actions native badge (no external service needed)
- Coverage badge: Use Codecov or similar service that auto-updates from CI results
  - Alternative: self-hosted badge with GitHub artifacts (more complex)
  - Decision: Use Codecov for simplicity; integrates directly with GitHub Actions

### Workflow Files
Location: `.github/workflows/test.yml`

Key steps:
1. Checkout code
2. Set up Python 3.13
3. Install dependencies
4. Run pytest with coverage
5. Upload coverage to Codecov
6. Fail if tests fail or coverage < 80%

## Alternatives Considered

### GitLab CI vs GitHub Actions
- **Chosen**: GitHub Actions (native to GitHub, free, no extra services)
- **Alternative**: GitLab CI (more powerful but requires migration)

### Coverage Service: Codecov vs Coveralls vs self-hosted
- **Chosen**: Codecov (industry standard, free tier for open source, auto badge)
- **Alternative**: Coveralls (simpler but less feature-rich)
- **Alternative**: Self-hosted (full control but complexity)

### Coverage Threshold Enforcement
- **Chosen**: Fail CI if coverage < 80% using pytest-cov return code
- **Alternative**: Soft warning (less effective at preventing regressions)

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| Codecov account setup required | Document setup in CONTRIBUTING guide |
| Coverage thresholds too strict | Set to 80% (per existing conventions); can adjust if needed |
| CI slowness with large models | Use mock detectors in CI (via PYTEST_RUN_WITH_MODELS=0 env var) |
| Flaky tests timeout | Set generous timeouts (10+ seconds per test); review flaky tests separately |

## Migration Plan

1. Create `.github/workflows/test.yml`
2. Set up Codecov integration (token in GitHub secrets)
3. Add status and coverage badges to README.md
4. Test on a feature branch before merging to main
5. Document in CONTRIBUTING.md (or create if needed)

## Open Questions

- Should we enforce coverage for specific modules (e.g., video_censor_personal/), or entire codebase including tests?
  - **Recommendation**: Exclude tests/ directory from coverage (focus on source code only)
- What should be the failure condition: >= 80% or <= 80%?
  - **Recommendation**: Fail if coverage < 80% (stricter enforcement)
- Should we track coverage trend over time?
  - **Recommendation**: Codecov provides trend visualization automatically
