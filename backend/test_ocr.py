from pathlib import Path

from docling.document_converter import DocumentConverter
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TesseractCliOcrOptions,
)
from docling.document_converter import PdfFormatOption


PDF_PATH = Path("test.pdf")

print("Starting Docling with Tesseract OCR...")
print("PDF:", PDF_PATH.resolve())


pipeline_options = PdfPipelineOptions()

# Enable OCR
pipeline_options.do_ocr = True

# Explicitly use Tesseract
pipeline_options.ocr_options = TesseractCliOcrOptions(
    lang=["eng"]
)

# Enable table structure processing
pipeline_options.do_table_structure = True


converter = DocumentConverter(
    format_options={
        "pdf": PdfFormatOption(
            pipeline_options=pipeline_options
        )
    }
)


result = converter.convert(PDF_PATH)

document = result.document

print("\n========== EXTRACTED TEXT ==========\n")

text = document.export_to_markdown()

print(text[:10000])

print("\n========== OCR TEST COMPLETE ==========\n")