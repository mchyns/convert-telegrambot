import tempfile
import zipfile
from pathlib import Path
import pymupdf as fitz
import pytest
from app.conversion.pdf_to_docx import convert_pdf_to_docx


def test_pdf_to_docx_conversion():
    """Test PDF to DOCX conversion pipeline with synthetic PDF."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        pdf_file = tmp_path / "sample.pdf"
        docx_file = tmp_path / "output.docx"

        # Create a simple PDF document with text
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Document Converter Test: Telegram Bot")
        page.insert_text((72, 100), "Testing PDF to DOCX using pdf2docx.")
        doc.save(str(pdf_file))
        doc.close()

        # Run conversion
        result = convert_pdf_to_docx(pdf_file, docx_file)

        assert result.exists()
        assert result.stat().st_size > 0
        assert result.suffix.lower() == ".docx"

        # Check DOCX ZIP archive integrity
        with zipfile.ZipFile(result, "r") as zf:
            assert "[Content_Types].xml" in zf.namelist()
            assert any(f.startswith("word/") for f in zf.namelist())
