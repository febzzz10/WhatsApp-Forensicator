from PySide6.QtGui import QFont
from PySide6.QtWidgets import QWidget


def ensure_valid_font_size(widget: QWidget, fallback: int = 10) -> None:
    font = widget.font()
    size = font.pointSize()
    if size <= 0:
        pixel_size = font.pixelSize()
        if pixel_size > 0:
            font.setPixelSize(pixel_size)
        else:
            font.setPointSize(fallback)
        widget.setFont(font)


def safe_font(widget: QWidget, fallback: int = 10) -> QFont:
    font = widget.font()
    size = font.pointSize()
    if size <= 0:
        pixel_size = font.pixelSize()
        if pixel_size > 0:
            f = QFont(font)
            f.setPixelSize(pixel_size)
            return f
        f = QFont(font)
        f.setPointSize(fallback)
        return f
    return QFont(font)
