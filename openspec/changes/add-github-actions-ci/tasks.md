# Implementation Tasks: GitHub Actions CI/CD

## 1. Workflow Setup
- [ ] 1.1 Create .github/workflows/ directory structure
- [ ] 1.2 Create test.yml workflow file with Python 3.13 environment
- [ ] 1.3 Configure workflow to trigger on push (main + feature branches) and pull requests
- [ ] 1.4 Add dependency installation step using requirements.txt
- [ ] 1.5 Add pytest execution step with verbose output
- [ ] 1.6 Verify workflow syntax is valid

## 2. Coverage Measurement
- [ ] 2.1 Add pytest-cov flags to workflow: --cov=video_censor_personal --cov-report=xml --cov-report=term
- [ ] 2.2 Configure coverage to exclude tests/ directory
- [ ] 2.3 Set coverage threshold to 80% in pytest configuration or workflow step
- [ ] 2.4 Add workflow step to fail build if coverage < 80%
- [ ] 2.5 Test coverage measurement locally before committing

## 3. Codecov Integration
- [ ] 3.1 Add codecov/codecov-action@v3 step to workflow
- [ ] 3.2 Configure action to use GITHUB_TOKEN (no extra secrets needed)
- [ ] 3.3 Test Codecov integration on a feature branch
- [ ] 3.4 Verify coverage.xml is uploaded successfully
- [ ] 3.5 Access Codecov project dashboard and confirm metrics appear

## 4. README Badges
- [ ] 4.1 Obtain GitHub Actions status badge markdown from workflow settings
- [ ] 4.2 Obtain Codecov coverage badge markdown from Codecov project page
- [ ] 4.3 Add badges to README.md at top (before other content)
- [ ] 4.4 Verify badges display correctly and are clickable
- [ ] 4.5 Verify badges update within 1-2 minutes of workflow completion

## 5. Documentation & Testing
- [ ] 5.1 Add section to CONTRIBUTING.md (create if needed) explaining CI/CD workflow
- [ ] 5.2 Document how developers can view test results in GitHub Actions UI
- [ ] 5.3 Document how to interpret coverage badges and improve coverage
- [ ] 5.4 Run full workflow on a feature branch to verify end-to-end behavior
- [ ] 5.5 Merge to main and verify workflow triggers correctly on main branch

## 6. Validation
- [ ] 6.1 Confirm all tests pass in CI
- [ ] 6.2 Confirm coverage is measured and reported correctly
- [ ] 6.3 Confirm badges are visible and accurate in README
- [ ] 6.4 Test failure scenario: modify a test to fail and verify CI fails appropriately
- [ ] 6.5 Test coverage scenario: introduce uncovered code and verify CI fails if below 80%
