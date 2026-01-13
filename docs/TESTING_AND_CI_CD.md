# Testing and CI/CD Setup

## Overview

This document describes the testing infrastructure and continuous integration/continuous deployment (CI/CD) setup for the label_web2 project.

---

## Tests Excluded from Docker Container

The `tests/` directory is excluded from the Docker container to keep the production image lean and focused. 
Any new tests must be added to the tests/ directory, which is ignored during the Docker build process.

---

## Unit Tests

### Running Tests Locally

To run all unit tests in your development environment:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

To run a specific test file:

```bash
python -m unittest tests.test_resolve_data -v
```

To run a specific test method:

```bash
python -m unittest tests.test_resolve_data.TestResolveData.test_resolve_data_with_simple_data -v
```

---

## GitHub Actions Workflows

Two automated workflows are configured to run unit tests:

### 1. Unit Tests Workflow (unit-tests.yml)

**Trigger:** 
- On push to `main`, `develop`, or version branches (`*.x`)
- On pull requests to `main`, `develop`, or version branches (`*.x`)

**What it does:**
- Executes all unit tests
- Generates test reports
- Uploads artifacts for 30 days

### 2. PR Validation Workflow (pr-validation.yml)

**Trigger:** 
- On pull requests to `main` or `develop`

**What it does:**
- Validates pull requests before merging
- Runs comprehensive unit tests
- Provides GitHub comments with results
- Ensures code quality standards


## Debugging Failed Tests

If tests fail in GitHub Actions:

1. **Check GitHub Actions output**
   - Go to the PR or push
   - Click "Details" on the failing status check
   - Review the test output

2. **Download test artifacts**
   - Go to the workflow run
   - Download the "test-results" artifact
   - Review for detailed error information

3. **Run tests locally**
   - Clone the repository
   - Checkout the failing branch
   - Run `python -m unittest discover -s tests -p "test_*.py" -v`
   - Reproduce and fix the issue

4. **Check Python version compatibility**
   - If tests pass on 3.10 but fail on 3.9 or 3.11, there may be version-specific issues
   - Use the Python version matrix to identify problematic versions

---

## Best Practices

1. **Run tests locally before pushing**
   ```bash
   python -m unittest discover -s tests -p "test_*.py" -v
   ```

2. **Create tests for new features**
   - Add unit tests in the `tests/` directory
   - Name test files: `test_*.py`
   - Follow existing test conventions

3. **Keep tests focused**
   - One concern per test
   - Clear test names describing what is tested
   - Meaningful assertions

4. **Review CI/CD feedback**
   - Check GitHub Actions results
   - Review PR comments for test status
   - Fix any failing tests before requesting review

---

## Troubleshooting

### Tests pass locally but fail in GitHub Actions

**Possible causes:**
- Python version differences
- Missing system dependencies
- Environment variable differences

**Solution:**
- Check the specific Python version that failed
- Verify all system dependencies are installed
- Review the GitHub Actions output for error messages

### Workflow file not triggering

**Possible causes:**
- Incorrect branch name pattern
- Incorrect file location
- YAML syntax errors

**Solution:**
- Verify branch names match the `on:` triggers
- Ensure files are in `.github/workflows/`
- Validate YAML syntax using a YAML linter

### Tests hang or timeout

**Possible causes:**
- Infinite loop in tests
- Waiting for external service
- Resource constraints

**Solution:**
- Add timeout to workflow: `timeout-minutes: 30`
- Review test for blocking operations
- Check for resource-intensive operations

---
