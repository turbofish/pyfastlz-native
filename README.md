# pyfastlz-native

[![CI](https://github.com/turbofish/pyfastlz-native/workflows/CI/badge.svg)](https://github.com/turbofish/pyfastlz-native/actions)
[![codecov](https://codecov.io/gh/turbofish/pyfastlz-native/branch/main/graph/badge.svg)](https://codecov.io/gh/turbofish/pyfastlz-native)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

This is a native python3 implementation of the FastLZ algorithm (more info in [Lempel-Ziv 77 algorithm](https://en.wikipedia.org/wiki/LZ77_and_LZ78#LZ77)).

Implements native compression (only level 1 for now) and decompression with both level 1 (fast) and level 2 (better compression) support.

## Installation

```bash
pip install pyfastlz-native
```

## Usage

```python
import fastlz_native

# Compress data
data = b"Hello, World! This is some data to compress."
compressed = fastlz_native.compress(data)  # Auto-selects level
compressed_lv1 = fastlz_native.compress(data, level=1)  # Fast compression
compressed_lv2 = fastlz_native.compress(data, level=2)  # Better compression

# Decompress data
decompressed = fastlz_native.decompress(compressed)
```

## Expected format

This implementation includes a 4-byte header containing the original data size, followed by the compressed data. The compression level is encoded in the first byte of the compressed data.

## Development

### Setup Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/turbofish/pyfastlz-native.git
   cd pyfastlz-native
   ```

2. Install development dependencies:
   ```bash
   make install-dev
   # or manually:
   pip install -e ".[dev]"
   ```

3. Install pre-commit hooks:
   ```bash
   make pre-commit-install
   # or manually:
   pre-commit install
   ```

### Development Commands

The project uses a Makefile for common development tasks:

```bash
make help              # Show all available commands
make lint              # Run ruff linter with auto-fix
make format            # Format code with ruff
make type-check        # Run mypy type checker
make test              # Run pytest tests
make test-cov          # Run tests with coverage report
make all-checks        # Run all quality checks
make clean             # Clean build artifacts
```

### Code Quality Tools

This project uses modern Python tooling for code quality:

- **[Ruff](https://github.com/astral-sh/ruff)**: Fast linter and formatter (replaces flake8, black, isort, and more)
- **[MyPy](https://github.com/python/mypy)**: Static type checker
- **[Pre-commit](https://pre-commit.com/)**: Git hooks for automated quality checks
- **[Pytest](https://pytest.org/)**: Testing framework with coverage reporting

## License

MIT License - see [LICENSE](LICENSE) file for details.
