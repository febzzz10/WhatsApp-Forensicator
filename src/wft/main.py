import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMessageBox

from wft.bootstrap import Container
from wft.ui.main_window import MainWindow


def get_settings_path() -> Path:
    if sys.platform == "win32":
        base = Path.home() / "AppData" / "Roaming" / "WhatsApp Forensic Toolkit"
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / "WhatsApp Forensic Toolkit"
    else:
        base = Path.home() / ".config" / "whatsapp-forensic-toolkit"
    base.mkdir(parents=True, exist_ok=True)
    return base / "settings.toml"


def show_legal_notice(parent=None) -> bool:
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle("Legal and Ethical Use Notice")
    msg.setText(
        "WhatsApp Forensicator — Complete Forensics Suite\n\n"
        "This tool is intended for authorised forensic examiners, cybersecurity analysts, "
        "incident responders, and supervised students.\n\n"
        "By using this application you acknowledge that:\n"
        "• You have lawful authority to examine the data\n"
        "• You will not use this tool for unauthorised surveillance\n"
        "• Network capture is limited to authorised networks\n"
        "• IP-based locations are approximate\n"
        "• Deleted-data recovery is not guaranteed\n"
        "• The application cannot decrypt call audio or video\n\n"
        "Case data remains on your machine unless you explicitly enable external services."
    )
    msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
    return msg.exec() == QMessageBox.Ok


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("WhatsApp Forensicator")
    app.setApplicationVersion(MainWindow.APP_VERSION)

    if not show_legal_notice():
        sys.exit(0)

    settings_path = get_settings_path()
    container = Container(settings_path)
    container.log.info("Application started")

    window = MainWindow(container)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
