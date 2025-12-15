# Change: Add GitHub Actions CI/CD

## Why
Automated testing ensures code quality and prevents regressions. GitHub Actions provides native CI/CD integration with public test results and coverage metrics. Status badges in the README increase project credibility and visibility.

## What Changes
- Create GitHub Actions workflow to run all tests on push and pull requests
- Measure and report test coverage from pytest-cov
- Display test status and coverage badges in README
- Fail CI if tests fail or if coverage drops below project minimum (80%)
- Generate test reports visible in GitHub UI

## Impact
- Affected specs: CI/CD (new capability), project-foundation (README badges)
- Affected code: .github/workflows/, README.md
- No breaking changes
