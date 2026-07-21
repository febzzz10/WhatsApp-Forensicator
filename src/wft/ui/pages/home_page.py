from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QFileDialog, QMessageBox, QFrame,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal

from wft.bootstrap import Container
from wft.ui.components import NeonButton


class RecentCaseCard(QFrame):
    opened = Signal(int, Path)

    def __init__(self, case_code: str, title: str, path: str, parent=None) -> None:
        super().__init__(parent)
        self._case_path = Path(path)
        self.setObjectName("recentCaseCard")
        self.setStyleSheet(
            "QFrame#recentCaseCard {"
            "  background-color: #061108; border: 1px solid #087A38;"
            "  border-radius: 6px; padding: 12px;"
            "}"
            "QFrame#recentCaseCard:hover { border: 1px solid #00F56A; }"
        )
        layout = QVBoxLayout(self)
        code_label = QLabel(case_code)
        code_label.setStyleSheet("color: #00F56A; font-size: 14px; font-weight: 700;")
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #EAF7EE; font-size: 13px;")
        path_label = QLabel(str(path))
        path_label.setStyleSheet("color: #6E9278; font-size: 10px;")
        layout.addWidget(code_label)
        layout.addWidget(title_label)
        layout.addWidget(path_label)
        self.setCursor(Qt.PointingHandCursor)

    def mouseDoubleClickEvent(self, event) -> None:
        self.opened.emit(0, self._case_path)


class HomePage(QWidget):
    def __init__(self, container: Container, main_window=None) -> None:
        super().__init__()
        self._container = container
        self._main_window = main_window
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(16)

        icon = QLabel("\u25C9")
        icon.setStyleSheet("color: #00F56A; font-size: 48px;")
        icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon)

        title = QLabel("WHATSAPP FORENSICATOR")
        title.setStyleSheet("color: #00F56A; font-size: 28px; font-weight: 700; letter-spacing: 2px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("COMPLETE FORENSICS SUITE \u2014 BY CYBER OCTOPUS")
        subtitle.setStyleSheet("color: #46A568; font-size: 12px; letter-spacing: 1px;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        desc = QLabel("Offline-first digital forensics for WhatsApp evidence")
        desc.setStyleSheet("color: #6E9278; font-size: 13px;")
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        layout.addSpacing(24)

        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignCenter)
        btn_row.setSpacing(16)

        new_case_btn = NeonButton("New Case", "primary")
        new_case_btn.setMinimumWidth(160)
        new_case_btn.clicked.connect(self._on_new_case)
        btn_row.addWidget(new_case_btn)

        open_case_btn = NeonButton("Open Case", "secondary")
        open_case_btn.setMinimumWidth(160)
        open_case_btn.clicked.connect(self._on_open_case)
        btn_row.addWidget(open_case_btn)

        layout.addLayout(btn_row)

        layout.addSpacing(32)

        self._recent_label = QLabel("RECENT CASES")
        self._recent_label.setStyleSheet("color: #A9C7B2; font-size: 13px; font-weight: 600;")
        self._recent_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._recent_label)

        self._recent_list = QListWidget()
        self._recent_list.setMaximumHeight(200)
        self._recent_list.setMaximumWidth(500)
        self._recent_list.setStyleSheet(
            "QListWidget { background: transparent; border: 1px solid #087A38; border-radius: 6px; }"
            "QListWidget::item { color: #EAF7EE; padding: 8px; border: none; }"
            "QListWidget::item:hover { background: #0B2413; }"
        )
        layout.addWidget(self._recent_list, alignment=Qt.AlignCenter)

        layout.addStretch()

    def on_activated(self) -> None:
        self._load_recent()

    def _load_recent(self) -> None:
        self._recent_list.clear()
        base_dirs = []
        if self._container.settings.data_dir:
            base_dirs.append(Path(self._container.settings.data_dir))
        base_dirs.append(Path.home() / ".wft")
        base_dirs.append(Path.home() / "wft_cases")

        seen = set()
        for base in base_dirs:
            if not base.exists():
                continue
            for child in sorted(base.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)[:10]:
                if child.is_dir() and (child / "case.toml").exists():
                    if child.name not in seen:
                        seen.add(child.name)
                        try:
                            import tomllib
                            meta = tomllib.loads((child / "case.toml").read_text(encoding="utf-8"))
                            item = QListWidgetItem(f"{meta.get('case_id', child.name)} \u2014 {meta.get('title', '')}")
                            item.setData(Qt.UserRole, str(child))
                            self._recent_list.addItem(item)
                        except Exception:
                            pass

        self._recent_list.itemDoubleClicked.connect(self._on_recent_clicked)

    def _on_recent_clicked(self, item) -> None:
        path = item.data(Qt.UserRole)
        if path and self._main_window:
            try:
                result = self._container.case_service.open_case(Path(path))
                self._main_window.on_case_opened(result["case"]["id"], Path(path))
            except Exception as exc:
                QMessageBox.critical(self, "Error", f"Could not open case:\n{exc}")

    def _on_new_case(self) -> None:
        if self._main_window:
            self._main_window.navigate_to("cases")

    def _on_open_case(self) -> None:
        dir_path = QFileDialog.getExistingDirectory(self, "Select Case Folder")
        if not dir_path:
            return
        case_path = Path(dir_path)
        try:
            result = self._container.case_service.open_case(case_path)
            if self._main_window:
                self._main_window.on_case_opened(result["case"]["id"], case_path)
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Could not open case:\n{exc}")
