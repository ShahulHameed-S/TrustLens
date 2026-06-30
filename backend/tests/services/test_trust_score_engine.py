import pytest
from datetime import datetime

from app.services.trust_score_engine import calculate_score
from app.schemas.trust_score import RiskLevel, DocumentStatus
from app.schemas.hash_result import HashResult
from app.schemas.metadata import MetadataResult, AssetType
from app.schemas.forensics import ForensicsResult

def build_perfect_hash():
    return HashResult(algorithm="SHA-256", hash="abc123def", size_bytes=1024)

def build_perfect_metadata():
    return MetadataResult(
        asset_type=AssetType.IMAGE,
        filename="test.png",
        extension=".png",
        mime_type="image/png",
        size_bytes=1024,
        extracted_at=datetime.utcnow(),
        basic_metadata={},
        technical_metadata={"width": 100},
        warnings=[]
    )

def build_perfect_forensics():
    return ForensicsResult(
        asset_type=AssetType.IMAGE,
        analyzed_at=datetime.utcnow(),
        tampering_detected=False,
        confidence=100.0,
        forensic_score=100.0,
        findings=[],
        warnings=[],
        raw_signals={"width": 100}
    )

def build_perfect_blockchain():
    return {"is_matched": True, "tx_hash": "0x123"}

def test_perfect_evidence():
    result = calculate_score(
        build_perfect_hash(),
        build_perfect_metadata(),
        build_perfect_forensics(),
        build_perfect_blockchain()
    )
    assert result.trust_score == 100.0
    assert result.confidence == 100.0
    assert result.risk_level == RiskLevel.LOW
    assert result.document_status == DocumentStatus.AUTHENTIC
    assert len(result.penalties) == 0

def test_missing_metadata_reduces_score():
    meta = build_perfect_metadata()
    meta.technical_metadata = {}
    
    result = calculate_score(
        build_perfect_hash(),
        meta,
        build_perfect_forensics(),
        build_perfect_blockchain()
    )
    assert result.trust_score < 100.0
    assert any(p.reason == "Technical metadata missing" for p in result.penalties)
    assert result.risk_level == RiskLevel.LOW

def test_forensic_warnings_reduce_score():
    forensic = build_perfect_forensics()
    forensic.warnings = ["Test warning"]
    
    result = calculate_score(
        build_perfect_hash(),
        build_perfect_metadata(),
        forensic,
        build_perfect_blockchain()
    )
    assert result.trust_score < 100.0
    assert any(p.reason == "Forensic warnings present" for p in result.penalties)

def test_forensic_score_below_80_medium_penalty():
    forensic = build_perfect_forensics()
    forensic.forensic_score = 75.0
    
    result = calculate_score(
        build_perfect_hash(),
        build_perfect_metadata(),
        forensic,
        build_perfect_blockchain()
    )
    assert any(p.reason == "Forensic score below 80" for p in result.penalties)
    assert result.trust_score == 90.0

def test_forensic_score_below_50_high_penalty():
    forensic = build_perfect_forensics()
    forensic.forensic_score = 45.0
    
    result = calculate_score(
        build_perfect_hash(),
        build_perfect_metadata(),
        forensic,
        build_perfect_blockchain()
    )
    assert any(p.reason == "Forensic score below 50" for p in result.penalties)
    assert result.trust_score == 75.0

def test_tampering_detected_true_high_penalty():
    forensic = build_perfect_forensics()
    forensic.tampering_detected = True
    
    result = calculate_score(
        build_perfect_hash(),
        build_perfect_metadata(),
        forensic,
        build_perfect_blockchain()
    )
    assert any(p.reason == "Strong tampering detected" for p in result.penalties)
    assert result.document_status == DocumentStatus.UNVERIFIED

def test_blockchain_unavailable_reduces_confidence_only():
    result = calculate_score(
        build_perfect_hash(),
        build_perfect_metadata(),
        build_perfect_forensics(),
        None
    )
    assert result.trust_score == 100.0
    assert result.confidence < 100.0
    assert any(p.reason == "Blockchain evidence unavailable (confidence penalty only)" for p in result.penalties)

def test_blockchain_mismatch_heavily_reduces_score():
    result = calculate_score(
        build_perfect_hash(),
        build_perfect_metadata(),
        build_perfect_forensics(),
        {"is_matched": False}
    )
    assert result.trust_score < 100.0
    assert any(p.reason == "Blockchain mismatch" for p in result.penalties)

def test_score_never_goes_below_0():
    result = calculate_score(
        None,
        None,
        None,
        {"is_matched": False}
    )
    assert result.trust_score == 0.0
    assert result.risk_level == RiskLevel.HIGH
    assert result.document_status == DocumentStatus.UNVERIFIED

def test_score_never_goes_above_100():
    result = calculate_score(
        build_perfect_hash(),
        build_perfect_metadata(),
        build_perfect_forensics(),
        build_perfect_blockchain()
    )
    assert result.trust_score == 100.0

def test_missing_evidence_does_not_crash():
    result = calculate_score(None, None, None, None)
    assert result.trust_score == 15.0
    assert result.confidence == 65.0 # 100 - 20 (forensic missing) - 15 (blockchain missing)
    assert len(result.penalties) == 4

def test_classifications():
    # HIGH / UNVERIFIED
    result1 = calculate_score(None, None, None, None)
    assert result1.risk_level == RiskLevel.HIGH
    assert result1.document_status == DocumentStatus.UNVERIFIED
    
    # LOW / AUTHENTIC
    result2 = calculate_score(build_perfect_hash(), build_perfect_metadata(), build_perfect_forensics(), build_perfect_blockchain())
    assert result2.risk_level == RiskLevel.LOW
    assert result2.document_status == DocumentStatus.AUTHENTIC

    # MEDIUM / SUSPICIOUS
    forensic = build_perfect_forensics()
    forensic.forensic_score = 45.0
    result3 = calculate_score(build_perfect_hash(), None, forensic, build_perfect_blockchain())
    # 100 - 20(meta missing) - 25(forensic < 50) = 55
    assert result3.trust_score == 55.0
    assert result3.risk_level == RiskLevel.MEDIUM
    assert result3.document_status == DocumentStatus.SUSPICIOUS
