use pixfuck::{sort_image, SortMode};
use std::io::{self, Write};

fn main() {
    println!("Welcome to Pixfuck! Please enter input file realpath:");
    let mut input = String::new();
    io::stdin().read_line(&mut input).unwrap();
    let input = input.trim();

    println!("Enter output file path:");
    let mut output = String::new();
    io::stdin().read_line(&mut output).unwrap();
    let output = output.trim();

    println!("Choose mode: 0=Hue, 1=Saturation, 2=Lightness, 3=Brightness");
    let mut mode_str = String::new();
    io::stdin().read_line(&mut mode_str).unwrap();
    let mode = match mode_str.trim() {
        "0" => SortMode::Hue,
        "1" => SortMode::Saturation,
        "2" => SortMode::Lightness,
        "3" => SortMode::Brightness,
        _ => {
            eprintln!("Invalid mode, defaulting to Hue");
            SortMode::Hue
        }
    };

    match sort_image(input, output, mode) {
        Ok(_) => println!("Image sorted and saved to this directory!"),
        Err(e) => eprintln!("Error: {}", e),
    }
}
