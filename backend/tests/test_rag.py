import pytest
from unittest.mock import MagicMock, patch
from app.rag.parsers import parse_pdf, parse_docx, parse_text
from app.rag.chunking import chunk_fixed, chunk_recursive

def test_parse_text():
    raw_bytes = b"Hello, this is a test text file."
    res = parse_text(raw_bytes)
    assert res == "Hello, this is a test text file."

def test_parse_pdf():
    # Mock PyMuPDF / fitz
    mock_page = MagicMock()
    mock_page.get_text.return_value = "Page content from PDF"
    mock_doc = MagicMock()
    mock_doc.__iter__.return_value = [mock_page]
    
    with patch("fitz.open", return_value=mock_doc):
        res = parse_pdf(b"fake_pdf_data")
        assert "Page content from PDF" in res

def test_parse_docx():
    # Mock python-docx Document
    mock_p = MagicMock()
    mock_p.text = "Paragraph from Word doc"
    mock_doc = MagicMock()
    mock_doc.paragraphs = [mock_p]
    mock_doc.tables = []
    
    with patch("docx.Document", return_value=mock_doc):
        res = parse_docx(b"fake_docx_data")
        assert "Paragraph from Word doc" in res

def test_chunking_recursive():
    text = "Word. " * 500  # long text
    chunks = chunk_recursive(text, chunk_size=200, overlap=20)
    assert len(chunks) > 0
    assert all(len(c.text) <= 220 for c in chunks)  # simple size boundary check

def test_chunking_fixed():
    text = "Word. " * 500
    chunks = chunk_fixed(text, chunk_size=200, overlap=20)
    assert len(chunks) > 0
