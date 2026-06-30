import logging
import pathlib
import mimetypes
from datetime import datetime
from typing import Optional, Dict, Any

from app.schemas.metadata import MetadataResult, AssetType

logger = logging.getLogger(__name__)

class MetadataEngineError(Exception):
    pass

def _get_asset_type_from_mime(mime_type: str) -> AssetType:
    if not mime_type:
        return AssetType.UNKNOWN
    if mime_type == "application/pdf":
        return AssetType.PDF
    if mime_type.startswith("image/"):
        return AssetType.IMAGE
    if mime_type.startswith("audio/"):
        return AssetType.AUDIO
    return AssetType.UNKNOWN

def extract_pdf_metadata(file_path: str) -> tuple[Dict[str, Any], list[str]]:
    metadata = {}
    warnings = []
    try:
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(file_path)
            metadata['page_count'] = doc.page_count
            metadata['encrypted'] = doc.is_encrypted
            doc_metadata = doc.metadata or {}
            metadata['title'] = doc_metadata.get('title')
            metadata['author'] = doc_metadata.get('author')
            metadata['creator'] = doc_metadata.get('creator')
            metadata['producer'] = doc_metadata.get('producer')
            metadata['creation_date'] = doc_metadata.get('creationDate')
            metadata['modification_date'] = doc_metadata.get('modDate')
            doc.close()
        except ImportError:
            try:
                import pypdf
                with open(file_path, "rb") as f:
                    reader = pypdf.PdfReader(f)
                    metadata['page_count'] = len(reader.pages)
                    metadata['encrypted'] = reader.is_encrypted
                    doc_metadata = reader.metadata or {}
                    metadata['title'] = getattr(doc_metadata, 'title', None)
                    metadata['author'] = getattr(doc_metadata, 'author', None)
                    metadata['creator'] = getattr(doc_metadata, 'creator', None)
                    metadata['producer'] = getattr(doc_metadata, 'producer', None)
                    metadata['creation_date'] = getattr(doc_metadata, 'creation_date', None)
                    metadata['modification_date'] = getattr(doc_metadata, 'modification_date', None)
            except ImportError:
                warnings.append("PyMuPDF or pypdf not available for PDF metadata extraction")
    except Exception as e:
        warnings.append(f"Failed to extract PDF metadata: {str(e)}")
    
    clean_metadata = {k: v for k, v in metadata.items() if v is not None}
    return clean_metadata, warnings

def extract_image_metadata(file_path: str) -> tuple[Dict[str, Any], list[str]]:
    metadata = {}
    warnings = []
    try:
        from PIL import Image
        with Image.open(file_path) as img:
            metadata['width'] = img.width
            metadata['height'] = img.height
            metadata['format'] = img.format
            metadata['mode'] = img.mode
            
            exif_available = False
            if hasattr(img, '_getexif') and img._getexif():
                exif_available = True
            elif hasattr(img, 'getexif') and img.getexif():
                exif_available = True
                
            metadata['exif_available'] = exif_available
    except ImportError:
        warnings.append("Pillow not available for image metadata extraction")
    except Exception as e:
        warnings.append(f"Failed to extract image metadata: {str(e)}")
    return metadata, warnings

def extract_audio_metadata(file_path: str) -> tuple[Dict[str, Any], list[str]]:
    metadata = {}
    warnings = []
    try:
        try:
            import librosa
            import soundfile as sf
            
            info = sf.info(file_path)
            metadata['duration_seconds'] = info.duration
            metadata['sample_rate'] = info.samplerate
            metadata['channels'] = info.channels
            metadata['format'] = info.format
        except ImportError:
            try:
                import wave
                with wave.open(file_path, 'rb') as wav_file:
                    metadata['channels'] = wav_file.getnchannels()
                    metadata['sample_rate'] = wav_file.getframerate()
                    frames = wav_file.getnframes()
                    metadata['duration_seconds'] = frames / float(metadata['sample_rate'])
                    metadata['format'] = 'WAV'
            except ImportError:
                warnings.append("wave library missing, though it should be built-in")
            except Exception as e:
                warnings.append(f"Failed to extract audio metadata using wave: {str(e)}")
    except Exception as e:
        warnings.append(f"Failed to extract audio metadata: {str(e)}")
        
    return metadata, warnings

def extract_metadata(file_path: str, asset_type: Optional[str] = None, original_filename: Optional[str] = None) -> MetadataResult:
    logger.info("Metadata extraction started")
    warnings = []
    
    if '..' in str(file_path):
        logger.error("Metadata extraction failed: Path traversal detected")
        raise MetadataEngineError("Path traversal detected")
        
    path = pathlib.Path(file_path)
    
    if not path.exists():
        logger.error("Metadata extraction failed: File does not exist")
        raise MetadataEngineError("File does not exist")
        
    if path.is_dir():
        logger.error("Metadata extraction failed: Path is a directory")
        raise MetadataEngineError("Path is a directory")
        
    resolved_path = path.resolve()

    filename = original_filename or path.name
    extension = path.suffix.lower()
    
    mime_type, _ = mimetypes.guess_type(filename)
    if mime_type is None:
        mime_type = "application/octet-stream"
        
    detected_asset_type = _get_asset_type_from_mime(mime_type)
    if asset_type:
        try:
            detected_asset_type = AssetType(asset_type)
        except ValueError:
            pass
            
    size_bytes = path.stat().st_size
    
    basic_metadata = {}
    technical_metadata = {}
    
    if detected_asset_type == AssetType.PDF:
        technical_metadata, pdf_warnings = extract_pdf_metadata(str(resolved_path))
        warnings.extend(pdf_warnings)
    elif detected_asset_type == AssetType.IMAGE:
        technical_metadata, image_warnings = extract_image_metadata(str(resolved_path))
        warnings.extend(image_warnings)
    elif detected_asset_type == AssetType.AUDIO:
        technical_metadata, audio_warnings = extract_audio_metadata(str(resolved_path))
        warnings.extend(audio_warnings)
    elif detected_asset_type == AssetType.UNKNOWN:
        warnings.append(f"Unsupported asset type for advanced metadata extraction (mime_type: {mime_type})")
        logger.warning(f"Metadata extraction warning: Unsupported asset type {mime_type}")
    
    if warnings:
        for w in warnings:
            logger.warning(f"Metadata extraction warning: {w}")
            
    logger.info("Metadata extraction completed")
    
    return MetadataResult(
        asset_type=detected_asset_type,
        filename=filename,
        extension=extension,
        mime_type=mime_type,
        size_bytes=size_bytes,
        extracted_at=datetime.utcnow(),
        basic_metadata=basic_metadata,
        technical_metadata=technical_metadata,
        warnings=warnings
    )
