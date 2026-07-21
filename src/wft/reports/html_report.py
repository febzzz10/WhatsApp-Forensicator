from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


_SIMPLE_CSS = """
<style>
body { font-family: 'Segoe UI', Arial, sans-serif; margin: 2em; color: #222; }
h1 { color: #1a1a2e; border-bottom: 2px solid #e0e0e0; padding-bottom: 0.3em; }
h2 { color: #333; margin-top: 1.5em; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; }
th, td { text-align: left; padding: 8px 12px; border: 1px solid #ddd; }
th { background-color: #f5f5f5; font-weight: 600; }
.footer { margin-top: 2em; font-size: 0.85em; color: #666; border-top: 1px solid #ddd; padding-top: 1em; }
.limitation { background: #fff3cd; padding: 1em; border-left: 4px solid #ffc107; margin: 1em 0; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 0.8em; }
.badge-parsed { background: #d4edda; color: #155724; }
.badge-recovered { background: #fff3cd; color: #856404; }
</style>
"""


class HtmlReportGenerator:
    def generate_case_summary(self, case_data: dict, output_path: Path) -> str:
        now = datetime.now(timezone.utc).isoformat(timespec="minutes").replace("+00:00", "Z")
        html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>Case Summary — {case_data.get('case_code', 'Unknown')}</title>{_SIMPLE_CSS}</head>
<body>
<h1>Case Summary</h1>
<table>
<tr><th>Case Code</th><td>{case_data.get('case_code', '')}</td></tr>
<tr><th>Title</th><td>{case_data.get('title', '')}</td></tr>
<tr><th>Status</th><td>{case_data.get('status', '')}</td></tr>
<tr><th>Time Zone</th><td>{case_data.get('display_timezone', 'UTC')}</td></tr>
<tr><th>Evidence Items</th><td>{case_data.get('evidence_count', 0)}</td></tr>
<tr><th>Messages</th><td>{case_data.get('message_count', 0)}</td></tr>
<tr><th>Contacts</th><td>{case_data.get('contact_count', 0)}</td></tr>
<tr><th>Calls</th><td>{case_data.get('call_count', 0)}</td></tr>
<tr><th>Media Files</th><td>{case_data.get('media_count', 0)}</td></tr>
</table>
<div class="limitation">
<strong>Limitations:</strong> Recovered records are best-effort and not guaranteed to be authentic.
IP-based locations are approximate. The application cannot decrypt call audio or video.
</div>
<div class="footer">
Generated: {now} | Tool: WhatsApp Forensic Toolkit v1.0.0a1
</div>
</body>
</html>"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html, encoding="utf-8")
        return html
