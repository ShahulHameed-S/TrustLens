import logging
import pathlib
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple

from app.schemas.metadata import AssetType
from app.schemas.forensics import ForensicsResult

logger = logging.getLogger(__name__)

class ForensicsEngineError(Exception):
    pass

def analyze_pdf(file_path: str) -> Tuple[float, List[str], List[str], Dict[str, Any]]:
    score = 100.0
    findings = []
    warnings = []
    raw_signals = {}
    
    try:
        try:
            import fitz
            doc = fitz.open(file_path)
            raw_signals['page_count'] = doc.page_count
            raw_signals['encrypted'] = doc.is_encrypted
            
            if doc.is_encrypted:
                score -= 30.0
                findings.append("PDF is encrypted or password protected")
                
            doc_metadata = doc.metadata or {}
            
            if not doc_metadata:
                score -= 10.0
                findings.append("PDF metadata is missing entirely")
            else:
                raw_signals['metadata'] = doc_metadata
                creation_date = doc_metadata.get("creationDate")
                mod_date = doc_metadata.get("modDate")
                if creation_date and mod_date and creation_date != mod_date:
                    score -= 15.0
                    findings.append("Creation date and modification date differ")
                
                producer = doc_metadata.get("producer", "")
                if producer and any(suspicious in producer.lower() for suspicious in ["pdf24", "ilovepdf", "smallpdf"]):
                    score -= 20.0
                    findings.append(f"Suspicious producer identified: {producer}")
                    
            doc.close()
            
        except ImportError:
            try:
                import pypdf
                with open(file_path, "rb") as f:
                    reader = pypdf.PdfReader(f)
                    raw_signals['page_count'] = len(reader.pages)
                    raw_signals['encrypted'] = reader.is_encrypted
                    
                    if reader.is_encrypted:
                        score -= 30.0
                        findings.append("PDF is encrypted")
                        
                    doc_metadata = reader.metadata or {}
                    if not doc_metadata:
                        score -= 10.0
                        findings.append("PDF metadata is missing")
                    else:
                        creation_date = getattr(doc_metadata, 'creation_date', None)
                        mod_date = getattr(doc_metadata, 'modification_date', None)
                        if creation_date and mod_date and creation_date != mod_date:
                            score -= 15.0
                            findings.append("Creation and modification dates differ")
                            
            except ImportError:
                warnings.append("PyMuPDF or pypdf not available. Deep PDF forensics skipped.")
    except Exception as e:
        warnings.append(f"Failed to deeply analyze PDF: {str(e)}")
        
    return score, findings, warnings, raw_signals

def analyze_image(file_path: str) -> Tuple[float, List[str], List[str], Dict[str, Any]]:
    score = 100.0
    findings = []
    warnings = []
    raw_signals = {}
    
    try:
        from PIL import Image
        with Image.open(file_path) as img:
            raw_signals['width'] = img.width
            raw_signals['height'] = img.height
            raw_signals['format'] = img.format
            raw_signals['mode'] = img.mode
            
            exif_available = False
            if hasattr(img, '_getexif') and img._getexif():
                exif_available = True
            elif hasattr(img, 'getexif') and img.getexif():
                exif_available = True
                
            raw_signals['exif_available'] = exif_available
            if not exif_available and img.format in ['JPEG', 'TIFF']:
                score -= 10.0
                findings.append(f"Suspiciously missing EXIF data for {img.format} format")
                
            try:
                import imagehash
                phash = imagehash.phash(img)
                raw_signals['phash'] = str(phash)
            except ImportError:
                warnings.append("ImageHash not available. Perceptual hashing skipped.")
                
    except ImportError:
        warnings.append("Pillow not available. Deep image forensics skipped.")
    except Exception as e:
        warnings.append(f"Failed to deeply analyze Image: {str(e)}")
        
    return score, findings, warnings, raw_signals

def analyze_audio(file_path: str) -> Tuple[float, List[str], List[str], Dict[str, Any]]:
    score = 100.0
    findings = []
    warnings = []
    raw_signals = {}
    
    try:
        try:
            import soundfile as sf
            import numpy as np
            
            data, samplerate = sf.read(file_path)
            duration = len(data) / samplerate
            channels = data.shape[1] if len(data.shape) > 1 else 1
            
            raw_signals['duration_seconds'] = duration
            raw_signals['sample_rate'] = samplerate
            raw_signals['channels'] = channels
            
            # clipping indicator
            max_amp = np.max(np.abs(data))
            raw_signals['max_amplitude'] = float(max_amp)
            if max_amp >= 1.0:
                score -= 15.0
                findings.append("Audio clipping detected (max amplitude >= 1.0)")
                
            try:
                import librosa
                rms = librosa.feature.rms(y=data.T if channels == 1 else data.mean(axis=1))
                silence_ratio = np.sum(rms < 0.01) / rms.size
                raw_signals['silence_ratio'] = float(silence_ratio)
                
                if silence_ratio > 0.5:
                    score -= 10.0
                    findings.append("Unusually high ratio of silence detected")
            except ImportError:
                warnings.append("librosa not available for silence ratio analysis.")
                
        except ImportError:
            try:
                import wave
                with wave.open(file_path, 'rb') as wav_file:
                    raw_signals['channels'] = wav_file.getnchannels()
                    raw_signals['sample_rate'] = wav_file.getframerate()
                    frames = wav_file.getnframes()
                    duration = frames / float(raw_signals['sample_rate'])
                    raw_signals['duration_seconds'] = duration
            except ImportError:
                warnings.append("wave library missing for audio forensics.")
            except Exception as e:
                warnings.append(f"Failed to analyze audio with wave fallback: {str(e)}")
    except Exception as e:
        warnings.append(f"Failed to deeply analyze Audio: {str(e)}")
        
    return score, findings, warnings, raw_signals


def analyze_file(file_path: str, asset_type: str, metadata: Optional[Dict[str, Any]] = None) -> ForensicsResult:
    logger.info("Forensic analysis started")
    
    if '..' in str(file_path):
        logger.error("Forensic analysis failed: Path traversal detected")
        raise ForensicsEngineError("Path traversal detected")
        
    path = pathlib.Path(file_path)
    if not path.exists():
        logger.error("Forensic analysis failed: File does not exist")
        raise ForensicsEngineError("File does not exist")
        
    if path.is_dir():
        logger.error("Forensic analysis failed: Path is a directory")
        raise ForensicsEngineError("Path is a directory")
        
    resolved_path = path.resolve()
    
    try:
        parsed_asset_type = AssetType(asset_type.upper())
    except ValueError:
        parsed_asset_type = AssetType.UNKNOWN

    final_score = 100.0
    findings = []
    warnings = []
    raw_signals = {}
    
    if parsed_asset_type == AssetType.PDF:
        score, f, w, r = analyze_pdf(str(resolved_path))
    elif parsed_asset_type == AssetType.IMAGE:
        score, f, w, r = analyze_image(str(resolved_path))
    elif parsed_asset_type == AssetType.AUDIO:
        score, f, w, r = analyze_audio(str(resolved_path))
    else:
        score, f, w, r = 100.0, [], [f"Unsupported asset type for forensics: {asset_type}"], {}
        
    final_score = max(0.0, min(100.0, score))
    findings.extend(f)
    warnings.extend(w)
    raw_signals.update(r)
    
    if warnings:
        for w_item in warnings:
            logger.warning(f"Forensic warning: {w_item}")
            
    tampering_detected = final_score < 50.0
    
    confidence = 100.0
    if not raw_signals:
        confidence = 0.0
    elif any("skipped" in w.lower() or "failed" in w.lower() for w in warnings):
        confidence = 50.0
        
    logger.info("Forensic analysis completed")
    return ForensicsResult(
        asset_type=parsed_asset_type,
        analyzed_at=datetime.utcnow(),
        tampering_detected=tampering_detected,
        confidence=confidence,
        forensic_score=final_score,
        findings=findings,
        warnings=warnings,
        raw_signals=raw_signals
    )
