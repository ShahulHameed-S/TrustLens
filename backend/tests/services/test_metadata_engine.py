import os
import pytest
from datetime import datetime

from app.services.metadata_engine import extract_metadata, MetadataEngineError
from app.schemas.metadata import AssetType

@pytest.fixture
def temp_files(tmp_path):
    files = {}
    
    # 1. Create a dummy text file (Unsupported)
    txt_path = tmp_path / "test.txt"
    txt_path.write_text("Hello World")
    files['txt'] = txt_path
    
    # 2. Create a dummy image file using Pillow if available
    img_path = tmp_path / "test.png"
    try:
        from PIL import Image
        img = Image.new('RGB', (100, 50), color='red')
        img.save(img_path)
    except ImportError:
        # Create a dummy fake image file
        img_path.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x64\x00\x00\x00\x32\x08\x02\x00\x00\x00")
    files['img'] = img_path
    
    # 3. Create a dummy audio file using wave
    import wave
    wav_path = tmp_path / "test.wav"
    with wave.open(str(wav_path), 'wb') as wav_file:
        wav_file.setnchannels(2)
        wav_file.setsampwidth(2)
        wav_file.setframerate(44100)
        # write 1 second of empty frames
        wav_file.writeframes(b'\x00' * (44100 * 2 * 2))
    files['wav'] = wav_path
    
    # 4. Create a dummy PDF using PyMuPDF or pypdf if available
    pdf_path = tmp_path / "test.pdf"
    try:
        import fitz
        doc = fitz.open()
        doc.new_page()
        doc.set_metadata({"title": "Test Title", "author": "Test Author"})
        doc.save(str(pdf_path))
        doc.close()
    except ImportError:
        try:
            import pypdf
            writer = pypdf.PdfWriter()
            writer.add_blank_page(width=100, height=100)
            writer.add_metadata({"/Title": "Test Title", "/Author": "Test Author"})
            with open(str(pdf_path), "wb") as f:
                writer.write(f)
        except ImportError:
            # Fallback: create empty file, metadata extraction will fail gracefully
            pdf_path.write_bytes(b"%PDF-1.4\n%EOF\n")
            
    files['pdf'] = pdf_path
    
    return files

def test_missing_file():
    with pytest.raises(MetadataEngineError, match="File does not exist"):
        extract_metadata("non_existent_file.pdf")

def test_directory_rejection(tmp_path):
    with pytest.raises(MetadataEngineError, match="Path is a directory"):
        extract_metadata(str(tmp_path))

def test_path_traversal(temp_files):
    with pytest.raises(MetadataEngineError, match="Path traversal detected"):
        extract_metadata(f"../{temp_files['txt'].name}")

def test_unsupported_asset_type(temp_files):
    result = extract_metadata(str(temp_files['txt']))
    assert result.asset_type == AssetType.UNKNOWN
    assert result.mime_type == "text/plain"
    assert any("Unsupported asset type" in w for w in result.warnings)
    assert result.filename == "test.txt"

def test_image_metadata(temp_files):
    result = extract_metadata(str(temp_files['img']))
    assert result.asset_type == AssetType.IMAGE
    assert result.mime_type == "image/png"
    if 'width' in result.technical_metadata:
        assert result.technical_metadata['width'] == 100
        assert result.technical_metadata['height'] == 50
        assert result.technical_metadata['format'] == 'PNG'
        assert 'exif_available' in result.technical_metadata
    else:
        assert any("Pillow not available" in w for w in result.warnings)

def test_audio_metadata(temp_files):
    result = extract_metadata(str(temp_files['wav']))
    assert result.asset_type == AssetType.AUDIO
    assert result.mime_type == "audio/wav"
    assert result.technical_metadata['channels'] == 2
    assert result.technical_metadata['sample_rate'] == 44100
    assert result.technical_metadata['duration_seconds'] == 1.0

def test_pdf_metadata(temp_files):
    result = extract_metadata(str(temp_files['pdf']))
    assert result.asset_type == AssetType.PDF
    assert result.mime_type == "application/pdf"
    
    # Validation if a PDF was successfully read
    if 'page_count' in result.technical_metadata:
        assert result.technical_metadata['page_count'] == 1

def test_graceful_fallback(tmp_path):
    # A corrupted image file will trigger the Pillow Exception fallback
    bad_img = tmp_path / "bad.png"
    bad_img.write_bytes(b"not an image")
    
    result = extract_metadata(str(bad_img))
    assert result.asset_type == AssetType.IMAGE
    assert len(result.technical_metadata) == 0
    assert len(result.warnings) > 0
    assert any("Failed to extract image metadata" in w or "Pillow not available" in w for w in result.warnings)
