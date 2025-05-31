# pixFuck 🎨

A pixel-sorting playground built with Python and PyQt6! Transform your images into mesmerizing works of art by sorting pixels in creative ways. ✨

## ✨ Features

- 🎯 Modern and intuitive PyQt6 interface
- 🎨 Real-time pixel sorting preview
- 🔄 Multiple sorting algorithms to play with
- 📸 Support for various image formats
- ⚡ Background processing for smooth performance
- 📝 Comprehensive logging system

## 🛠️ Requirements

- Python 3.6 or higher
- PyQt6 >= 6.4.0
- Pillow >= 9.0.0
- numpy >= 1.20.0
- numba >= 0.55.0
- scipy >= 1.7.0

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pixFuck.git
cd pixFuck
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
.\venv\Scripts\activate  # On Windows
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## 🎮 Usage

Run the application:
```bash
python main.py
```

## 📁 Project Structure

```
pixFuck/
├── main.py              # Application entry point
├── requirements.txt     # Project dependencies
├── ui/                  # User interface components
│   ├── __init__.py
│   ├── logger.py       # Logging configuration
│   ├── pixel_sort_app.py # Main application window
│   └── worker.py       # Background processing worker
└── logs/               # Application logs
```

## 💻 Development

The project uses a modular structure with separate components for:
- 🖥️ UI handling (`pixel_sort_app.py`)
- ⚙️ Background processing (`worker.py`)
- 📝 Logging (`logger.py`)

## 📜 License

This project is licensed under the GNU General Public License v3.0 (GPL-3.0) - see the [LICENSE](LICENSE) file for details.

The GPL-3.0 is a strong copyleft license that ensures the software remains free and open source. This means:
- You are free to use, modify, and distribute the software
- You must make any modifications available under the same license
- You must include the original copyright notice and license
- You must make the source code available to anyone who receives the software

For more information about the GPL-3.0, visit: https://www.gnu.org/licenses/gpl-3.0.html

This project was previously unlicensed. As of now, it is licensed under GPLv3. Prior code is copyrighted and not licensed for reuse.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. By contributing to this project, you agree that your contributions will be licensed under the GPL-3.0 license.

---

Made with ❤️ and lots of pixels! 