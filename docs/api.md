# API Documentation

- [Documentation Index](index.md)
- [Development Guide](development.md)
- [Contributing Guidelines](contributing.md)
- [Architecture Overview](architecture.md)

This document provides detailed information about Pixfuck's public API and its usage.

## Core Functions

### Image Processing

#### `process_image`
```rust
pub fn process_image(
    input_path: &str,
    output_path: &str,
    sorting_mode: SortingMode,
    options: ProcessingOptions
) -> Result<(), Error>
```

Processes an image using the specified sorting mode and options.

**Parameters:**
- `input_path`: Path to the input image file
- `output_path`: Path where the processed image will be saved
- `sorting_mode`: The mode to use for pixel sorting (Hue, Saturation, Lightness, or Brightness)
- `options`: Additional processing options

**Returns:**
- `Result<(), Error>`: Ok(()) on success, Error on failure

### Sorting Modes

#### `SortingMode` Enum
```rust
pub enum SortingMode {
    Hue,
    Saturation,
    Lightness,
    Brightness
}
```

Defines the available sorting modes for pixel processing.

### Processing Options

#### `ProcessingOptions` Struct
```rust
pub struct ProcessingOptions {
    pub threshold: f32,
    pub direction: SortDirection,
    pub region: Option<Region>
}
```

Configuration options for image processing.

**Fields:**
- `threshold`: Minimum value threshold for sorting (0.0 to 1.0)
- `direction`: Direction of sorting (Ascending or Descending)
- `region`: Optional region to process (None for entire image)

## Error Handling

### `Error` Enum
```rust
pub enum Error {
    IoError(std::io::Error),
    ImageError(image::ImageError),
    InvalidOptions(String)
}
```

Represents possible errors that can occur during processing.

## Examples

### Basic Usage
```rust
use pixfuck::{process_image, SortingMode, ProcessingOptions};

let options = ProcessingOptions {
    threshold: 0.5,
    direction: SortDirection::Ascending,
    region: None
};

process_image(
    "input.jpg",
    "output.jpg",
    SortingMode::Hue,
    options
)?;
```

### Advanced Usage
```rust
use pixfuck::{process_image, SortingMode, ProcessingOptions, Region};

let region = Region {
    x: 100,
    y: 100,
    width: 200,
    height: 200
};

let options = ProcessingOptions {
    threshold: 0.7,
    direction: SortDirection::Descending,
    region: Some(region)
};

process_image(
    "input.jpg",
    "output.jpg",
    SortingMode::Saturation,
    options
)?;
```

## Performance Considerations

- The library uses parallel processing for optimal performance
- Memory usage scales linearly with image size
- Processing time depends on image dimensions and selected options

## Best Practices

1. Always handle errors appropriately using the Result type
2. Use appropriate sorting modes for desired effects
3. Consider memory usage when processing large images
4. Use region processing for targeted effects 