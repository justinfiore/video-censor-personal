# ci-cd Specification

## Purpose
Define automated testing and quality control infrastructure for the video-censor-personal project.

## ADDED Requirements

### Requirement: GitHub Actions Test Workflow

The system SHALL execute all tests automatically on code changes via GitHub Actions.

#### Scenario: Tests run on push to main
- **WHEN** code is pushed to the main branch
- **THEN** GitHub Actions triggers test workflow

#### Scenario: Tests run on pull requests
- **WHEN** a pull request is created or updated
- **THEN** GitHub Actions triggers test workflow on the PR branch

#### Scenario: Workflow uses Python 3.13
- **WHEN** GitHub Actions workflow executes
- **THEN** tests run in Python 3.13 environment

#### Scenario: All dependencies installed
- **WHEN** workflow runs
- **THEN** all packages from requirements.txt are installed

#### Scenario: Tests executed via pytest
- **WHEN** workflow runs
- **THEN** pytest is invoked with command `python -m pytest tests/ -v`

#### Scenario: Workflow fails on test failures
- **WHEN** any test fails
- **THEN** workflow exits with non-zero status, marking build as failed

#### Scenario: Workflow logs available
- **WHEN** workflow completes
- **THEN** test output and logs are visible in GitHub Actions UI

### Requirement: Test Coverage Measurement

The system SHALL measure and report code coverage for all tests.

#### Scenario: Coverage measured with pytest-cov
- **WHEN** tests run
- **THEN** pytest-cov generates coverage report for video_censor_personal package

#### Scenario: Coverage report in XML format
- **WHEN** tests complete
- **THEN** coverage.xml is generated for CI integration

#### Scenario: Coverage report in terminal format
- **WHEN** tests complete
- **THEN** coverage percentage is printed to CI logs for human review

#### Scenario: Minimum coverage threshold enforced
- **WHEN** coverage analysis completes
- **THEN** build fails if coverage is less than 80%

#### Scenario: Coverage excludes test files
- **WHEN** coverage is measured
- **THEN** tests/ directory is excluded from coverage calculation (focus on source code)

### Requirement: Coverage Reporting to External Service

The system SHALL upload coverage metrics to a third-party service for badge generation and trend tracking.

#### Scenario: Coverage uploaded to Codecov
- **WHEN** tests complete successfully
- **THEN** coverage.xml is uploaded to Codecov via codecov-action

#### Scenario: Codecov integration uses GitHub token
- **WHEN** uploading to Codecov
- **THEN** GITHUB_TOKEN is used for authentication (no additional secrets required)

#### Scenario: Coverage badge generated
- **WHEN** coverage is uploaded to Codecov
- **THEN** coverage badge URL is available for README display

### Requirement: Status Badges in README

The system SHALL display build status and coverage badges in the README.

#### Scenario: Test status badge included
- **WHEN** README is viewed on GitHub
- **THEN** a badge showing the latest test status (passing/failing) is visible at the top

#### Scenario: Coverage badge included
- **WHEN** README is viewed on GitHub
- **THEN** a badge showing the latest coverage percentage is visible near test status badge

#### Scenario: Badges are clickable
- **WHEN** user clicks a badge
- **THEN** they are directed to GitHub Actions workflow or Codecov project page

#### Scenario: Badges update automatically
- **WHEN** a new workflow run completes
- **THEN** badges refresh to reflect new status and coverage within 60 seconds
