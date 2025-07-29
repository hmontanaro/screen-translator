# Screen Translator

A real-time screen translation tool that offers two convenient ways to translate German text to English: screen area selection and clipboard translation. Uses OCR (Optical Character Recognition) and DeepL API for translations.

## Features

- **Screen Area Selection**: Interactive rectangle selection for OCR translation
- **Clipboard Translation**: Translate text you copy
- **OCR Recognition**: Uses Tesseract OCR for German text recognition
- **DeepL Translation**: Translations using DeepL API
- **Overlay Display**: Translation results appear near your cursor
- **Global Hotkeys**: Works system-wide with keyboard shortcuts
- **Multi-monitor Support**: Works across multiple displays

## Prerequisites

Before installation, you'll need:

1. **Python 3.12+** installed on your system
2. **Tesseract OCR** with German language support
3. **DeepL API Key** (free tier available)

### Installing Tesseract OCR

#### Windows
1. Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
2. Install with German language data included
3. Note the installation path (e.g., `C:\Users\user-name\AppData\Local\Programs\Tesseract-OCR\tesseract.exe` if installed locally)

### Getting a DeepL API Key

1. Sign up at: https://www.deepl.com/pro-api
2. Get your free API key (500,000 characters/month limit)
3. Note key - needed for setup

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

### 4. Configure Environment Variables
Create a `.env` file in the project root:
```env
DEEPL_API_KEY=your-deepl-api-key-here
TESSERACT_CMD=C:\path\to\tesseract.exe  # Optional: custom Tesseract path
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
- **Ctrl+Alt+T**: Select screen area and translate (OCR)
- **Ctrl+Alt+C**: Translate clipboard content
- **Ctrl+Alt+Q**: Quit the application

### How It Works

#### Screen Area Translation (Ctrl+Alt+T)
1. Press `Ctrl+Alt+T` to enter selection mode
2. Click and drag to select any area of your screen containing German text
3. Release the mouse button to capture the selection
4. OCR extracts German text from the selected area
5. DeepL translates the text to English
6. Translation appears in an overlay near the selected area

#### Clipboard Translation (Ctrl+Alt+C)
1. Copy any German text to your clipboard (Ctrl+C)
2. Press `Ctrl+Alt+C` to translate
3. Translation appears in an overlay near your cursor
4. Works with text from any application (browsers, documents, etc.)

## Configuration

### Changing Languages
Update the language constants in `main.py`:
```python
LANG_SRC, LANG_DST = "DE", "EN"  # Source and target languages
```

### Tesseract Path Configuration
The application automatically searches for Tesseract in common installation locations:
- `C:\Program Files\Tesseract-OCR\tesseract.exe`
- `C:\Program Files (x86)\Tesseract-OCR\tesseract.exe`
- `%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe`

You can also set a custom path using the `TESSERACT_CMD` environment variable.

## Troubleshooting

### Common Issues

**"Error: Tesseract not found"**
- Ensure Tesseract is installed and path is correct in `main.py`
- Install German language data: `tessdata/deu.traineddata`

**"Translation error: 403 Forbidden"**
- Check your DeepL API key in `.env` file
- Verify you haven't exceeded your monthly quota

**"Clipboard is empty" message**
- Make sure you've copied text before pressing Ctrl+Alt+C
- Try copying the text again and wait a moment before translating

**Selection overlay not appearing**
- Try pressing Ctrl+Alt+T again
- Press ESC to cancel selection mode if stuck

### Dependencies
- `PySide6`: Qt-based GUI framework
- `pytesseract`: Python wrapper for Tesseract OCR
- `Pillow`: Image processing
- `mss`: Screen capture
- `requests`: HTTP requests for DeepL API
- `keyboard`: Global hotkey detection
- `pywin32`: Windows API access
- `python-dotenv`: Environment variable loading
