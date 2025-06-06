use image::{Rgb, RgbImage};
use rayon::prelude::*;

pub fn sort(img: RgbImage) -> RgbImage {
    let (w, h) = img.dimensions();
    let mut rows: Vec<Vec<Rgb<u8>>> = (0..h)
        .map(|y| (0..w).map(|x| *img.get_pixel(x, y)).collect())
        .collect();

    rows.par_iter_mut().for_each(|row| {
        row.sort_by(|a, b| brightness(a).total_cmp(&brightness(b)));
    });

    let mut out = RgbImage::new(w, h);
    for (y, row) in rows.iter().enumerate() {
        for (x, px) in row.iter().enumerate() {
            out.put_pixel(x as u32, y as u32, *px);
        }
    }

    out
}

fn brightness(rgb: &Rgb<u8>) -> f32 {
    0.299 * rgb[0] as f32 + 0.587 * rgb[1] as f32 + 0.114 * rgb[2] as f32
}
