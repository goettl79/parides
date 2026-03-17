# Contributing to Parides

First off, thank you for considering contributing to Parides! It's people like you that make open source such a great community.

## 1. Where do I go from here?

If you've noticed a bug or have a feature request, make sure to check our [Issues](https://github.com/goettl79/parides/issues) first to see if someone else has already created a ticket. If not, go ahead and [make one](https://github.com/goettl79/parides/issues/new/choose)!

## 2. Setting up your environment

Parides primarily uses **Poetry** for dependency management, but you can also use a standard virtual environment.

### Option A: Using Poetry (Recommended)

1. Ensure you have Python 3.10+ installed.
2. Install Poetry:
   ```bash
   pip install poetry
   ```
3. Clone the repository and install dependencies:
   ```bash
   git clone https://github.com/goettl79/parides.git
   cd parides
   poetry install
   ```

### Option B: Using Virtual Environment (venv)

1. Ensure you have Python 3.10+ installed.
2. Clone the repository:
   ```bash
   git clone https://github.com/goettl79/parides.git
   cd parides
   ```
3. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install the package in editable mode with development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## 3. Making Changes

* Create a new branch from `master` (`git checkout -b feature/your-feature-name`).
* Make your changes.
* Ensure you add type hints where applicable.

## 4. Testing & Linting

Before submitting a Pull Request, ensure your code passes the test suite and linting rules.

1. **Run Linting (flake8):**
   ```bash
   # Using Poetry (if venv not activated)
   poetry run flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

   # With activated venv
   flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
   ```
2. **Run Unit Tests:**
   ```bash
   # Using Poetry
   poetry run pytest

   # With activated venv
   pytest
   ```
3. **Run Integration Tests (Optional):**
   If you made changes to the API fetching logic, try to test against a real Prometheus instance:
   ```bash
   export PROM_URL="http://localhost:9090" # Replace with your Prometheus URL
   
   # Using Poetry
   poetry run pytest tests/integration/

   # With activated venv
   pytest tests/integration/
   ```

## 5. Submitting a Pull Request

* Push your branch to GitHub (`git push origin feature/your-feature-name`).
* Open a Pull Request against the `master` branch.
* Provide a clear description of what the PR does and link to any relevant issues.
* The CI pipeline will automatically run your code against Python 3.9-3.12. Please fix any failures before requesting a review.
