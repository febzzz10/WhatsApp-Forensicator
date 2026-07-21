from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QComboBox,
    QGroupBox, QGridLayout, QFrame, QPushButton, QFileDialog, QMessageBox,
)
from PySide6.QtCore import Qt

from wft.application.services.case_context import ActiveCaseContext
from wft.ui.components import PageHeader, NeonButton, StatisticCard, EmptyState
from wft.infrastructure.database.artefact_repositories import ReportRunRepository


class ReportsPage(QWidget):
    def __init__(self, ctx: ActiveCaseContext) -> None:
        super().__init__()
        self._ctx = ctx
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        header = PageHeader("Reports & Export", "Generate forensic reports and export packages")
        layout.addWidget(header)

        cats = QGroupBox("Report Categories")
        cats_layout = QVBoxLayout()

        conv_group = QGroupBox("Conversation")
        conv_grid = QGridLayout()
        for i, label in enumerate(["Chat PDF", "Chat HTML", "Chat CSV", "Chat JSON"]):
            btn = QPushButton(label)
            btn.setObjectName("secondaryButton")
            conv_grid.addWidget(btn, i // 2, i % 2)
        conv_group.setLayout(conv_grid)
        cats_layout.addWidget(conv_group)

        foren_group = QGroupBox("Forensic")
        foren_grid = QGridLayout()
        self._summary_btn = QPushButton("Case Summary")
        self._summary_btn.setObjectName("secondaryButton")
        self._summary_btn.clicked.connect(self._on_generate_summary)
        foren_grid.addWidget(self._summary_btn, 0, 0)

        foren_reports = [
            "Evidence Inventory", "Hash Verification",
            "Recovery Report", "Call Report", "Media Report",
            "Timeline Report", "Chain of Custody",
        ]
        for i, label in enumerate(foren_reports):
            btn = QPushButton(label)
            btn.setObjectName("secondaryButton")
            foren_grid.addWidget(btn, (i + 1) // 3, (i + 1) % 3)
        foren_group.setLayout(foren_grid)
        cats_layout.addWidget(foren_group)

        pkg_group = QGroupBox("Packages")
        pkg_grid = QGridLayout()
        for i, label in enumerate(["Selected Evidence ZIP", "Complete Case Package", "Redacted Review Package"]):
            btn = QPushButton(label)
            btn.setObjectName("secondaryButton")
            pkg_grid.addWidget(btn, 0, i)
        pkg_group.setLayout(pkg_grid)
        cats_layout.addWidget(pkg_group)

        cats.setLayout(cats_layout)
        layout.addWidget(cats)

        self._reports_list = QListWidget()
        self._reports_list.setMaximumHeight(200)
        layout.addWidget(QLabel("Generated Reports:"))
        layout.addWidget(self._reports_list, 1)

    def on_activated(self) -> None:
        if self._ctx.is_active:
            self._refresh()

    def _refresh(self) -> None:
        if not self._ctx.is_active:
            return
        try:
            repo = ReportRunRepository(self._ctx.get_db())
            reports = repo.list_for_case(self._ctx.case_id)
            self._reports_list.clear()
            for r in reports:
                text = f"[{r.get('status', '?')}] {r.get('title', '')} \u2014 {r.get('created_at_utc', '')}"
                QListWidgetItem(text, self._reports_list)
        except Exception:
            pass

    def _on_generate_summary(self) -> None:
        if not self._ctx.is_active:
            QMessageBox.warning(self, "No Case", "Open a case first.")
            return
        try:
            from wft.reports.html_report import HtmlReportGenerator
            from wft.application.services.statistics_service import StatisticsService

            stats = StatisticsService().get_case_stats(self._ctx.get_db(), self._ctx.case_id)
            case = self._ctx.case_path.name

            report_dir = self._ctx.case_path / "reports"
            report_dir.mkdir(exist_ok=True)
            output_path = report_dir / "case_summary.html"

            gen = HtmlReportGenerator()
            gen.generate_case_summary(
                {"case_code": case, "title": case, "status": "OPEN",
                 "display_timezone": "UTC", **stats},
                output_path,
            )

            repo = ReportRunRepository(self._ctx.get_db())
            import uuid
            report_code = f"R-{uuid.uuid4().hex[:8].upper()}"
            run_id = repo.create({
                "case_id": self._ctx.case_id,
                "report_code": report_code,
                "title": f"Case Summary - {case}",
                "report_type": "CASE_SUMMARY",
            })
            repo.complete(run_id, "COMPLETED")

            self._refresh()
            QMessageBox.information(self, "Report Generated", f"Summary saved to:\n{output_path}")
        except Exception as exc:
            QMessageBox.critical(self, "Error", f"Report generation failed:\n{exc}")
