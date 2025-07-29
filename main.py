import os
import time

import keyboard
import mss
import pytesseract
import requests
import win32api
import win32clipboard
from dotenv import load_dotenv
from PIL import Image
from PySide6 import QtCore, QtGui, QtWidgets
from pytesseract import Output

load_dotenv()

DEEPL_KEY = os.getenv("DEEPL_API_KEY")  # set this in your environment
LANG_SRC, LANG_DST = "DE", "EN"  # German -> English


# Try to find Tesseract or use environment variable
tesseract_path = os.getenv("TESSERACT_CMD")
if not tesseract_path:
    # Common installation paths
    possible_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    # Look in AppData for all users
    app_data_path = os.path.join(
        os.environ.get("LOCALAPPDATA", ""), "Programs", "Tesseract-OCR", "tesseract.exe"
    )
    if os.path.exists(app_data_path):
        possible_paths.insert(0, app_data_path)

    # Use the first path that exists
    tesseract_path = next(
        (path for path in possible_paths if os.path.exists(path)), None
    )

if tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_path
else:
    print(
        "Warning: Tesseract not found. Please set TESSERACT_CMD environment variable."
    )


def get_clipboard_text():
    """Get text from clipboard"""
    try:
        win32clipboard.OpenClipboard()
        text = ""

        # Try Unicode text first (most common for modern apps)
        if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
            text = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
        # Fallback to regular text
        elif win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_TEXT):
            data = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
            text = data.decode("utf-8") if isinstance(data, bytes) else data

        win32clipboard.CloseClipboard()
        return text.strip() if text else ""
    except Exception as e:
        print(f"Error getting clipboard text: {e}")
        try:
            win32clipboard.CloseClipboard()
        except Exception:
            pass
        return ""


def capture_rect(rect):
    left, top, w, h = rect
    with mss.mss() as sct:
        img = sct.grab({"left": left, "top": top, "width": w, "height": h})
    return Image.frombytes("RGB", img.size, img.rgb)


def ocr_de(image):
    # lang='deu' requires Tesseract German language data installed
    data = pytesseract.image_to_data(image, lang="deu", output_type=Output.DICT)
    # Join words into lines (simple merge; refine if needed)
    lines = {}
    for i, text in enumerate(data["text"]):
        if int(data["conf"][i]) > 60 and text.strip():
            line = data["line_num"][i]
            lines.setdefault(line, []).append(text)
    extracted = " ".join(" ".join(words) for _, words in sorted(lines.items()))
    return extracted.strip()


def translate_deepl(text):
    if not text:
        return ""
    url = "https://api-free.deepl.com/v2/translate"
    resp = requests.post(
        url,
        data={
            "auth_key": DEEPL_KEY,
            "text": text,
            "source_lang": LANG_SRC,
            "target_lang": LANG_DST,
        },
        timeout=10,
    )
    resp.raise_for_status()
    j = resp.json()
    return "\n".join(t["text"] for t in j.get("translations", []))


class SelectionOverlay(QtWidgets.QWidget):
    selection_made = QtCore.Signal(tuple)  # (x, y, width, height)

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.WindowStaysOnTopHint
            | QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        # Remove the transparent for mouse events to allow interaction
        self.setCursor(QtCore.Qt.CrossCursor)

        # Get all screens for multi-monitor support
        primary_screen = QtWidgets.QApplication.primaryScreen()
        if primary_screen:
            self.setGeometry(primary_screen.geometry())

        # Make sure it's visible and on top
        self.setWindowState(QtCore.Qt.WindowFullScreen)

        self.start_pos = None
        self.end_pos = None
        self.selecting = False

    def showEvent(self, event):
        super().showEvent(event)
        # Ensure it covers the entire screen
        primary_screen = QtWidgets.QApplication.primaryScreen()
        if primary_screen:
            geometry = primary_screen.geometry()
            self.setGeometry(geometry)
        self.raise_()
        self.activateWindow()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.start_pos = event.position().toPoint()
            self.end_pos = self.start_pos
            self.selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self.selecting:
            self.end_pos = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton and self.selecting:
            self.selecting = False
            if self.start_pos and self.end_pos:
                # Calculate rectangle
                x1, y1 = self.start_pos.x(), self.start_pos.y()
                x2, y2 = self.end_pos.x(), self.end_pos.y()

                left = min(x1, x2)
                top = min(y1, y2)
                width = abs(x2 - x1)
                height = abs(y2 - y1)

                if width > 10 and height > 10:  # Minimum size
                    self.selection_made.emit((left, top, width, height))

            self.hide()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.hide()
        super().keyPressEvent(event)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # Always draw a semi-transparent overlay to make it visible
        painter.fillRect(self.rect(), QtGui.QColor(0, 0, 0, 50))

        # Draw instructions text
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255)))
        painter.setFont(QtGui.QFont("Segoe UI", 16))
        text_rect = self.rect()
        text_rect.setHeight(100)
        instruction_text = "Click and drag to select screen area • Press ESC to cancel"
        painter.drawText(text_rect, QtCore.Qt.AlignCenter, instruction_text)

        if not self.selecting or not self.start_pos or not self.end_pos:
            return

        # Calculate selection rectangle
        x1, y1 = self.start_pos.x(), self.start_pos.y()
        x2, y2 = self.end_pos.x(), self.end_pos.y()

        left = min(x1, x2)
        top = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)

        selection_rect = QtCore.QRect(left, top, width, height)

        # Clear the selection area (make it less dark)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
        painter.fillRect(selection_rect, QtGui.QColor(255, 255, 255, 100))

        # Draw selection border
        pen = QtGui.QPen(QtGui.QColor(190, 0, 0), 3, QtCore.Qt.SolidLine)
        painter.setPen(pen)
        painter.drawRect(selection_rect)

        # Draw dimension text
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255)))
        painter.setFont(QtGui.QFont("Segoe UI", 14, QtGui.QFont.Bold))
        text = f"{width} x {height}"
        text_y = max(top - 25, 25)  # Ensure text is visible
        painter.drawText(left, text_y, text)


class Overlay(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.Tool
            | QtCore.Qt.WindowStaysOnTopHint
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        # Remove transparent for mouse events to allow clicking
        self.text = ""
        self.padding = 10
        self.font = QtGui.QFont("Segoe UI", 10)
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.hide()

    def show_text_near(self, text, near_pos):
        if not text:
            self.hide()
            return
        self.text = text

        # Fixed width for consistent layout
        fixed_width = 400

        # Calculate height needed for wrapped text
        fm = QtGui.QFontMetrics(self.font)
        text_rect = QtCore.QRect(0, 0, fixed_width - self.padding * 2, 1000)
        bounded_rect = fm.boundingRect(text_rect, QtCore.Qt.TextWordWrap, text)

        # Set overlay size
        width = fixed_width
        height = bounded_rect.height() + self.padding * 2 + 25  # Extra space for hints
        self.resize(width, height)

        # Position near cursor with slight offset
        x = near_pos[0] + 16
        y = near_pos[1] + 16
        self.move(x, y)
        self.show()
        self.raise_()
        self.repaint()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            # Left click dismisses the overlay
            self.hide()
        elif event.button() == QtCore.Qt.RightButton:
            # Right click copies text to clipboard
            self.copy_to_clipboard()
        super().mousePressEvent(event)

    def copy_to_clipboard(self):
        """Copy the translation text to clipboard"""
        if not self.text:
            return
        try:
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardText(self.text)
            win32clipboard.CloseClipboard()
            print(f"Copied to clipboard: {self.text[:50]}...")
            # Brief visual feedback - could add a small "Copied!" indicator here
        except Exception as e:
            print(f"Error copying to clipboard: {e}")
            try:
                win32clipboard.CloseClipboard()
            except Exception:
                pass

    def paintEvent(self, _):
        if not self.text:
            return
        painter = QtGui.QPainter(self)
        painter.setRenderHints(
            QtGui.QPainter.Antialiasing | QtGui.QPainter.TextAntialiasing
        )
        # Bubble background
        bg = QtGui.QColor(20, 20, 20, 200)
        pen = QtGui.QPen(QtGui.QColor(255, 255, 255, 220))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(bg)
        rect = self.rect()
        painter.drawRoundedRect(rect, 10, 10)
        # Text
        painter.setFont(self.font)
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255)))
        painter.drawText(
            rect.adjusted(self.padding, self.padding, -self.padding, -self.padding),
            QtCore.Qt.TextWordWrap,
            self.text,
        )

        # Add interaction hints at the bottom
        hint_font = QtGui.QFont("Segoe UI", 8)
        painter.setFont(hint_font)
        painter.setPen(QtGui.QPen(QtGui.QColor(180, 180, 180)))
        hint_text = "Left click: dismiss • Right click: copy"
        hint_rect = QtCore.QRect(
            self.padding, rect.height() - 20, rect.width() - self.padding * 2, 15
        )
        painter.drawText(hint_rect, QtCore.Qt.AlignCenter, hint_text)


def run():
    app = QtWidgets.QApplication([])
    overlay = Overlay()
    selection_overlay = SelectionOverlay()

    print("Press Ctrl+Alt+T to select screen area and translate.")
    print("Press Ctrl+Alt+C to translate clipboard content.")
    print("Press Ctrl+Alt+Q to quit.")

    # Add debouncing for hotkeys
    last_translate_time = 0
    last_clipboard_time = 0
    last_quit_time = 0

    def on_selection_made(rect):
        try:
            img = capture_rect(rect)
            german = ocr_de(img)
            english = translate_deepl(german)
            # Show translation near the center of the selected area
            center_x = rect[0] + rect[2] // 2
            center_y = rect[1] + rect[3] // 2
            result_text = english or "(no text detected)"
            overlay.show_text_near(result_text, (center_x, center_y))
        except Exception as e:
            print(f"Translation error: {e}")
            center_x = rect[0] + rect[2] // 2
            center_y = rect[1] + rect[3] // 2
            overlay.show_text_near(f"Error: {str(e)}", (center_x, center_y))

    selection_overlay.selection_made.connect(on_selection_made)

    def on_translate_clipboard():
        nonlocal last_clipboard_time
        current_time = time.time()
        if current_time - last_clipboard_time < 1.0:  # 1 second debounce
            return
        last_clipboard_time = current_time

        print("Clipboard hotkey")

        # Get current clipboard content
        clipboard_text = get_clipboard_text()

        if clipboard_text and clipboard_text.strip():
            print(f"Clipboard text: {clipboard_text[:50]}...")
            try:
                # Translate the clipboard text
                english = translate_deepl(clipboard_text.strip())
                result_text = english or "(translation failed)"

                # Show translation near mouse cursor
                x, y = win32api.GetCursorPos()
                overlay.show_text_near(result_text, (x, y))
                print("Clipboard text translated")
            except Exception as e:
                print(f"Translation error: {e}")
                x, y = win32api.GetCursorPos()
                overlay.show_text_near(f"Error: {str(e)}", (x, y))
        else:
            print("Empty clipboard")
            x, y = win32api.GetCursorPos()
            overlay.show_text_near("Empty clipboard", (x, y))

    def on_translate():
        nonlocal last_translate_time
        current_time = time.time()
        if current_time - last_translate_time < 1.0:  # 1 second debounce
            return
        last_translate_time = current_time

        print("Screen selection hotkey")

        # Hide any existing overlay
        overlay.hide()

        # Reset selection state
        selection_overlay.start_pos = None
        selection_overlay.end_pos = None
        selection_overlay.selecting = False

        # Show selection overlay for screen capture
        selection_overlay.show()
        selection_overlay.raise_()
        selection_overlay.activateWindow()
        selection_overlay.setFocus()

    def on_quit():
        nonlocal last_quit_time
        current_time = time.time()
        if current_time - last_quit_time < 0.5:  # 0.5 second debounce
            return
        last_quit_time = current_time

        overlay.close()
        selection_overlay.close()
        QtWidgets.QApplication.quit()

    # Poll for hotkeys without blocking the Qt loop
    def check_hotkeys():
        if keyboard.is_pressed("ctrl+alt+t"):
            on_translate()
        elif keyboard.is_pressed("ctrl+alt+c"):
            on_translate_clipboard()
        elif keyboard.is_pressed("ctrl+alt+q"):
            on_quit()

    timer = QtCore.QTimer()
    timer.timeout.connect(check_hotkeys)
    timer.start(120)  # check ~8x/second
    app.exec()


if __name__ == "__main__":
    run()
