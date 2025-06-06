pub mod brightness;
pub mod hue;
pub mod lightness;
pub mod saturation;

use image::RgbImage;

#[derive(Clone, Copy)]
pub enum SortMode {
    Hue,
    Saturation,
    Lightness,
    Brightness,
}

pub fn sort_pixels(img: RgbImage, mode: SortMode) -> RgbImage {
    match mode {
        SortMode::Hue => hue::sort(img),
        SortMode::Saturation => saturation::sort(img),
        SortMode::Lightness => lightness::sort(img),
        SortMode::Brightness => brightness::sort(img),
    }
}
