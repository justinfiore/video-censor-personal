# Contributing to Video Censor Personal

Thank you for your interest in contributing! This guide explains the development workflow, testing requirements, and CI/CD process.

## Development Workflow

### Setting Up Your Development Environment

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd video-censor-personal
   ```

2. **Create a feature branch:**
   ```bash
   git checkout -b feature/description
   ```

3. **Create a virtual environment:**
   ```bash
   python3.13 -m venv venv
   source venv/bin/activate  # macOS/Linux
   # or
   venv\Scripts\activate.bat  # Windows
   ```

4. **Install dependencies:**
   ```bash
   pip install --upgrade pip setuptools wheel
   pip install -r requirements.txt
   ```

### Code Style and Quality

This project follows PEP 8 with a 100-character line limit.

```bash
# Format code with black
pip install black
black video_censor_personal/

# Check code style with flake8
pip install flake8
flake8 video_censor_personal/
```

## Testing Requirements

### Running Tests Locally

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=video_censor_personal

# Run tests with verbose output
pytest -v

# Run a specific test file
pytest tests/test_config.py

# Run a specific test class or function
pytest tests/test_config.py::TestValidateConfig::test_valid_config
```

### Coverage Requirements

The project maintains a **minimum code coverage of 80%** to ensure code quality and prevent regressions.

```bash
# Check coverage with failure threshold
pytest --cov=video_censor_personal --cov-report=term
coverage report --fail-under=80
```

**To improve coverage:**
- Identify low-coverage modules: `coverage report` shows percentages for each module
- Write tests for untested code paths
- Focus on critical paths and edge cases
- See modules with low coverage:
  - `audio_extractor.py` (0%) - Future feature, no tests needed yet
  - `audio_remediator.py` (0%) - Future feature, no tests needed yet
  - `video_muxer.py` (0%) - Future feature, no tests needed yet
  - `speech_profanity_detector.py` (15%) - Limited tests for early implementation
  - `audio_classification_detector.py` (19%) - Limited tests for early implementation

For additional guidance, check the current coverage:
```bash
pytest --cov=video_censor_personal --cov-report=html
# Opens interactive coverage report in htmlcov/index.html
```

## Continuous Integration (CI/CD)

### GitHub Actions Workflow

The project uses **GitHub Actions** for automated testing. The workflow is defined in `.github/workflows/test.yml` and runs automatically on:

- **Pushes** to `main` and `feature/*` branches
- **Pull requests** to `main`

### What the CI/CD Pipeline Does

1. **Sets up Python 3.13** on Ubuntu runner
2. **Installs dependencies** from `requirements.txt`
3. **Runs all tests** with pytest in verbose mode
4. **Measures code coverage** with pytest-cov
5. **Enforces 80% coverage threshold** - fails if below threshold
6. **Uploads coverage reports** to Codecov for tracking and badge generation

### Viewing Test Results

#### In GitHub Actions

1. Push your branch or open a pull request to `main`
2. Navigate to the **"Actions"** tab in the repository
3. Click on your workflow run to see:
   - Test output and results
   - Coverage measurements
   - Build status

#### Coverage Reports

- **Codecov**: Integration with Codecov provides:
  - Coverage badges (displayed in README.md)
  - Coverage trend tracking over time
  - File-by-file coverage breakdown
  - Pull request coverage change detection

Visit the [Codecov dashboard](https://codecov.io) to see detailed reports and trends.

### CI/CD Failure Scenarios

The CI/CD pipeline will **fail and block merging** if:

- Any test fails
- Code coverage drops below 80%
- Dependencies cannot be installed
- Python 3.13 environment setup fails

### Test and Coverage Workflow

Before pushing to a feature branch:

```bash
# Run complete test suite locally
pytest --cov=video_censor_personal --cov-report=term

# Check coverage threshold
coverage report --fail-under=80

# If coverage is low, identify modules needing tests
coverage report -m  # Shows missing lines

# After improving coverage, re-run
pytest --cov=video_censor_personal
```

## Submitting Changes

### Creating a Pull Request

1. **Push your feature branch:**
   ```bash
   git push origin feature/description
   ```

2. **Open a PR** on GitHub with a clear description:
   - What problem does this solve?
   - What changes were made?
   - Any testing considerations?

3. **Wait for CI/CD checks** to pass:
   - All tests must pass
   - Coverage must be ≥ 80%
   - Code review approval required

4. **Merge to main** once all checks pass

### Commit Message Guidelines

Use clear, descriptive commit messages in present tense:

```bash
# Good
git commit -m "Add profanity detection threshold configuration"

# Avoid
git commit -m "Fix bug" or "Updates"
```

## Project Structure

```
video-censor-personal/
├── video_censor_personal/          # Main package
│   ├── cli.py                      # CLI interface
│   ├── config.py                   # Configuration parsing
│   ├── detection.py                # Detector base classes
│   ├── pipeline.py                 # Analysis pipeline
│   ├── detectors/                  # Detector implementations
│   └── ...
├── tests/                          # Test suite
│   ├── test_*.py                   # Unit tests
│   └── integration/                # Integration tests
├── .github/workflows/              # CI/CD workflows
│   └── test.yml                    # Test automation
├── requirements.txt                # Python dependencies
├── pytest.ini                      # Pytest configuration
└── README.md                       # Project documentation
```

## Debugging and Troubleshooting

### Running Tests with Verbose Output

```bash
pytest -vv tests/test_config.py
```

### Testing with Debug Logging

```bash
python video_censor_personal.py --verbose --input test.mp4
```

### Checking Coverage for a Specific Module

```bash
coverage run -m pytest tests/test_config.py
coverage report --include=video_censor_personal/config.py
```

## Questions?

- Review existing tests for patterns and examples
- Check README.md for setup and usage guidance
- Review project.md in openspec/ for architecture decisions

Thank you for contributing!
