import concurrent.futures
import logging
from pathlib import Path
from typing import Optional
from pdf2docx import Converter
from app.config.settings import settings
from app.conversion.docx_to_pdf import ConversionError
from app.conversion.validator import ValidationError, validate_output_document

logger = logging.getLogger(__name__)


def _run_pdf2docx_conversion(input_path: str, output_path: str) -> None:
    """Synchronous worker function to convert PDF to DOCX using pdf2docx."""
    cv = Converter(input_path)
    try:
        cv.convert(output_path, start=0, end=None)
    finally:
        cv.close()


def convert_pdf_to_docx(
    input_file: Path,
    output_file: Path,
    timeout_seconds: Optional[int] = None,
) -> Path:
    """
    Convert PDF document to DOCX using pdf2docx.
    Enforces timeout, resource cleanup, and output validation.
    """
    timeout = timeout_seconds or settings.JOB_TIMEOUT_SECONDS
    output_dir = output_file.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Converting PDF to DOCX: {input_file} -> {output_file}")

    try:
        # Run conversion in a separate thread to strictly enforce the timeout
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                _run_pdf2docx_conversion, str(input_file), str(output_file)
            )
            try:
                future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                logger.error(f"pdf2docx conversion timed out after {timeout} seconds.")
                raise ConversionError(
                    f"Waktu konversi habis (melebihi batas {timeout} detik). "
                    "Dokumen PDF kemungkinan terlalu besar atau kompleks."
                )

        # Validate generated DOCX container
        validate_output_document(output_file, "docx")
        logger.info(f"Successfully converted PDF to DOCX: {output_file}")
        return output_file

    except ConversionError:
        raise
    except ValidationError as ve:
        logger.error(f"Validation error for converted DOCX {output_file}: {ve}")
        raise ConversionError(f"Hasil konversi tidak valid: {str(ve)}")
    except Exception as e:
        logger.exception(f"Unexpected error in convert_pdf_to_docx: {e}")
        raise ConversionError(
            f"Gagal mengonversi PDF ke DOCX. Pastikan file PDF tidak terenkripsi atau rusak ({str(e)})."
        )
