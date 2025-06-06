# Contributing to Pixfuck

Thank you for your interest in contributing to Pixfuck! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please read it before contributing.

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in the [Issues](https://github.com/evolvewithevan/pixfuck/issues) section
2. If not, create a new issue with:
   - A clear, descriptive title
   - Steps to reproduce the bug
   - Expected behavior
   - Actual behavior
   - Screenshots if applicable
   - System information (OS, Rust version, etc.)

### Suggesting Features

1. Check if the feature has already been suggested
2. Create a new issue with:
   - A clear, descriptive title
   - Detailed description of the feature
   - Use cases and examples
   - Any relevant technical details

### Pull Requests

1. Fork the repository
2. Create a new branch for your feature/fix
3. Make your changes
4. Run tests and ensure they pass
5. Update documentation if necessary
6. Submit a pull request

#### Pull Request Guidelines

- Keep changes focused and atomic
- Follow the existing code style
- Include tests for new features
- Update documentation
- Reference related issues
- Ensure CI passes

## Development Process

### Setting Up

1. Fork and clone the repository
2. Install dependencies:
   ```bash
   cargo build
   ```
3. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

### Making Changes

1. Make your changes
2. Run tests:
   ```bash
   cargo test
   ```
3. Format code:
   ```bash
   cargo fmt
   ```
4. Run linter:
   ```bash
   cargo clippy
   ```

### Submitting Changes

1. Commit your changes:
   ```bash
   git commit -m "Description of changes"
   ```
2. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
3. Create a pull request

## Code Style

- Follow the [Rust Style Guide](https://doc.rust-lang.org/1.0.0/style/style/naming/README.html)
- Use meaningful variable and function names
- Write clear, concise comments
- Document all public APIs
- Keep functions small and focused

## Testing

- Write unit tests for new features
- Ensure all tests pass
- Maintain or improve test coverage
- Include integration tests for complex features

## Documentation

- Update README.md if necessary
- Document new features
- Update API documentation
- Include examples for new functionality

## Review Process

1. All pull requests require at least one review
2. Address review comments promptly
3. Make requested changes
4. Ensure CI passes
5. Wait for maintainer approval

## Release Process

1. Version bump
2. Update changelog
3. Tag release
4. Create release notes
5. Publish to crates.io

## Getting Help

- Check the [documentation](docs/index.md)
- Join our [Discord server](https://discord.gg/pixfuck)
- Open an issue for questions

## License

By contributing to Pixfuck, you agree that your contributions will be licensed under the project's [LICENSE](../LICENSE) file. 