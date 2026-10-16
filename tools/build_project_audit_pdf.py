"""Render the dated Markdown audit without changing operational application code."""
from pathlib import Path
import html
import re
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from pypdf import PdfReader
import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1]
STEM = 'QIU_SLD_Project_Audit_2026-10-15'
SOURCE = ROOT / 'docs/review' / (STEM + '.md')
OUTPUT = SOURCE.with_suffix('.pdf')
QA = ROOT / '.agency/audit-2026-10-15/pdf'

for name, filename in [('Audit', 'arial.ttf'), ('AuditBold', 'arialbd.ttf'), ('AuditItalic', 'ariali.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(Path('C:/Windows/Fonts') / filename)))
pdfmetrics.registerFontFamily('Audit', normal='Audit', bold='AuditBold', italic='AuditItalic', boldItalic='AuditBold')

styles = {
    'body': ParagraphStyle('body', fontName='Audit', fontSize=9.5, leading=13, spaceAfter=7),
    'title': ParagraphStyle('title', fontName='AuditBold', fontSize=24, leading=28, spaceAfter=14),
    'h1': ParagraphStyle('h1', fontName='AuditBold', fontSize=18, leading=22, spaceAfter=13, keepWithNext=True),
    'h2': ParagraphStyle('h2', fontName='AuditBold', fontSize=13, leading=17, spaceBefore=8, spaceAfter=9, keepWithNext=True),
    'h3': ParagraphStyle('h3', fontName='AuditBold', fontSize=11, leading=14, spaceBefore=6, spaceAfter=6, keepWithNext=True),
    'table': ParagraphStyle('table', fontName='Audit', fontSize=8.4, leading=11.3, alignment=TA_LEFT),
}


def rich(text):
    value = html.escape(text)
    value = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', value)
    value = re.sub(r'`(.+?)`', r'<font name="Audit">\1</font>', value)
    return value


def page(canvas, doc):
    width, height = A4
    canvas.setFont('Audit', 8)
    canvas.setFillColor(colors.HexColor('#526071'))
    canvas.drawString(42, height - 27, 'QIU Student Life Division | Project audit and workflow plan')
    canvas.setStrokeColor(colors.HexColor('#D8DEE6'))
    canvas.line(42, height - 34, width - 42, height - 34)
    canvas.drawString(42, 23, '15 October 2026 | Source and local-evidence review')
    canvas.drawRightString(width - 42, 23, str(doc.page))


def build():
    lines = SOURCE.read_text(encoding='utf-8').splitlines()
    story = []
    index = 0
    for line in lines:
        if line.startswith('# ') and line != '# QIU Student Life Division System':
            index += 1
    assert index == 15, index
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line == '<!-- pagebreak -->':
            story.append(PageBreak())
        elif line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].startswith('|'):
                row = [part.strip() for part in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[-: ]+', part) for part in row):
                    rows.append([Paragraph(rich(part), styles['table']) for part in row])
                i += 1
            columns = len(rows[0])
            ratios = [.24, .25, .51] if columns == 3 else [.24, .26, .5] if columns == 4 else [1 / columns] * columns
            if columns == 4:
                ratios = [.22, .26, .26, .26]
            width = A4[0] - 84
            table = Table(rows, colWidths=[width * ratio for ratio in ratios], repeatRows=1, hAlign='LEFT')
            table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E8EDF2')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FB')]),
                ('GRID', (0, 0), (-1, -1), .4, colors.HexColor('#B9C3CD')),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.extend([table, Spacer(1, 8)])
            continue
        elif line.startswith('# '):
            story.append(Paragraph(rich(line[2:]), styles['title' if 'Division System' in line else 'h1']))
        elif line.startswith('## '):
            story.append(Paragraph(rich(line[3:]), styles['h2']))
        elif line.startswith('### '):
            story.append(Paragraph(rich(line[4:]), styles['h3']))
        else:
            if line.startswith('- '):
                line = '• ' + line[2:]
            story.append(Paragraph(rich(line), styles['body']))
        i += 1
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, rightMargin=42, leftMargin=42,
                           topMargin=48, bottomMargin=42,
                           title='QIU SLD Project Review, Workflows and Delivery Plan',
                           author='Prepared for QIU SLD and ICT')
    doc.build(story, onFirstPage=page, onLaterPages=page)
    reader = PdfReader(OUTPUT)
    text = '\n'.join(p.extract_text() for p in reader.pages)
    assert all(f'W{n:02}' in text for n in range(1, 19))
    assert all(f'F{n:02}' in text for n in range(1, 11))
    assert '\ufffd' not in text
    QA.mkdir(parents=True, exist_ok=True)
    pdf = pdfium.PdfDocument(str(OUTPUT))
    for number in range(len(pdf)):
        pdf[number].render(scale=1.4).to_pil().save(QA / f'page-{number + 1}.png')
    print(f'Created {OUTPUT.name}: {len(reader.pages)} pages; W01-W18 and F01-F10 present; all pages rendered.')


if __name__ == '__main__':
    build()
