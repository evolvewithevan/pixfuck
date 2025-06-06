pub mod sort;

use image::{ImageFormat, ImageReader};
use std::fs::File;
use std::path::Path;

pub use sort::{SortMode, sort_pixels};

pub fn sort_image(input_path: &str, output_path: &str, mode: SortMode) -> image::ImageResult<()> {
    let img = ImageReader::open(input_path)?.decode()?.to_rgb8();
    let sorted = sort_pixels(img, mode);
    let ext = Path::new(output_path)
        .extension()
        .and_then(|s| s.to_str())
        .unwrap_or("png");

    let mut file = File::create(output_path)?;
    let format = ImageFormat::from_extension(ext).unwrap_or(ImageFormat::Png);
    sorted.write_to(&mut file, format)
}
