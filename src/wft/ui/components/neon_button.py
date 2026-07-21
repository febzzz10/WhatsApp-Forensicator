from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton, QSizePolicy


class NeonButton(QPushButton):
    STYLES = {
        "primary": "",
        "secondary": "secondaryButton",
        "destructive": "destructiveButton",
        "warning": "warningButton",
    }

    def __init__(
        self,
        text: str = "",
        style: str = "primary",
        parent=None,
    ) -> None:
        super().__init__(text, parent)
        self._button_style = style
        obj_name = self.STYLES.get(style, "")
        if obj_name:
            self.setObjectName(obj_name)
        self.setMinimumHeight(36)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.setCursor(Qt.PointingHandCursor)

    def set_style(self, style: str) -> None:
        self._button_style = style
        obj_name = self.STYLES.get(style, "")
        self.setObjectName(obj_name)
        self.style().unpolish(self)
        self.style().polish(self)
