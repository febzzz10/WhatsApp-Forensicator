from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton, QSizePolicy


class NavigationItem(QPushButton):
    def __init__(self, label: str, icon_text: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setText(label)
        self.setObjectName("NavigationItem")
        self.setProperty("active", False)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)
        self.setCheckable(False)

    def set_active(self, active: bool) -> None:
        self.setProperty("active", active)
        style = self.style()
        if style is not None:
            style.unpolish(self)
            style.polish(self)
        self.update()