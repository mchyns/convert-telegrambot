import tempfile
import zipfile
from pathlib import Path
import pymupdf as fitz
import pytest
from app.conversion.validator import (
    ValidationError,
    detect_file_format,
    get_target_filename,
    sanitize_filename,
    validate_docx_content,
    validate_file_size,
    validate_pdf_content,
)


def test_sanitize_filename():
    assert sanitize_filename("../../etc/passwd") == "passwd"
    assert sanitize_filename("..\\..\\windows\\system32\\calc.exe") == "calc.exe"
    assert sanitize_filename("laporan:keuangan*2026?.docx") == "laporan_keuangan_2026_.docx"
    assert sanitize_filename("dokumen normal.pdf") == "dokumen normal.pdf"
    assert sanitize_filename("") == "document"
    assert sanitize_filename("...") == "document"


def test_get_target_filename():
    assert get_target_filename("laporan.docx", "pdf") == "laporan.pdf"
    assert get_target_filename("dokumen.pdf", "docx") == "dokumen.docx"
    assert get_target_filename("../../rahasia.docx", "pdf") == "rahasia.pdf"


def test_detect_file_format():
    assert detect_file_format("tugas.docx") == "docx"
    assert detect_file_format("tugas.DOCX") == "docx"
    assert detect_file_format("arsip.pdf") == "pdf"
    assert detect_file_format("arsip.PDF") == "pdf"

    with pytest.raises(ValidationError):
        detect_file_format("script.py")

    with pytest.raises(ValidationError):
        detect_file_format("image.png")


def test_validate_file_size():
    # 0 bytes should fail
    with pytest.raises(ValidationError):
        validate_file_size(0, 25 * 1024 * 1024)

    # Exceeding size should fail
    with pytest.raises(ValidationError):
        validate_file_size(30 * 1024 * 1024, 25 * 1024 * 1024)

    # Valid size should succeed
    validate_file_size(5 * 1024 * 1024, 25 * 1024 * 1024)


def test_validate_pdf_content():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # 1. Valid PDF
        valid_pdf = tmp_path / "valid.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Hello Telegram Converter!")
        doc.save(str(valid_pdf))
        doc.close()

        validate_pdf_content(valid_pdf)

        # 2. Corrupt / fake PDF
        fake_pdf = tmp_path / "fake.pdf"
        fake_pdf.write_text("This is not a real PDF file header.")
        with pytest.raises(ValidationError):
            validate_pdf_content(fake_pdf)


def test_validate_docx_content():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # 1. Fake DOCX (plain text)
        fake_docx = tmp_path / "fake.docx"
        fake_docx.write_text("Hello plain text")
        with pytest.raises(ValidationError):
            validate_docx_content(fake_docx)

        # 2. Incomplete ZIP (missing Content_Types.xml)
        bad_zip = tmp_path / "bad.docx"
        with zipfile.ZipFile(bad_zip, "w") as zf:
            zf.writestr("test.txt", "sample")
        with pytest.raises(ValidationError):
            validate_docx_content(bad_zip)

        # 3. Valid DOCX structure
        good_docx = tmp_path / "valid.docx"
        with zipfile.ZipFile(good_docx, "w") as zf:
            zf.writestr("[Content_Types].xml", "<Types></Types>")
            zf.writestr("word/document.xml", "<w:document></w:document>")
        validate_docx_content(good_docx)
