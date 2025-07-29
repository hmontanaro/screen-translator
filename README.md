# Screen Translator

A real-time screen translation tool that captures text around your cursor, performs OCR (Optical Character Recognition), and translates German text to English using DeepL API. The translated text is displayed in overlay near your cursor.

## Features

- **Cursor-based capture**: Captures text around your mouse cursor
- **OCR Recognition**: Uses Tesseract OCR for German text recognition
- **DeepL Translation**
- **Overlay Display:** Overlay appears near cursor
- **Global Hotkeys**: Works system-wide with keyboard shortcuts

## Prerequisites

Before installation, you'll need:

1. **Python 3.12+** installed on your system
2. **Tesseract OCR** with German language support
3. **DeepL API Key** (free tier available)

### Installing Tesseract OCR

#### Windows
1. Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install with German language data included
3. Note the installation path (e.g., `C:\Users\hmont\AppData\Local\Programs\Tesseract-OCR\tesseract.exe` if installed locally)

#### Alternative via Chocolatey
```powershell
choco install tesseract
```

### Getting a DeepL API Key

1. Sign up at: https://www.deepl.com/pro-api
2. Get your free API key (500,000 characters/month limit)
3. Keep this key secure - you'll need it for setup

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd screen-translator
```

### 2. Set up Python Environment
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

Or if using `uv`:
```powershell
uv sync
```

### 3. Configure Environment Variables
Create a `.env` file in the project root:
```env
DEEPL_API_KEY=your-deepl-api-key-here
```

### 4. Update Tesseract Path (if needed)
If Tesseract is installed in a different location, update the path in `main.py`:
```python
pytesseract.pytesseract.tesseract_cmd = r"C:\path\to\your\tesseract.exe"
```

## Usage

### Starting the Application
```powershell
# Activate virtual environment (if not already active)
.venv\Scripts\Activate.ps1

# Run the application
python main.py
```

### Keyboard Shortcuts
- **Ctrl+Alt+T**: Capture and translate text around cursor
- **Ctrl+Alt+Q**: Quit the application

### How It Works
1. Position your cursor near German text on screen
2. Press `Ctrl+Alt+T`
3. The app captures a 600x220 pixel area around your cursor
4. OCR extracts German text from the image
5. DeepL translates the text to English
6. Translation appears in an overlay near your cursor

## Configuration

### Customizing Capture Area
Modify the `get_mouse_rect()` function in `main.py`:
```python
def get_mouse_rect(w=600, h=220):  # Change w and h values
```

### Changing Languages
Update the language constants in `main.py`:
```python
LANG_SRC, LANG_DST = "DE", "EN"  # Source and target languages
```

## Troubleshooting

### Common Issues

**"Error: Tesseract not found"**
- Ensure Tesseract is installed and path is correct in `main.py`
- Install German language data: `tessdata/deu.traineddata`

**"Translation error: 403 Forbidden"**
- Check your DeepL API key in `.env` file
- Verify you haven't exceeded your monthly quota

### Dependencies
- `PySide6`: Qt-based GUI framework
- `pytesseract`: Python wrapper for Tesseract OCR
- `Pillow`: Image processing
- `mss`: Screen capture
- `requests`: HTTP requests for DeepL API
- `keyboard`: Global hotkey detection
- `pywin32`: Windows API access
- `python-dotenv`: Environment variable loading
