# Contributing to Crestron Home Integration

Thank you for considering contributing to the Crestron Home integration for Home Assistant!

## How to contribute

1. Fork the repository
2. Create a feature branch: `git checkout -b my-new-feature`
3. Make your changes
4. Run the linting tools: `ruff check .`
5. Commit your changes: `git commit -am 'Add some feature'`
6. Push to the branch: `git push origin my-new-feature`
7. Submit a pull request

## Development Environment

1. Clone the repository
2. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install pre-commit hooks:
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Code Style

This project follows the Home Assistant code style guidelines:

- Use double quotes for strings
- Use 4 spaces for indentation
- Follow PEP 8 guidelines
- Use type hints for function parameters and return values

## Testing

Before submitting a pull request, please test your changes:

1. Install the integration in a test Home Assistant instance
2. Verify that your changes work as expected
3. Ensure that existing functionality is not broken

## Reporting Issues

If you find a bug or have a feature request, please open an issue on GitHub.

## License

By contributing to this project, you agree that your contributions will be licensed under the project's MIT License.
