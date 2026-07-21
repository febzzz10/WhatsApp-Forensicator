from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QSplitter, QTextBrowser,
    QLineEdit, QComboBox, QFrame,
)
from PySide6.QtCore import Qt

from wft.application.services.case_context import ActiveCaseContext
from wft.ui.components import PageHeader, NeonButton, StatusBadge, EmptyState
from wft.infrastructure.database.artefact_repositories import (
    ConversationRepository,
    MessageRepository,
)


class ChatsPage(QWidget):
    def __init__(self, ctx: ActiveCaseContext) -> None:
        super().__init__()
        self._ctx = ctx
        self._current_conv_id: Optional[int] = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        header = PageHeader("Chat Viewer", "Review conversation messages and provenance")
        layout.addWidget(header)

        splitter = QSplitter(Qt.Horizontal)

        conversation_panel = QWidget()
        conv_layout = QVBoxLayout(conversation_panel)
        conv_layout.setContentsMargins(0, 0, 0, 0)
        conv_layout.setSpacing(4)

        self._conv_search = QLineEdit()
        self._conv_search.setPlaceholderText("Search conversations...")
        self._conv_search.textChanged.connect(self._on_search)
        conv_layout.addWidget(self._conv_search)

        conv_filter = QComboBox()
        conv_filter.addItems(["All", "Direct Chats", "Group Chats", "Recovered Only"])
        conv_layout.addWidget(conv_filter)

        self._conversation_list = QListWidget()
        self._conversation_list.currentRowChanged.connect(self._on_conversation_selected)
        conv_layout.addWidget(self._conversation_list, 1)

        splitter.addWidget(conversation_panel)

        chat_panel = QWidget()
        chat_layout = QVBoxLayout(chat_panel)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(4)

        self._chat_header = QFrame()
        self._chat_header.setStyleSheet(
            "background-color: #030A05; border: 1px solid #087A38; border-radius: 4px; padding: 8px;"
        )
        chat_header_layout = QHBoxLayout(self._chat_header)
        chat_header_layout.setContentsMargins(12, 8, 12, 8)

        self._chat_name = QLabel("Select a conversation")
        self._chat_name.setStyleSheet("color: #00F56A; font-size: 15px; font-weight: 600;")
        chat_header_layout.addWidget(self._chat_name)

        self._conv_badge = StatusBadge("Parsed", "parsed")
        chat_header_layout.addWidget(self._conv_badge)
        chat_header_layout.addStretch()

        chat_header_layout.addWidget(QLabel("Messages:"))
        self._msg_count_label = QLabel("0")
        self._msg_count_label.setStyleSheet("color: #00F56A; font-weight: 700;")
        chat_header_layout.addWidget(self._msg_count_label)

        chat_layout.addWidget(self._chat_header)

        self._message_view = QTextBrowser()
        self._message_view.setOpenExternalLinks(False)
        self._message_view.setStyleSheet(
            "QTextBrowser { background-color: #FFFFFF; color: #1A1A1A;"
            " border: 1px solid #087A38; border-radius: 4px; padding: 12px;"
            " font-size: 13px; }"
        )
        chat_layout.addWidget(self._message_view, 1)

        bottom_bar = QFrame()
        bottom_bar.setStyleSheet(
            "background-color: #030A05; border: 1px solid #087A38; border-radius: 4px; padding: 8px;"
        )
        bottom_bar.setFixedHeight(44)
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(8, 6, 8, 6)

        self._examiner_note = QLineEdit()
        self._examiner_note.setPlaceholderText("Add examiner note to this conversation...")
        bottom_layout.addWidget(self._examiner_note, 1)

        chat_layout.addWidget(bottom_bar)

        splitter.addWidget(chat_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter, 1)

    def on_activated(self) -> None:
        if self._ctx.is_active:
            self._refresh_conversations()

    def _refresh_conversations(self) -> None:
        self._conversation_list.clear()
        if not self._ctx.is_active:
            return
        try:
            repo = ConversationRepository(self._ctx.get_db())
            conversations = repo.list_with_stats(self._ctx.case_id)
            self._conversations_data = conversations
            for conv in conversations:
                title = conv.get("title") or conv.get("conversation_code", "Unknown")
                msg_count = conv.get("actual_message_count", conv.get("message_count", 0))
                conv_type = conv.get("conversation_type", "UNKNOWN")
                label = f"{title} [{conv_type}] \u2014 {msg_count} msgs"
                QListWidgetItem(label, self._conversation_list)
        except Exception:
            self._conversations_data = []

    def _on_search(self, text: str) -> None:
        for i in range(self._conversation_list.count()):
            item = self._conversation_list.item(i)
            if item:
                item.setHidden(text.lower() not in item.text().lower())

    def _on_conversation_selected(self, row: int) -> None:
        if row < 0 or not hasattr(self, "_conversations_data") or row >= len(self._conversations_data):
            return
        conv = self._conversations_data[row]
        self._current_conv_id = conv["id"]
        self._chat_name.setText(conv.get("title") or conv.get("conversation_code", "Conversation"))
        msg_count = conv.get("actual_message_count", conv.get("message_count", 0))
        self._msg_count_label.setText(str(msg_count))

        conv_type = conv.get("conversation_type", "UNKNOWN")
        badge_type = "parsed"
        if conv.get("origin") == "RECOVERED":
            badge_type = "recovered"
        self._conv_badge.set_text(conv_type)
        self._conv_badge.set_badge_type(badge_type)

        self._load_messages(conv["id"])

    def _load_messages(self, conversation_id: int) -> None:
        if not self._ctx.is_active:
            return
        try:
            repo = MessageRepository(self._ctx.get_db())
            messages = repo.list_for_conversation(conversation_id, limit=500)
            html = ""
            for m in messages:
                direction = m.get("direction", "UNKNOWN")
                sender = m.get("sender_name") or "Unknown"
                timestamp = m.get("sent_at_utc") or ""
                text = m.get("text_content") or "(no content)"
                msg_type = m.get("message_type", "TEXT")

                if direction == "INCOMING":
                    html += f'<div style="margin:4px 0;padding:6px 10px;background:#f0f0f0;border-radius:8px;max-width:80%">'
                else:
                    html += f'<div style="margin:4px 0;padding:6px 10px;background:#dcf8c6;border-radius:8px;max-width:80%;margin-left:auto">'
                html += f'<strong>{sender}</strong> <span style="color:#888;font-size:11px">{timestamp}</span><br>'
                if msg_type != "TEXT":
                    html += f'<em>[{msg_type}]</em> '
                html += f'{text}'
                html += '</div>'
            self._message_view.setHtml(html or "<p style='color:#888'>No messages in this conversation.</p>")
        except Exception:
            self._message_view.setHtml("<p style='color:#c00'>Error loading messages.</p>")
