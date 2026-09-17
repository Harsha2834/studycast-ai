from pathlib import Path
import fitz
from docx import Document
from pptx import Presentation
def extract(path):
    p=Path(path); s=p.suffix.lower()
    if s=='.pdf':
        d=fitz.open(p); t='\n'.join(x.get_text('text') for x in d); d.close()
    elif s=='.docx': t='\n'.join(x.text for x in Document(p).paragraphs)
    elif s=='.pptx':
        prs=Presentation(p); t='\n'.join(sh.text for sl in prs.slides for sh in sl.shapes if hasattr(sh,'text'))
    elif s=='.txt': t=p.read_text(encoding='utf-8',errors='ignore')
    else: raise ValueError('Unsupported file type')
    t='\n'.join(x.strip() for x in t.splitlines() if x.strip())
    if not t: raise ValueError('No extractable text. Scanned PDFs need OCR, a later module.')
    return t
