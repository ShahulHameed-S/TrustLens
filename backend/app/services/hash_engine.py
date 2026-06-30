import hashlib
import logging
import os
from pathlib import Path
from typing import Union
from datetime import datetime, timezone

from app.schemas.hash_result import HashResult

logger = logging.getLogger(__name__)

class HashEngineError(Exception):
    """Base exception for HashEngine errors."""
    pass

class InvalidFilePathError(HashEngineError):
    """Raised when the file path is invalid, unauthorized, or contains traversal characters."""
    pass

class FileProcessingError(HashEngineError):
    """Raised when there is an issue reading or processing the file."""
    pass

class HashEngine:
    """
    Independent Hash Engine for calculating and verifying deterministic
    cryptographic fingerprints (SHA-256) of digital assets.
    """
    
    CHUNK_SIZE = 65536  # 64 KB chunks for memory efficiency
    ALGORITHM = "SHA-256"

    @classmethod
    def _validate_path(cls, file_path: Union[str, Path]) -> Path:
        """
        Validates the file path to prevent path traversal and ensure the file exists.
        Never exposes internal filesystem information in exceptions.
        """
        try:
            path = Path(file_path)
            
            # Prevent path traversal by checking for parent directory references
            if ".." in path.parts:
                raise InvalidFilePathError("Invalid file path: path traversal detected.")
                
            resolved_path = path.resolve()
            
            if not resolved_path.exists():
                raise InvalidFilePathError("Invalid file path: file does not exist.")
                
            if not resolved_path.is_file():
                raise InvalidFilePathError("Invalid file path: path is a directory or not a standard file.")
                
            return resolved_path
        except (TypeError, ValueError) as e:
            raise InvalidFilePathError("Invalid file path provided.") from None
        except OSError as e:
            # Catch OS errors (like permission denied) without exposing the actual path
            raise FileProcessingError("Error accessing the file.") from None

    @classmethod
    def calculate_sha256(cls, file_path: Union[str, Path]) -> HashResult:
        """
        Calculates the SHA-256 hash of a file deterministically.
        Streams the file in chunks to support files larger than RAM.
        """
        logger.info("Hash started")
        
        try:
            valid_path = cls._validate_path(file_path)
            
            sha256_hash = hashlib.sha256()
            size_bytes = 0
            
            with open(valid_path, "rb") as f:
                for chunk in iter(lambda: f.read(cls.CHUNK_SIZE), b""):
                    sha256_hash.update(chunk)
                    size_bytes += len(chunk)
                    
            hex_digest = sha256_hash.hexdigest().lower()
            
            result = HashResult(
                algorithm=cls.ALGORITHM,
                hash=hex_digest,
                size_bytes=size_bytes,
                generated_at=datetime.now(timezone.utc)
            )
            
            logger.info("Hash completed")
            return result
            
        except HashEngineError:
            logger.error("Hash failed")
            raise
        except Exception as e:
            logger.error("Hash failed")
            raise FileProcessingError("An unexpected error occurred during hashing.") from None

    @classmethod
    def verify_hash(cls, file_path: Union[str, Path], expected_hash: str) -> bool:
        """
        Verifies if the file at file_path produces the expected_hash.
        """
        try:
            result = cls.calculate_sha256(file_path)
            return cls.compare_hashes(result.hash, expected_hash)
        except HashEngineError:
            return False

    @classmethod
    def compare_hashes(cls, hash1: str, hash2: str) -> bool:
        """
        Compares two hashes in a time-constant manner to prevent timing attacks.
        Both hashes are converted to lowercase before comparison.
        """
        if not hash1 or not hash2:
            return False
        import hmac
        return hmac.compare_digest(hash1.lower(), hash2.lower())
