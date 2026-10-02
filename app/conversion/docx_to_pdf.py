import logging
import os
import shutil
import subprocess
from pathlib import Path
from typing import Optional
from app.config.settings import settings
from app.conversion.validator import ValidationError, validate_output_document

import sys

logger = logging.getLogger(__name__)


class ConversionError(Exception):
    """Exception raised when a conversion pipeline fails."""
    pass


def _convert_via_docx2pdf(input_file: Path, output_file: Path) -> Path:
    """Fallback conversion on Windows using Microsoft Word via docx2pdf."""
    import docx2pdf
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except Exception:
        pass

    try:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        docx2pdf.convert(str(input_file), str(output_file))
        validate_output_document(output_file, "pdf")
        return output_file
    finally:
        try:
            import pythoncom
            pythoncom.CoUninitialize()
        except Exception:
            pass


def find_libreoffice_binary() -> Optional[str]:
    """Find LibreOffice or soffice executable path across operating systems."""
    if settings.LIBREOFFICE_PATH and Path(settings.LIBREOFFICE_PATH).exists():
        return settings.LIBREOFFICE_PATH

    # Check PATH
    for cmd in ["libreoffice", "soffice"]:
        found = shutil.which(cmd)
        if found:
            return found

    # Standard Windows install locations
    windows_candidates = [
        r"C:\Program Files\LibreOffice\program\soffice.exe",
        r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
        r"C:\Program Files\LibreOffice 24\program\soffice.exe",
        r"C:\Program Files\LibreOffice 7\program\soffice.exe",
    ]
    for candidate in windows_candidates:
        if Path(candidate).exists():
            return candidate

    # Standard Linux / Docker locations
    linux_candidates = [
        "/usr/bin/libreoffice",
        "/usr/bin/soffice",
        "/usr/local/bin/libreoffice",
        "/usr/local/bin/soffice",
    ]
    for candidate in linux_candidates:
        if Path(candidate).exists():
            return candidate

    return None


def convert_docx_to_pdf(
    input_file: Path,
    output_file: Path,
    timeout_seconds: Optional[int] = None,
) -> Path:
    """
    Convert DOCX document to PDF using LibreOffice headless.
    Ensures safe subprocess execution, timeout enforcement, and output validation.
    """
    timeout = timeout_seconds or settings.JOB_TIMEOUT_SECONDS
    libreoffice_bin = find_libreoffice_binary()

    if not libreoffice_bin:
        # On Windows, try native Microsoft Word via docx2pdf
        if sys.platform == "win32":
            try:
                logger.info(
                    f"LibreOffice not found; converting DOCX to PDF using Microsoft Word (docx2pdf) for {input_file}"
                )
                return _convert_via_docx2pdf(input_file, output_file)
            except Exception as e:
                logger.error(f"docx2pdf conversion error: {e}")
                raise ConversionError(
                    f"Konversi DOCX ke PDF via Word gagal: {str(e)}"
                )

        raise ConversionError(
            "LibreOffice tidak ditemukan di server. Pastikan LibreOffice terinstal "
            "atau jalankan menggunakan Docker Compose sesuai PRD."
        )

    output_dir = output_file.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Temporary environment to avoid LibreOffice user-profile locking issues in multi-worker
    env = os.environ.copy()
    user_profile_dir = output_dir / ".libreoffice_profile"
    user_profile_dir.mkdir(parents=True, exist_ok=True)
    env["UserInstallation"] = f"file:///{str(user_profile_dir).replace('\\', '/')}"

    cmd = [
        libreoffice_bin,
        "--headless",
        "--invisible",
        "--nodefault",
        "--nofirststartwizard",
        "--nolockcheck",
        "--nologo",
        "--convert-to",
        "pdf",
        "--outdir",
        str(output_dir),
        str(input_file),
    ]

    logger.info(f"Running LibreOffice conversion: {' '.join(cmd)}")

    try:
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
            env=env,
        )

        if process.returncode != 0:
            stderr = process.stderr.decode("utf-8", errors="replace")
            stdout = process.stdout.decode("utf-8", errors="replace")
            logger.error(
                f"LibreOffice exited with code {process.returncode}. stdout: {stdout}, stderr: {stderr}"
            )
            raise ConversionError(f"Gagal melakukan konversi DOCX ke PDF (kode: {process.returncode}).")

        # LibreOffice generates output named <input_file.stem>.pdf in output_dir
        expected_lo_output = output_dir / f"{input_file.stem}.pdf"
        if not expected_lo_output.exists():
            # Check if any .pdf file was generated in output_dir
            pdf_files = list(output_dir.glob("*.pdf"))
            if pdf_files:
                expected_lo_output = pdf_files[0]
            else:
                raise ConversionError("File PDF tidak terbentuk setelah konversi.")

        # Rename to final requested output filename if different
        if expected_lo_output.resolve() != output_file.resolve():
            if output_file.exists():
                output_file.unlink()
            expected_lo_output.rename(output_file)

        # Clean up temporary user profile dir
        if user_profile_dir.exists():
            shutil.rmtree(user_profile_dir, ignore_errors=True)

        # Validate the resulting output PDF
        validate_output_document(output_file, "pdf")
        logger.info(f"Successfully converted DOCX to PDF: {output_file}")
        return output_file

    except subprocess.TimeoutExpired:
        logger.error(f"Conversion timed out after {timeout} seconds for {input_file}")
        raise ConversionError(f"Waktu konversi habis (melebihi batas {timeout} detik).")
    except ValidationError as ve:
        logger.error(f"Validation error for converted PDF {output_file}: {ve}")
        raise ConversionError(f"Hasil konversi tidak valid: {str(ve)}")
    except Exception as e:
        if isinstance(e, ConversionError):
            raise
        logger.exception(f"Unexpected error in convert_docx_to_pdf: {e}")
        raise ConversionError(f"Terjadi kesalahan saat mengonversi dokumen: {str(e)}")
