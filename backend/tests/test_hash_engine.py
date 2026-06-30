import os
import pytest
from pathlib import Path
from app.services.hash_engine import HashEngine, InvalidFilePathError

@pytest.fixture
def test_files(tmp_path):
    """
    Fixture to create various test files mimicking different file types and scenarios.
    Returns a dictionary of file paths.
    """
    files = {}

    # 1. Small PDF
    small_pdf = tmp_path / "small.pdf"
    small_pdf.write_bytes(b"%PDF-1.4\n%...\n%%EOF")
    files["small_pdf"] = small_pdf

    # 2. Large PDF (e.g., slightly larger than chunk size to test chunking, ~100KB)
    large_pdf = tmp_path / "large.pdf"
    large_pdf.write_bytes(b"%PDF-1.4\n" + b"A" * 100000 + b"\n%%EOF")
    files["large_pdf"] = large_pdf

    # 3. Image
    image_file = tmp_path / "image.png"
    image_file.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR...")
    files["image"] = image_file

    # 4. Audio
    audio_file = tmp_path / "audio.mp3"
    audio_file.write_bytes(b"ID3\x04\x00\x00\x00\x00\x00\x23...")
    files["audio"] = audio_file

    # 5. Empty file
    empty_file = tmp_path / "empty.txt"
    empty_file.write_bytes(b"")
    files["empty_file"] = empty_file

    # 6. Duplicate file (exact copy of small_pdf)
    duplicate_file = tmp_path / "duplicate.pdf"
    duplicate_file.write_bytes(small_pdf.read_bytes())
    files["duplicate"] = duplicate_file

    # 7. Modified file (almost same as small_pdf but slightly changed)
    modified_file = tmp_path / "modified.pdf"
    modified_file.write_bytes(b"%PDF-1.4\n%...\n%%EOF_modified")
    files["modified"] = modified_file

    # 8. Directory (to test directory rejection)
    test_dir = tmp_path / "test_directory"
    test_dir.mkdir()
    files["directory"] = test_dir
    
    return files


def test_hash_small_pdf(test_files):
    result = HashEngine.calculate_sha256(test_files["small_pdf"])
    assert result.algorithm == "SHA-256"
    assert result.size_bytes == len(b"%PDF-1.4\n%...\n%%EOF")
    assert isinstance(result.hash, str)
    assert len(result.hash) == 64
    assert result.hash.islower()


def test_hash_large_pdf_chunking(test_files):
    result = HashEngine.calculate_sha256(test_files["large_pdf"])
    expected_size = len(b"%PDF-1.4\n" + b"A" * 100000 + b"\n%%EOF")
    assert result.size_bytes == expected_size
    assert len(result.hash) == 64


def test_hash_image_and_audio(test_files):
    img_result = HashEngine.calculate_sha256(test_files["image"])
    audio_result = HashEngine.calculate_sha256(test_files["audio"])
    assert len(img_result.hash) == 64
    assert len(audio_result.hash) == 64
    assert img_result.hash != audio_result.hash


def test_hash_empty_file(test_files):
    result = HashEngine.calculate_sha256(test_files["empty_file"])
    assert result.size_bytes == 0
    # The SHA-256 hash of an empty string
    assert result.hash == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_hash_duplicate_file(test_files):
    result1 = HashEngine.calculate_sha256(test_files["small_pdf"])
    result2 = HashEngine.calculate_sha256(test_files["duplicate"])
    assert result1.hash == result2.hash
    assert result1.size_bytes == result2.size_bytes


def test_hash_modified_file(test_files):
    result_original = HashEngine.calculate_sha256(test_files["small_pdf"])
    result_modified = HashEngine.calculate_sha256(test_files["modified"])
    assert result_original.hash != result_modified.hash


def test_hash_verification(test_files):
    result = HashEngine.calculate_sha256(test_files["small_pdf"])
    
    # Verify with correct hash
    assert HashEngine.verify_hash(test_files["small_pdf"], result.hash) is True
    
    # Verify with incorrect hash
    assert HashEngine.verify_hash(test_files["small_pdf"], "0" * 64) is False


def test_hash_comparison():
    hash1 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    hash2 = "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855"
    hash3 = "a" * 64
    
    # Should be true as comparison is case-insensitive
    assert HashEngine.compare_hashes(hash1, hash2) is True
    assert HashEngine.compare_hashes(hash1, hash3) is False
    assert HashEngine.compare_hashes(hash1, "") is False
    assert HashEngine.compare_hashes("", hash2) is False


def test_missing_file():
    with pytest.raises(InvalidFilePathError):
        HashEngine.calculate_sha256("non_existent_file.txt")


def test_directory_rejection(test_files):
    with pytest.raises(InvalidFilePathError):
        HashEngine.calculate_sha256(test_files["directory"])


def test_path_traversal_rejection():
    with pytest.raises(InvalidFilePathError):
        HashEngine.calculate_sha256("../test.txt")
