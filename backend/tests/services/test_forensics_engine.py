import os
import pytest
from datetime import datetime
from app.services.forensics_engine import analyze_file, ForensicsEngineError
from app.schemas.metadata import AssetType

@pytest.fixture
def temp_files(tmp_path):
    files = {}
    
    txt_path = tmp_path / "test.txt"
    txt_path.write_text("Hello World")
    files['txt'] = txt_path
    
    img_path = tmp_path / "test.png"
    try:
        from PIL import Image
        img = Image.new('RGB', (100, 50), color='red')
        img.save(img_path)
    except ImportError:
        img_path.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x64\x00\x00\x00\x32\x08\x02\x00\x00\x00")
    files['img'] = img_path
    
    import wave
    wav_path = tmp_path / "test.wav"
    with wave.open(str(wav_path), 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(44100)
        wav_file.writeframes(b'\x00' * (44100 * 2))
    files['wav'] = wav_path
    
    pdf_path = tmp_path / "test.pdf"
    try:
        import pypdf
        writer = pypdf.PdfWriter()
        writer.add_blank_page(width=100, height=100)
        writer.add_metadata({"/Title": "Test Title"})
        with open(str(pdf_path), "wb") as f:
            writer.write(f)
    except ImportError:
        pdf_path.write_bytes(b"%PDF-1.4\n%EOF\n")
            
    files['pdf'] = pdf_path
    
    # A corrupted file
    bad_img = tmp_path / "bad.png"
    bad_img.write_bytes(b"not an image")
    files['bad'] = bad_img

    return files

def test_missing_file():
    with pytest.raises(ForensicsEngineError, match="File does not exist"):
        analyze_file("non_existent_file.pdf", "PDF")

def test_directory_rejection(tmp_path):
    with pytest.raises(ForensicsEngineError, match="Path is a directory"):
        analyze_file(str(tmp_path), "PDF")

def test_path_traversal(temp_files):
    with pytest.raises(ForensicsEngineError, match="Path traversal detected"):
        analyze_file(f"../{temp_files['txt'].name}", "PDF")

def test_unsupported_asset_type(temp_files):
    result = analyze_file(str(temp_files['txt']), "UNKNOWN")
    assert result.asset_type == AssetType.UNKNOWN
    assert result.forensic_score == 100.0
    assert result.confidence == 0.0
    assert any("Unsupported asset type" in w for w in result.warnings)

def test_image_forensics(temp_files):
    result = analyze_file(str(temp_files['img']), "IMAGE")
    assert result.asset_type == AssetType.IMAGE
    assert isinstance(result.tampering_detected, bool)
    assert 0 <= result.forensic_score <= 100
    assert 0 <= result.confidence <= 100
    # In my dummy PIL image without EXIF, if format is PNG, score won't drop, if JPEG/TIFF it drops. 
    # For PNG it stays 100 unless Pillow is missing.
    
def test_audio_forensics(temp_files):
    result = analyze_file(str(temp_files['wav']), "AUDIO")
    assert result.asset_type == AssetType.AUDIO
    assert isinstance(result.tampering_detected, bool)
    assert 0 <= result.forensic_score <= 100

def test_pdf_forensics(temp_files):
    result = analyze_file(str(temp_files['pdf']), "PDF")
    assert result.asset_type == AssetType.PDF
    assert isinstance(result.tampering_detected, bool)
    assert 0 <= result.forensic_score <= 100

def test_graceful_fallback(temp_files):
    result = analyze_file(str(temp_files['bad']), "IMAGE")
    assert result.asset_type == AssetType.IMAGE
    assert len(result.raw_signals) == 0
    assert result.confidence == 0.0
    assert any("Failed to deeply analyze" in w or "skipped" in w.lower() or "Pillow not available" in w for w in result.warnings)
