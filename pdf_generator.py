"""
PDF generator for daily news digests.
"""

from datetime import datetime
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas


class PDFGenerator:
    def __init__(self, output_dir="logs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_daily_digest_pdf(self, digest_text, category="world"):
        timestamp = datetime.now().strftime("%Y%m%d")
        file_name = f"daily_digest_{category}_{timestamp}.pdf"
        file_path = self.output_dir / file_name

        c = canvas.Canvas(str(file_path), pagesize=A4)
        width, height = A4

        y = height - 20 * mm
        c.setFont("Helvetica-Bold", 16)
        c.drawString(15 * mm, y, "Daily News Digest")

        y -= 8 * mm
        c.setFont("Helvetica", 10)
        c.drawString(15 * mm, y, f"Category: {category}")

        y -= 5 * mm
        c.drawString(15 * mm, y, f"Generated: {datetime.now().strftime('%d %b %Y %I:%M %p')}")

        y -= 10 * mm
        c.setFont("Helvetica", 11)

        for raw_line in digest_text.splitlines():
            line = raw_line.strip()
            if not line:
                y -= 5 * mm
            else:
                wrapped = self._wrap_line(line, max_chars=100)
                for sub in wrapped:
                    c.drawString(15 * mm, y, sub)
                    y -= 5 * mm

            if y < 20 * mm:
                c.showPage()
                c.setFont("Helvetica", 11)
                y = height - 20 * mm

        c.save()
        return str(file_path)

    def _wrap_line(self, text, max_chars=100):
        if len(text) <= max_chars:
            return [text]

        words = text.split()
        out = []
        current = []
        current_len = 0

        for word in words:
            additional = len(word) + (1 if current else 0)
            if current_len + additional > max_chars:
                out.append(" ".join(current))
                current = [word]
                current_len = len(word)
            else:
                current.append(word)
                current_len += additional

        if current:
            out.append(" ".join(current))

        return out
