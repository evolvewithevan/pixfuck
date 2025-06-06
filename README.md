# Pixfuck - Pixel Sorting Tool

> **⚠️ Development Branch Notice**
> 
> This is a development branch and is not intended for production use. Features may be unstable, incomplete, or subject to breaking changes. Use at your own risk.
> For production ready software, see [main](https://github.com/evolvewithevan/pixfuck/tree/main)


A fast pixel sorting tool written in Rust that creates artistic effects by sorting pixels in images based on various criteria.

## Features

- **Multiple Sorting Modes**: Sort pixels by Hue, Saturation, Lightness, or Brightness
- **Fast Processing**: Built with Rust for optimal performance using parallel processing
- **Simple CLI Interface**: Easy-to-use command-line interface
- **Multiple Image Formats**: Supports common image formats (PNG, JPEG, etc.)

## Installation

### From Pre-Built Binaries

Pre-built binaries are not available for this development branch. Please build from source instead.

### From Source

1. Make sure you have Rust installed. If not, install it from [rustup.rs](https://rustup.rs/)

2. Clone the repository:
   ```bash
   git clone <repository-url>
   cd pixfuck
   ```

3. Build the project:
   ```bash
   cargo build --release
   ```

5. (Optional - Not recommended) Install globally:
   ```bash
   cargo install --path .
   ```

