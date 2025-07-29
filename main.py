import os, time
import requests
import pytesseract
from pytesseract import Output
from PIL import Image
import mss
import win32gui, win32api, win32con
from PySide6 import QtCore, QtGui, QtWidgets
import keyboard

DEEPL_KEY = os.getenv("DEEPL_API_KEY")  # set this in your environment
LANG_SRC, LANG_DST = "DE", "EN"         # German -> English

def get_mouse_rect(w=600, h=220):
    x, y = win32api.GetCursorPos()
    return (max(0, x - w//2), max(0, y - h//2), w, h)

def capture_rect(rect):
    left, top, w, h = rect
    with mss.mss() as sct:
        img = sct.grab({"left": left, "top": top, "width": w, "height": h})
    return Image.frombytes("RGB", img.size, img.rgb)

def ocr_de(image):
    # lang='deu' requires Tesseract German language data installed
    data = pytesseract.image_to_data(image, lang='deu', output_type=Output.DICT)
    # Join words into lines (simple merge; refine if needed)
    lines = {}
    for i, text in enumerate(data["text"]):
        if int(data["conf"][i]) > 60 and text.strip():
            line = data["line_num"][i]
            lines.setdefault(line, []).append(text)
    extracted = "\n".join(" ".join(words) for _, words in sorted(lines.items()))
    return extracted.strip()

def translate_deepl(text):
    if not text:
        return ""
    url = "https://api-free.deepl.com/v2/translate"
    resp = requests.post(url, data={
        "auth_key": DEEPL_KEY,
        "text": text,
        "source_lang": LANG_SRC,
        "target_lang": LANG_DST
    }, timeout=10)
    resp.raise_for_status()
    j = resp.json()
    return "\n".join(t["text"] for t in j.get("translations", []))

class Overlay(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint |
                           QtCore.Qt.Tool |
                           QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        self.text = ""
        self.padding = 10
        self.font = QtGui.QFont("Segoe UI", 10)
        self.hide()

    def show_text_near(self, text, near_pos):
        if not text:
            self.hide(); return
        self.text = text
        # Size to text
        fm = QtGui.QFontMetrics(self.font)
        lines = text.splitlines() or [text]
        width = max(fm.horizontalAdvance(l) for l in lines) + self.padding*2
        height = (fm.height() * len(lines)) + self.padding*2
        self.resize(width, height)
        # Position near cursor with slight offset
        x = near_pos[0] + 16
        y = near_pos[1] + 16
        self.move(x, y)
        self.show(); self.raise_(); self.repaint()

    def paintEvent(self, _):
        if not self.text: return
        painter = QtGui.QPainter(self)
        painter.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.TextAntialiasing)
        # Bubble background
        bg = QtGui.QColor(20, 20, 20, 200)
        pen = QtGui.QPen(QtGui.QColor(255,255,255,220))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(bg)
        rect = self.rect()
        painter.drawRoundedRect(rect, 10, 10)
        # Text
        painter.setFont(self.font)
        painter.setPen(QtGui.QPen(QtGui.QColor(255,255,255)))
        painter.drawText(rect.adjusted(self.padding, self.padding, -self.padding, -self.padding),
                         QtCore.Qt.TextWordWrap, self.text)

def run():
    app = QtWidgets.QApplication([])
    overlay = Overlay()
    print("Press Ctrl+Alt+T to translate around cursor. Press Ctrl+Alt+Q to quit.")
    
    # Add debouncing for hotkeys
    last_translate_time = 0
    last_quit_time = 0

    def on_translate():
        nonlocal last_translate_time
        current_time = time.time()
        if current_time - last_translate_time < 1.0:  # 1 second debounce
            return
        last_translate_time = current_time
        
        try:
            rect = get_mouse_rect()
            img = capture_rect(rect)
            german = ocr_de(img)
            english = translate_deepl(german)
            x, y = win32api.GetCursorPos()
            overlay.show_text_near(english or "(no text detected)", (x, y))
        except Exception as e:
            print(f"Translation error: {e}")
            overlay.show_text_near(f"Error: {str(e)}", win32api.GetCursorPos())

    def on_quit():
        nonlocal last_quit_time
        current_time = time.time()
        if current_time - last_quit_time < 0.5:  # 0.5 second debounce
            return
        last_quit_time = current_time
        
        overlay.close()
        QtWidgets.QApplication.quit()

    # Poll for hotkeys without blocking the Qt loop
    timer = QtCore.QTimer()
    timer.timeout.connect(lambda: (
        on_translate() if keyboard.is_pressed("ctrl+alt+t") else None,
        on_quit() if keyboard.is_pressed("ctrl+alt+q") else None
    ))
    timer.start(120)  # check ~8x/second
    app.exec()

if __name__ == "__main__":
    run()
