import os
import re
import zipfile
from pathlib import Path
from typing import Tuple
import pymupdf as fitz


class ValidationError(Exception):
    """Custom exception raised when file validation fails."""
    pass


ALLOWED_EXTENSIONS = {".docx", ".pdf"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/octet-stream",  # Sometimes sent by Telegram clients
    "application/x-zip-compressed",
}

# Max uncompressed size for DOCX to protect against decompression/zip bombs (e.g., 200MB)
MAX_UNCOMPRESSED_DOCX_BYTES = 200 * 1024 * 1024
MAX_COMPRESSION_RATIO = 100


def sanitize_filename(filename: str, default_name: str = "document") -> str:
    """
    Sanitize input filename to prevent path traversal, control character injection,
    and invalid characters while preserving base name and valid extension.
    """
    if not filename:
        return default_name

    # Remove any directory path components
    filename = Path(filename).name
    # Strip null bytes and control characters
    filename = re.sub(r"[\x00-\x1f\x7f]", "", filename)
    # Strip unsafe path traversal sequences
    filename = re.sub(r"\.\.+", ".", filename)
    # Remove leading dots or slashes
    filename = filename.lstrip("./\\ ")

    # Filter to safe characters (alphanumeric, unicode letters, dash, underscore, space, dot)
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename).strip()

    if not filename or filename == ".":
        return default_name

    return filename


def get_target_filename(original_filename: str, target_format: str) -> str:
    """Generate target filename preserving the original stem."""
    safe_name = sanitize_filename(original_filename)
    path = Path(safe_name)
    stem = path.stem or "document"
    target_ext = f".{target_format.lower().lstrip('.')}"
    return f"{stem}{target_ext}"


def detect_file_format(filename: str, mime_type: str = "") -> str:
    """
    Detect format based on extension and optional mime type.
    Returns 'docx' or 'pdf'.
    Raises ValidationError if unsupported.
    """
    ext = Path(filename).suffix.lower()
    if ext == ".docx":
        return "docx"
    elif ext == ".pdf":
        return "pdf"
    
    # Try mime type fallback
    if mime_type == "application/pdf":
        return "pdf"
    elif (
        mime_type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ):
        return "docx"

    raise ValidationError(
        "Format file belum didukung.\n\nFormat yang tersedia:\n• DOCX → PDF\n• PDF → DOCX"
    )


def validate_file_size(file_size: int, max_bytes: int) -> None:
    """Validate that the file size is positive and within allowable limits."""
    if file_size <= 0:
        raise ValidationError("File dokumen kosong (0 bytes).")
    if file_size > max_bytes:
        max_mb = max_bytes // (1024 * 1024)
        raise ValidationError(
            f"Ukuran file melebihi batas yang diperbolehkan (maksimal {max_mb} MB)."
        )


def validate_pdf_content(file_path: Path) -> None:
    """Validate PDF file header, structure, and integrity."""
    if not file_path.exists():
        raise ValidationError("File PDF tidak ditemukan.")

    if file_path.stat().st_size == 0:
        raise ValidationError("File PDF kosong.")

    # Magic bytes check
    with open(file_path, "rb") as f:
        header = f.read(1024)
        if b"%PDF-" not in header:
            raise ValidationError("File bukan dokumen PDF yang valid (magic bytes mismatch).")

    # PyMuPDF verification
    try:
        doc = fitz.open(str(file_path))
        page_count = len(doc)
        doc.close()
        if page_count < 1:
            raise ValidationError("Dokumen PDF tidak memiliki halaman valid.")
    except Exception as e:
        raise ValidationError(f"Dokumen PDF rusak atau terproteksi password: {str(e)}")


def validate_docx_content(file_path: Path) -> None:
    """Validate DOCX file structure, ZIP container, Content_Types, and check against zip bombs."""
    if not file_path.exists():
        raise ValidationError("File DOCX tidak ditemukan.")

    if file_path.stat().st_size == 0:
        raise ValidationError("File DOCX kosong.")

    # Magic bytes check for ZIP (PK\x03\x04)
    with open(file_path, "rb") as f:
        header = f.read(4)
        if header != b"PK\x03\x04":
            raise ValidationError("File bukan format DOCX yang valid (ZIP header mismatch).")

    # Validate ZIP container and OOXML parts
    try:
        with zipfile.ZipFile(file_path, "r") as zf:
            namelist = zf.namelist()
            if "[Content_Types].xml" not in namelist:
                raise ValidationError("Dokumen DOCX tidak valid (Content_Types.xml hilang).")

            # Check for document structure (word/document.xml)
            if not any(name.startswith("word/") for name in namelist):
                raise ValidationError("File bukan dokumen Word (.docx) yang valid.")

            # Decompression bomb inspection
            total_uncompressed = sum(info.file_size for info in zf.infolist())
            compressed_size = file_path.stat().st_size
            if total_uncompressed > MAX_UNCOMPRESSED_DOCX_BYTES:
                raise ValidationError("Dokumen ditolak: ukuran setelah dekompresi melebihi batas aman.")
            if compressed_size > 0 and (total_uncompressed / compressed_size) > MAX_COMPRESSION_RATIO:
                raise ValidationError("Dokumen ditolak: rasio kompresi mencurigakan (potensi zip bomb).")

            # Test zip integrity
            bad_file = zf.testzip()
            if bad_file:
                raise ValidationError(f"File DOCX korup pada bagian {bad_file}.")
    except zipfile.BadZipFile:
        raise ValidationError("File DOCX korup atau tidak dapat dibaca.")
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Validasi DOCX gagal: {str(e)}")


def validate_input_document(file_path: Path, format_type: str, max_bytes: int) -> None:
    """Full validation of the incoming input document file."""
    validate_file_size(file_path.stat().st_size, max_bytes)
    if format_type == "pdf":
        validate_pdf_content(file_path)
    elif format_type == "docx":
        validate_docx_content(file_path)
    else:
        raise ValidationError(f"Format {format_type} tidak dikenali.")


def validate_output_document(file_path: Path, format_type: str) -> None:
    """Validate that the conversion produced a valid non-empty document."""
    if not file_path.exists():
        raise ValidationError(f"File output hasil konversi tidak terbentuk.")
    if file_path.stat().st_size == 0:
        raise ValidationError(f"File output hasil konversi kosong (0 bytes).")

    if format_type == "pdf":
        validate_pdf_content(file_path)
    elif format_type == "docx":
        validate_docx_content(file_path)
