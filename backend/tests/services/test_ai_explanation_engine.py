import pytest
from datetime import datetime

from app.services.ai_explanation_engine import AIExplanationEngine
from app.schemas.ai_explanation import ExplanationMode
from app.schemas.trust_score import TrustScoreResult, RiskLevel, DocumentStatus, Penalty
from app.schemas.hash_result import HashResult
from app.schemas.metadata import MetadataResult, AssetType
from app.schemas.forensics import ForensicsResult

@pytest.fixture
def base_evidence():
    hash_ev = HashResult(algorithm="SHA-256", hash="abc123def", size_bytes=1024)
    meta_ev = MetadataResult(
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
    forensic_ev = ForensicsResult(
        asset_type=AssetType.IMAGE,
        analyzed_at=datetime.utcnow(),
        tampering_detected=False,
        confidence=100.0,
        forensic_score=100.0,
        findings=[],
        warnings=[],
        raw_signals={"width": 100}
    )
    bc_ev = {"is_matched": True, "tx_hash": "0x123"}
    return hash_ev, meta_ev, forensic_ev, bc_ev

def test_authentic_explanation(base_evidence):
    engine = AIExplanationEngine(use_llm=False)
    hash_ev, meta_ev, forensic_ev, bc_ev = base_evidence
    
    trust_score_result = TrustScoreResult(
        trust_score=100.0,
        risk_level=RiskLevel.LOW,
        document_status=DocumentStatus.AUTHENTIC,
        confidence=100.0,
        score_breakdown={},
        penalties=[],
        calculated_at=datetime.utcnow()
    )
    
    result = engine.generate_explanation(hash_ev, meta_ev, forensic_ev, trust_score_result, bc_ev)
    
    assert "authentic" in result.summary.lower()
    assert result.explanation_mode == ExplanationMode.RULE_BASED
    assert len(result.evidence) == 4
    assert "no integrity penalties" in result.reasoning.lower()
    assert "normal confidence" in result.recommendation.lower()

def test_suspicious_explanation(base_evidence):
    engine = AIExplanationEngine(use_llm=False)
    hash_ev, meta_ev, forensic_ev, bc_ev = base_evidence
    
    trust_score_result = TrustScoreResult(
        trust_score=60.0,
        risk_level=RiskLevel.MEDIUM,
        document_status=DocumentStatus.SUSPICIOUS,
        confidence=100.0,
        score_breakdown={},
        penalties=[Penalty(reason="Forensic warnings present", points_deducted=10.0)],
        calculated_at=datetime.utcnow()
    )
    
    result = engine.generate_explanation(hash_ev, meta_ev, forensic_ev, trust_score_result, bc_ev)
    
    assert "suspicious" in result.summary.lower()
    assert "review the forensic findings" in result.recommendation.lower()
    assert "forensic warnings present" in result.reasoning.lower()

def test_unverified_explanation(base_evidence):
    engine = AIExplanationEngine(use_llm=False)
    hash_ev, meta_ev, forensic_ev, bc_ev = base_evidence
    
    trust_score_result = TrustScoreResult(
        trust_score=20.0,
        risk_level=RiskLevel.HIGH,
        document_status=DocumentStatus.UNVERIFIED,
        confidence=100.0,
        score_breakdown={},
        penalties=[Penalty(reason="Hash missing or invalid", points_deducted=30.0)],
        calculated_at=datetime.utcnow()
    )
    
    result = engine.generate_explanation(hash_ev, meta_ev, forensic_ev, trust_score_result, bc_ev)
    
    assert "cannot be trusted" in result.summary.lower()
    assert "do not trust this asset" in result.recommendation.lower()
    assert "hash missing or invalid" in result.reasoning.lower()

def test_missing_metadata_evidence(base_evidence):
    engine = AIExplanationEngine()
    hash_ev, _, forensic_ev, bc_ev = base_evidence
    
    trust_score_result = TrustScoreResult(
        trust_score=80.0,
        risk_level=RiskLevel.LOW,
        document_status=DocumentStatus.AUTHENTIC,
        confidence=100.0,
        score_breakdown={},
        penalties=[],
        calculated_at=datetime.utcnow()
    )
    
    result = engine.generate_explanation(hash_ev, None, forensic_ev, trust_score_result, bc_ev)
    assert any("metadata evidence is unavailable" in e.lower() for e in result.evidence)

def test_missing_blockchain_evidence(base_evidence):
    engine = AIExplanationEngine()
    hash_ev, meta_ev, forensic_ev, _ = base_evidence
    
    trust_score_result = TrustScoreResult(
        trust_score=80.0,
        risk_level=RiskLevel.LOW,
        document_status=DocumentStatus.AUTHENTIC,
        confidence=100.0,
        score_breakdown={},
        penalties=[],
        calculated_at=datetime.utcnow()
    )
    
    result = engine.generate_explanation(hash_ev, meta_ev, forensic_ev, trust_score_result, None)
    assert any("blockchain evidence is unavailable" in e.lower() for e in result.evidence)
    assert "blockchain proof was not available" in result.recommendation.lower()

def test_blockchain_mismatch_explanation(base_evidence):
    engine = AIExplanationEngine()
    hash_ev, meta_ev, forensic_ev, _ = base_evidence
    bc_ev = {"is_matched": False}
    
    trust_score_result = TrustScoreResult(
        trust_score=60.0,
        risk_level=RiskLevel.MEDIUM,
        document_status=DocumentStatus.SUSPICIOUS,
        confidence=100.0,
        score_breakdown={},
        penalties=[],
        calculated_at=datetime.utcnow()
    )
    
    result = engine.generate_explanation(hash_ev, meta_ev, forensic_ev, trust_score_result, bc_ev)
    assert any("blockchain record did not match" in e.lower() for e in result.evidence)
    assert "blockchain mismatch was detected" in result.recommendation.lower()

def test_fallback_mode():
    engine = AIExplanationEngine()
    
    # Intentionally passing None for trust_score_result to trigger an exception in the provider
    result = engine.generate_explanation(None, None, None, None, None)
    
    assert result.explanation_mode == ExplanationMode.FALLBACK
    assert "error occurred" in result.summary.lower()
    assert result.confidence == 0.0
    assert len(result.warnings) > 0
    assert "Fallback" in result.model_name

def test_low_risk_recommendation(base_evidence):
    engine = AIExplanationEngine()
    hash_ev, meta_ev, forensic_ev, bc_ev = base_evidence
    tsr = TrustScoreResult(
        trust_score=90.0,
        risk_level=RiskLevel.LOW,
        document_status=DocumentStatus.AUTHENTIC,
        confidence=100.0,
        score_breakdown={},
        penalties=[],
        calculated_at=datetime.utcnow()
    )
    result = engine.generate_explanation(hash_ev, meta_ev, forensic_ev, tsr, bc_ev)
    assert "normal confidence" in result.recommendation.lower()

def test_medium_risk_recommendation(base_evidence):
    engine = AIExplanationEngine()
    hash_ev, meta_ev, forensic_ev, bc_ev = base_evidence
    tsr = TrustScoreResult(
        trust_score=60.0,
        risk_level=RiskLevel.MEDIUM,
        document_status=DocumentStatus.SUSPICIOUS,
        confidence=100.0,
        score_breakdown={},
        penalties=[],
        calculated_at=datetime.utcnow()
    )
    result = engine.generate_explanation(hash_ev, meta_ev, forensic_ev, tsr, bc_ev)
    assert "review the forensic findings" in result.recommendation.lower()

def test_high_risk_recommendation(base_evidence):
    engine = AIExplanationEngine()
    hash_ev, meta_ev, forensic_ev, bc_ev = base_evidence
    tsr = TrustScoreResult(
        trust_score=20.0,
        risk_level=RiskLevel.HIGH,
        document_status=DocumentStatus.UNVERIFIED,
        confidence=100.0,
        score_breakdown={},
        penalties=[],
        calculated_at=datetime.utcnow()
    )
    result = engine.generate_explanation(hash_ev, meta_ev, forensic_ev, tsr, bc_ev)
    assert "do not trust this asset without manual verification" in result.recommendation.lower()

def test_penalties_included_in_reasoning(base_evidence):
    engine = AIExplanationEngine()
    hash_ev, meta_ev, forensic_ev, bc_ev = base_evidence
    tsr = TrustScoreResult(
        trust_score=40.0,
        risk_level=RiskLevel.HIGH,
        document_status=DocumentStatus.UNVERIFIED,
        confidence=100.0,
        score_breakdown={},
        penalties=[
            Penalty(reason="Missing Metadata", points_deducted=10.0),
            Penalty(reason="Bad Hash", points_deducted=50.0)
        ],
        calculated_at=datetime.utcnow()
    )
    result = engine.generate_explanation(hash_ev, meta_ev, forensic_ev, tsr, bc_ev)
    assert "Missing Metadata" in result.reasoning
    assert "Bad Hash" in result.reasoning

def test_engine_does_not_modify_trust_score_result(base_evidence):
    import copy
    engine = AIExplanationEngine()
    hash_ev, meta_ev, forensic_ev, bc_ev = base_evidence
    tsr = TrustScoreResult(
        trust_score=80.0,
        risk_level=RiskLevel.LOW,
        document_status=DocumentStatus.AUTHENTIC,
        confidence=100.0,
        score_breakdown={"hash": 30.0},
        penalties=[Penalty(reason="Test", points_deducted=5.0)],
        calculated_at=datetime.utcnow()
    )
    
    tsr_copy = copy.deepcopy(tsr)
    engine.generate_explanation(hash_ev, meta_ev, forensic_ev, tsr, bc_ev)
    
    assert tsr.model_dump() == tsr_copy.model_dump()

def test_output_schema_is_always_valid(base_evidence):
    from app.schemas.ai_explanation import AIExplanationResult
    engine = AIExplanationEngine()
    hash_ev, meta_ev, forensic_ev, bc_ev = base_evidence
    tsr = TrustScoreResult(
        trust_score=80.0,
        risk_level=RiskLevel.LOW,
        document_status=DocumentStatus.AUTHENTIC,
        confidence=100.0,
        score_breakdown={},
        penalties=[],
        calculated_at=datetime.utcnow()
    )
    result = engine.generate_explanation(hash_ev, meta_ev, forensic_ev, tsr, bc_ev)
    assert isinstance(result, AIExplanationResult)

def test_no_file_contents_required(base_evidence):
    engine = AIExplanationEngine()
    hash_ev, meta_ev, forensic_ev, bc_ev = base_evidence
    tsr = TrustScoreResult(
        trust_score=80.0,
        risk_level=RiskLevel.LOW,
        document_status=DocumentStatus.AUTHENTIC,
        confidence=100.0,
        score_breakdown={},
        penalties=[],
        calculated_at=datetime.utcnow()
    )
    result = engine.generate_explanation(hash_ev, meta_ev, forensic_ev, tsr, bc_ev)
    assert result.confidence > 0

def test_no_database_access_used():
    import pathlib
    engine_file = pathlib.Path("app/services/ai_explanation_engine.py")
    content = engine_file.read_text()
    assert "sqlalchemy" not in content.lower()
    assert "session" not in content.lower()
    assert "repository" not in content.lower()
    assert "database" not in content.lower()

def test_fallback_mode_works_without_llm(base_evidence):
    engine = AIExplanationEngine(use_llm=True)
    hash_ev, meta_ev, forensic_ev, bc_ev = base_evidence
    tsr = TrustScoreResult(
        trust_score=80.0,
        risk_level=RiskLevel.LOW,
        document_status=DocumentStatus.AUTHENTIC,
        confidence=100.0,
        score_breakdown={},
        penalties=[],
        calculated_at=datetime.utcnow()
    )
    result = engine.generate_explanation(hash_ev, meta_ev, forensic_ev, tsr, bc_ev)
    assert result.explanation_mode == ExplanationMode.RULE_BASED
    assert result.confidence == 100.0
