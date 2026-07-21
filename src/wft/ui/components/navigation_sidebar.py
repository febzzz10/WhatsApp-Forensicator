from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from wft.ui.pages.page_id import PageId
from wft.ui.components.navigation_item import NavigationItem

_GROUPS: list[tuple[str, list[tuple[str, PageId]]]] = [
    ("Case Management", [
        ("Dashboard", PageId.DASHBOARD),
        ("Cases", PageId.CASES),
        ("Evidence", PageId.EVIDENCE),
    ]),
    ("Acquisition", [
        ("ADB Extractor", PageId.ADB_EXTRACTOR),
    ]),
    ("Analysis", [
        ("Chat Viewer", PageId.CHATS),
        ("Contacts", PageId.CONTACTS),
        ("Groups", PageId.GROUPS),
        ("Calls", PageId.CALLS),
        ("Media", PageId.MEDIA),
        ("Timeline", PageId.TIMELINE),
        ("Recovered Data", PageId.RECOVERED),
        ("VoIP Analysis", PageId.VOIP),
    ]),
    ("Tools", [
        ("Decryptor", PageId.DECRYPTOR),
        ("Search", PageId.SEARCH),
        ("Reports", PageId.REPORTS),
    ]),
    ("System", [
        ("Audit Log", PageId.AUDIT),
        ("Settings", PageId.SETTINGS),
    ]),
]


class NavigationSidebar(QWidget):
    page_selected = Signal(PageId)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._is_collapsed = False
        self._items: dict[PageId, NavigationItem] = {}

        self.setObjectName("NavigationSidebar")
        self.setMinimumWidth(56)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)

        self._outer_layout = QVBoxLayout(self)
        self._outer_layout.setContentsMargins(0, 0, 0, 0)
        self._outer_layout.setSpacing(0)

        self._collapse_btn = QPushButton("\u2630")
        self._collapse_btn.setObjectName("sidebarCollapseBtn")
        self._collapse_btn.setCursor(Qt.PointingHandCursor)
        self._collapse_btn.clicked.connect(self.toggle_collapse)
        self._outer_layout.addWidget(self._collapse_btn)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._scroll_content = QWidget()
        self._nav_layout = QVBoxLayout(self._scroll_content)
        self._nav_layout.setContentsMargins(4, 4, 4, 4)
        self._nav_layout.setSpacing(2)
        self._nav_layout.addStretch()

        self._build_groups()

        scroll.setWidget(self._scroll_content)
        self._outer_layout.addWidget(scroll, 1)

    def _build_groups(self) -> None:
        for group_name, items in _GROUPS:
            header = QLabel(group_name)
            header.setObjectName("sidebarGroupHeader")
            self._nav_layout.addWidget(header)

            for label, page_id in items:
                item = NavigationItem(label)
                self._nav_layout.addWidget(item)
                self._items[page_id] = item
                item.clicked.connect(
                    lambda checked=False, pid=page_id: self._on_item_clicked(pid)
                )

    def _on_item_clicked(self, page_id: PageId) -> None:
        self.page_selected.emit(page_id)

    def set_active(self, page_id: PageId | None) -> None:
        for pid, item in self._items.items():
            item.set_active(pid == page_id)

    def toggle_collapse(self) -> None:
        self._is_collapsed = not self._is_collapsed
        for item in self._items.values():
            item.setVisible(not self._is_collapsed)
        for i in range(self._nav_layout.count()):
            w = self._nav_layout.itemAt(i).widget()
            if isinstance(w, QLabel) and w.objectName() == "sidebarGroupHeader":
                w.setVisible(not self._is_collapsed)

    def _item_count(self) -> int:
        return len(self._items)

    @property
    def is_collapsed(self) -> bool:
        return self._is_collapsed