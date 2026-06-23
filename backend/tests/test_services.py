import os
import tempfile
import pytest

from app.services.document_processor import extract_text, chunk_text


class TestDocumentProcessor:
    def test_extract_txt(self):
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False)
        try:
            tmp.write("Hello, this is a test document.")
            tmp.close()
            text = extract_text(tmp.name, "txt")
            assert text == "Hello, this is a test document."
        finally:
            os.unlink(tmp.name)

    def test_chunk_text(self):
        text = "word " * 2000
        chunks = chunk_text(text, chunk_size=500, overlap=50)
        assert len(chunks) > 1
        for c in chunks:
            assert "content" in c
            assert "chunk_index" in c
            assert "token_count" in c

    def test_chunk_single(self):
        text = "Short text."
        chunks = chunk_text(text, chunk_size=500, overlap=50)
        assert len(chunks) == 1
        assert chunks[0]["chunk_index"] == 0

    def test_extract_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            extract_text(r"C:\nonexistent_file_path.txt", "txt")

    def test_extract_unsupported_type(self):
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".xyz", delete=False)
        try:
            tmp.write("dummy")
            tmp.close()
            with pytest.raises(ValueError, match="Unsupported file type"):
                extract_text(tmp.name, "xyz")
        finally:
            os.unlink(tmp.name)
