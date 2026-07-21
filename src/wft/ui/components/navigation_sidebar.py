from PySide6.QtCore import Qt, QVariantAnimation, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)
from shiboken6 import isValid
from wft.ui.pages.page_id import PageId
from wft.ui.components.navigation_item import NavigationItem
from wft.ui.theme.tokens import DesignTokens

_COLLAPSE_ICON = "\u25C0"
_EXPAND_ICON = "\u25B6"
_TOGGLE_SIZE = 36

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

    def __init__(self, tokens: DesignTokens | None = None, parent=None) -> None:
        super().__init__(parent)
        self._tokens = tokens or DesignTokens()
        self._is_collapsed = False
        self._items: dict[PageId, NavigationItem] = {}
        self._settings_callback = None
        self._animation: QVariantAnimation | None = None

        self._expanded_width = self._tokens.sidebar_expanded_width
        self._collapsed_width = self._tokens.sidebar_collapsed_width

        self.setObjectName("NavigationSidebar")
        self.setMinimumWidth(self._expanded_width)
        self.setMaximumWidth(self._expanded_width)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)

        self._outer_layout = QVBoxLayout(self)
        self._outer_layout.setContentsMargins(0, 0, 0, 0)
        self._outer_layout.setSpacing(0)

        self._top_layout = QHBoxLayout()
        self._top_layout.setContentsMargins(0, 8, 0, 4)
        self._top_layout.setSpacing(0)

        self._collapse_btn = QPushButton(_COLLAPSE_ICON)
        self._collapse_btn.setObjectName("sidebarToggleBtn")
        self._collapse_btn.setCursor(Qt.PointingHandCursor)
        self._collapse_btn.setToolTip("Collapse sidebar")
        self._collapse_btn.setAccessibleName("Collapse sidebar")
        self._collapse_btn.setFixedSize(_TOGGLE_SIZE, _TOGGLE_SIZE)
        self._collapse_btn.clicked.connect(self.toggle_collapse)

        self._top_layout.addStretch()
        self._top_layout.addWidget(self._collapse_btn)
        self._outer_layout.addLayout(self._top_layout)

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

    def set_persistence_callback(self, callback) -> None:
        self._settings_callback = callback

    def toggle_collapse(self) -> None:
        self._is_collapsed = not self._is_collapsed
        target = self._collapsed_width if self._is_collapsed else self._expanded_width

        for item in self._items.values():
            item.setVisible(not self._is_collapsed)
        for i in range(self._nav_layout.count()):
            w = self._nav_layout.itemAt(i).widget()
            if isinstance(w, QLabel) and w.objectName() == "sidebarGroupHeader":
                w.setVisible(not self._is_collapsed)

        if self._is_collapsed:
            self._collapse_btn.setText(_EXPAND_ICON)
            self._collapse_btn.setToolTip("Expand sidebar")
            self._collapse_btn.setAccessibleName("Expand sidebar")
            self._top_layout.setContentsMargins(0, 8, 0, 4)
        else:
            self._collapse_btn.setText(_COLLAPSE_ICON)
            self._collapse_btn.setToolTip("Collapse sidebar")
            self._collapse_btn.setAccessibleName("Collapse sidebar")
            self._top_layout.setContentsMargins(0, 8, 0, 4)

        self._animate_width(target)

        if self._settings_callback:
            self._settings_callback(self._is_collapsed)

    def _dispose_animation(self) -> None:
        old = self._animation
        self._animation = None
        if old is None:
            return
        if not isValid(old):
            return
        try:
            old.stop()
        except RuntimeError:
            pass
        try:
            old.valueChanged.disconnect()
        except (RuntimeError, TypeError):
            pass
        try:
            old.finished.disconnect()
        except (RuntimeError, TypeError):
            pass
        try:
            old.deleteLater()
        except RuntimeError:
            pass

    def _animate_width(self, target: int) -> None:
        self._dispose_animation()

        start_width = self.width()
        if (
            self._tokens.reduced_motion
            or start_width == target
        ):
            self._apply_sidebar_width(target)
            return

        animation = QVariantAnimation(self)
        self._animation = animation

        animation.setDuration(self._tokens.animation_duration_normal_ms)
        animation.setStartValue(start_width)
        animation.setEndValue(target)
        animation.valueChanged.connect(
            lambda v: self._apply_sidebar_width(v)
        )
        animation.finished.connect(
            lambda anim=animation, tgt=target: self._on_animation_finished(anim, tgt)
        )
        animation.start()

    def _on_animation_finished(
        self,
        animation: QVariantAnimation,
        target_width: int,
    ) -> None:
        if self._animation is not animation:
            return
        self._apply_sidebar_width(target_width)
        self._dispose_animation()

    def _apply_sidebar_width(self, value: int | float) -> None:
        width = int(round(value))
        self.setMinimumWidth(width)
        self.setMaximumWidth(width)

    def _item_count(self) -> int:
        return len(self._items)

    @property
    def is_collapsed(self) -> bool:
        return self._is_collapsed