use image::{Rgb, RgbImage};
use rayon::prelude::*;
use palette::{Srgb, Hsl, IntoColor};

pub fn sort(img: RgbImage) -> RgbImage {
    let (w, h) = img.dimensions();
    let mut rows: Vec<Vec<Rgb<u8>>> = (0..h)
        .map(|y| (0..w).map(|x| *img.get_pixel(x, y)).collect())
        .collect();

    rows.par_iter_mut().for_each(|row| {
        row.sort_by(|a, b| hue(a).partial_cmp(&hue(b)).unwrap());
    });

    let mut out = RgbImage::new(w, h);
    for (y, row) in rows.iter().enumerate() {
        for (x, px) in row.iter().enumerate() {
            out.put_pixel(x as u32, y as u32, *px);
        }
    }

    out
}

fn hue(rgb: &Rgb<u8>) -> f32 {
    let Srgb { red, green, blue, .. } = Srgb::new(rgb[0], rgb[1], rgb[2]).into_format::<f32>();
    let hsl: Hsl = Srgb::new(red, green, blue).into_color();
    hsl.hue.into_degrees()
}
