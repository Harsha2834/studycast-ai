from pathlib import Path

import fitz
from docx import Document
from pptx import Presentation

from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
)
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TesseractCliOcrOptions,
)


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Minimum amount of text considered sufficient from a PDF.
# If a PDF contains less than this amount, OCR is attempted.
MIN_PDF_TEXT_LENGTH = 100


# ---------------------------------------------------------
# Normalization
# ---------------------------------------------------------

def normalize_text(text: str) -> str:
    """
    Clean extracted document text while preserving useful
    line structure.
    """

    lines = []

    for line in text.splitlines():
        line = line.strip()

        if line:
            lines.append(line)

    return "\n".join(lines)


# ---------------------------------------------------------
# Normal PDF extraction using PyMuPDF
# ---------------------------------------------------------

def extract_pdf_text(path: Path) -> str:
    """
    Extract embedded text from a normal text-based PDF
    using PyMuPDF.
    """

    document = fitz.open(path)

    try:
        text = "\n".join(
            page.get_text("text")
            for page in document
        )
    finally:
        document.close()

    return normalize_text(text)


# ---------------------------------------------------------
# OCR PDF extraction using Docling + Tesseract
# ---------------------------------------------------------

def extract_pdf_with_ocr(path: Path) -> str:
    """
    Extract text from scanned/image-based PDFs using
    Docling with Tesseract OCR.
    """

    pipeline_options = PdfPipelineOptions()

    # Enable OCR
    pipeline_options.do_ocr = True

    # Explicitly use the Windows Tesseract installation
    pipeline_options.ocr_options = TesseractCliOcrOptions(
        lang=["eng"],
        tesseract_cmd=TESSERACT_PATH,
        scale=3.0,
        psm=3,
    )

    # Preserve table structure when possible
    pipeline_options.do_table_structure = True

    converter = DocumentConverter(
        format_options={
            "pdf": PdfFormatOption(
                pipeline_options=pipeline_options
            )
        }
    )

    result = converter.convert(path)

    document = result.document

    text = document.export_to_markdown()

    return normalize_text(text)


# ---------------------------------------------------------
# PDF extraction strategy
# ---------------------------------------------------------

def extract_pdf(path: Path) -> str:
    """
    Hybrid PDF extraction.

    1. Try normal PyMuPDF extraction.
    2. If insufficient text is found, fall back to OCR.
    """

    print(f"[DocumentService] Processing PDF: {path}")

    # First attempt: normal PDF text extraction
    text = extract_pdf_text(path)

    print(
        f"[DocumentService] PyMuPDF extracted "
        f"{len(text)} characters."
    )

    # Normal text-based PDF
    if len(text) >= MIN_PDF_TEXT_LENGTH:
        print(
            "[DocumentService] Sufficient embedded text found. "
            "Using PyMuPDF result."
        )

        return text

    # Scanned/image PDF
    print(
        "[DocumentService] Insufficient embedded text detected."
    )

    print(
        "[DocumentService] Falling back to "
        "Docling + Tesseract OCR..."
    )

    ocr_text = extract_pdf_with_ocr(path)

    print(
        f"[DocumentService] OCR extracted "
        f"{len(ocr_text)} characters."
    )

    if not ocr_text:
        raise ValueError(
            "No text could be extracted from the PDF "
            "using either normal extraction or OCR."
        )

    return ocr_text


# ---------------------------------------------------------
# Main document extraction function
# ---------------------------------------------------------

def extract(path):
    """
    Extract textual content from supported document formats.

    Supported:
        PDF
        DOCX
        PPTX
        TXT
    """

    p = Path(path)
    suffix = p.suffix.lower()

    print(
        f"[DocumentService] Extracting document: {p.name}"
    )

    # -----------------------------------------------------
    # PDF
    # -----------------------------------------------------

    if suffix == ".pdf":

        text = extract_pdf(p)

    # -----------------------------------------------------
    # DOCX
    # -----------------------------------------------------

    elif suffix == ".docx":

        document = Document(p)

        text = "\n".join(
            paragraph.text
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        )

        text = normalize_text(text)

    # -----------------------------------------------------
    # PPTX
    # -----------------------------------------------------

    elif suffix == ".pptx":

        presentation = Presentation(p)

        extracted_lines = []

        for slide in presentation.slides:

            for shape in slide.shapes:

                if hasattr(shape, "text"):

                    value = shape.text.strip()

                    if value:
                        extracted_lines.append(value)

        text = normalize_text(
            "\n".join(extracted_lines)
        )

    # -----------------------------------------------------
    # TXT
    # -----------------------------------------------------

    elif suffix == ".txt":

        text = p.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        text = normalize_text(text)

    # -----------------------------------------------------
    # Unsupported
    # -----------------------------------------------------

    else:

        raise ValueError(
            f"Unsupported file type: {suffix}"
        )

    # -----------------------------------------------------
    # Final validation
    # -----------------------------------------------------

    if not text:
        raise ValueError(
            "No extractable text was found in the document."
        )

    print(
        f"[DocumentService] Final extracted text: "
        f"{len(text)} characters."
    )

    return text