"""Read calibration notes."""
from docx import Document
DOC = r"C:\Users\RobbieOrvis\Models\state-eps-data-repository\Notes on Calibration_01232025.docx"
d = Document(DOC)
for i, p in enumerate(d.paragraphs):
    if p.text.strip():
        print(p.text)
