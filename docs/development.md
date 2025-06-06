# Development Guide

- [Documentation Index](index.md)
- [API Documentation](api.md)
- [Contributing Guidelines](contributing.md)
- [Architecture Overview](architecture.md)

This guide provides detailed instructions for setting up a development environment and working with the Pixfuck codebase.

## Prerequisites

- Rust 1.70.0 or later
- Cargo (comes with Rust)
- Git
- A code editor (VS Code recommended)

## Development Environment Setup

1. **Install Rust**
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```

2. **Clone the Repository**
   ```bash
   git clone https://github.com/evolvewithevan/pixfuck.git
   cd pixfuck
   ```

3. **Install Dependencies**
   ```bash
   cargo build
   ```

4. **Install Development Tools**
   ```bash
   cargo install cargo-watch    # For development with auto-reload
   cargo install cargo-fmt      # For code formatting
   cargo install cargo-clippy   # For linting
   ```

## Project Structure

```
pixfuck/
├── src/              # Source code
│   ├── main.rs      # Entry point
│   ├── lib.rs       # Library code
│   └── utils/       # Utility functions
├── docs/            # Documentation
└── assets/          # Preview image(s)
```

## Development Workflow

1. **Create a New Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Run Tests**
   ```bash
   cargo test
   ```

3. **Check Code Style**
   ```bash
   cargo fmt
   cargo clippy
   ```

4. **Build the Project**
   ```bash
   cargo build
   ```

5. **Run the Project**
   ```bash
   cargo run -- [args]
   ```

## Testing

### Running Tests
```bash
# Run all tests
cargo test

# Run specific test
cargo test test_name

# Run tests with output
cargo test -- --nocapture
```

### Writing Tests
- Place unit tests in the same file as the code being tested
- Place integration tests in the `tests` directory
- Use the `#[test]` attribute for test functions
- Use `assert!`, `assert_eq!`, and `assert_ne!` for assertions

## Code Style

- Follow the [Rust Style Guide](https://doc.rust-lang.org/1.0.0/style/style/naming/README.html)
- Use `cargo fmt` to format code
- Use `cargo clippy` to check for common mistakes
- Document all public APIs with doc comments

## Debugging

### Using `println!`
```rust
println!("Debug: {:?}", variable);
```

### Using the Debugger
1. Install VS Code Rust extension
2. Set breakpoints in code
3. Press F5 to start debugging

## Performance Optimization

1. Use `cargo bench` to run benchmarks
2. Profile with `cargo flamegraph`
3. Use `#[inline]` for small, frequently called functions
4. Consider using `rayon` for parallel processing

## Common Issues

### Build Errors
- Ensure all dependencies are up to date
- Check for conflicting features
- Verify Rust toolchain version

### Test Failures
- Check test environment setup
- Verify test data
- Check for race conditions

## Resources

- [Rust Documentation](https://doc.rust-lang.org/book/)
- [Cargo Documentation](https://doc.rust-lang.org/cargo/)
- [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)
- [Rust Performance Book](https://nnethercote.github.io/perf-book/) 