"""Verify and bundle the local SLD/ICT documentation handover."""
from pathlib import Path
import re
import shutil
import zipfile
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/review'
STEM = 'QIU_SLD_Requirements_and_Workflows'
shutil.copy2(ROOT / '.agency/qa/review-pack' / (STEM + '.pdf'), OUT / (STEM + '.pdf'))
source = (OUT / (STEM + '.md')).read_text(encoding='utf-8')
ids = re.findall(r'\bR(\d{2})\b', source)
assert ids == [f'{n:02}' for n in range(1, 74)], ids
reader = PdfReader(OUT / (STEM + '.pdf'))
assert len(reader.pages) == 18
text = '\n'.join(page.extract_text() for page in reader.pages)
assert all(f'R{n:02}' in text for n in range(1, 74))
assert 'â€' not in text and '\ufffd' not in text
with zipfile.ZipFile(OUT / (STEM + '.docx')) as doc:
    assert len([name for name in doc.namelist() if name.startswith('word/media/')]) == 5
    assert b'<w:pBdr' not in doc.read('word/styles.xml')

note = '''# QIU SLD and ICT review pack\n\nStart with the 18-page PDF. Use the Word copy to record review changes.\nThe Markdown copy is the maintainable source; workflow PNGs are in flows/.\n\nSLD: check requirements, responsibilities, policies and the review worksheet.\nICT: review chapters 15-17 and the supporting technical documents.\n\nThe main pack distinguishes prototype features, work under verification and planned modules.\nSupporting documents retain earlier dated implementation evidence; the current review pack\nand latest dated notes take precedence for scope/status. This is a review draft, not launch approval.\n\nNo database, credentials, personal records or application source are included.\nTechnical Markdown documents can be opened in a text editor or Markdown viewer.\n'''
(OUT / 'READ_ME_FIRST.md').write_text(note, encoding='utf-8')
files = [OUT / (STEM + extension) for extension in ('.pdf', '.docx', '.md')]
files += [OUT / 'READ_ME_FIRST.md'] + sorted((OUT / 'flows').glob('*.png'))
files += sorted((ROOT / 'docs').glob('*.md'))
files += [ROOT / name for name in ('RULES.md', 'PRD.md', 'PLAN.md', 'MEMORY.md')]
with zipfile.ZipFile(OUT / 'QIU_SLD_Review_Pack.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
    for file in files:
        destination = file.relative_to(OUT).as_posix() if file.is_relative_to(OUT) else 'supporting/' + file.name
        archive.write(file, destination)
with zipfile.ZipFile(OUT / 'QIU_SLD_Review_Pack.zip') as archive:
    assert archive.testzip() is None
print(f'Verified 18 pages, 73 ordered requirements, five diagrams; packaged {len(files)} documentation files.')
