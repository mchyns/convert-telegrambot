import tempfile
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from app.conversion.docx_to_pdf import (
    ConversionError,
    convert_docx_to_pdf,
    find_libreoffice_binary,
)


def test_find_libreoffice_binary_fallback():
    # When binary is not found, returns None or configured path
    with patch("app.conversion.docx_to_pdf.settings.LIBREOFFICE_PATH", None):
        with patch("shutil.which", return_value=None):
            with patch("pathlib.Path.exists", return_value=False):
                assert find_libreoffice_binary() is None


def test_convert_docx_to_pdf_missing_binary():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_docx = Path(tmpdir) / "test.docx"
        output_pdf = Path(tmpdir) / "test.pdf"
        input_docx.write_text("dummy")

        with patch("sys.platform", "linux"):
            with patch("app.conversion.docx_to_pdf.find_libreoffice_binary", return_value=None):
                with pytest.raises(ConversionError) as exc_info:
                    convert_docx_to_pdf(input_docx, output_pdf)
                assert "LibreOffice tidak ditemukan" in str(exc_info.value)


def test_convert_docx_to_pdf_mock_subprocess():
    with tempfile.TemporaryDirectory() as tmpdir:
        input_docx = Path(tmpdir) / "test.docx"
        output_pdf = Path(tmpdir) / "test.pdf"
        input_docx.write_text("dummy")

        def fake_subprocess_run(cmd, **kwargs):
            # Simulate LibreOffice creating a valid PDF
            outdir = Path(cmd[cmd.index("--outdir") + 1])
            pdf_path = outdir / f"{input_docx.stem}.pdf"
            # Write valid minimal PDF
            pdf_path.write_bytes(b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n")
            mock = MagicMock()
            mock.returncode = 0
            return mock

        with patch("app.conversion.docx_to_pdf.find_libreoffice_binary", return_value="/usr/bin/libreoffice"):
            with patch("subprocess.run", side_effect=fake_subprocess_run):
                with patch("app.conversion.docx_to_pdf.validate_output_document") as mock_val:
                    res = convert_docx_to_pdf(input_docx, output_pdf)
                    assert res == output_pdf
                    assert output_pdf.exists()
                    mock_val.assert_called_once()
