import pytest
import os
import json
import tempfile
import uuid
from datetime import datetime

from app.services.report_engine import ReportEngine
from app.schemas.report import ReportContent
from app.schemas.trust_score import TrustScoreResult, RiskLevel, DocumentStatus
from app.schemas.hash_result import HashResult
from app.schemas.metadata import MetadataResult, AssetType
from app.schemas.ai_explanation import AIExplanationResult, ExplanationMode

@pytest.fixture
def mock_evidence():
    asset_info = {"filename": "test.pdf", "size": 1024}
    
    hash_ev = HashResult(algorithm="SHA-256", hash="abc123def", size_bytes=1024)
    
    meta_ev = MetadataResult(
        asset_type=AssetType.PDF,
        filename="test.pdf",
        extension=".pdf",
        mime_type="application/pdf",
        size_bytes=1024,
        extracted_at=datetime.utcnow(),
        basic_metadata={},
        technical_metadata={},
        warnings=[]
    )
    
    trust_score_result = TrustScoreResult(
        trust_score=90.0,
        risk_level=RiskLevel.LOW,
        document_status=DocumentStatus.AUTHENTIC,
        confidence=100.0,
        score_breakdown={},
        penalties=[],
        calculated_at=datetime.utcnow()
    )
    
    ai_exp = AIExplanationResult(
        summary="Test summary <script>alert(1)</script>",
        evidence=["Evidence 1"],
        reasoning="Because of things",
        recommendation="Accept",
        confidence=100.0,
        generated_at=datetime.utcnow(),
        model_name="TestModel",
        explanation_mode=ExplanationMode.RULE_BASED,
        warnings=[]
    )
    
    return asset_info, hash_ev, meta_ev, None, trust_score_result, ai_exp

def test_report_content_structure(mock_evidence):
    engine = ReportEngine()
    asset_info, hash_ev, meta_ev, forensic_ev, trust_score_result, ai_exp = mock_evidence
    
    content = engine.create_report_content(
        asset_info, hash_ev, meta_ev, forensic_ev, trust_score_result, ai_exp, None
    )
    
    assert content.verification_summary == ai_exp.summary
    assert content.trust_score == 90.0
    assert content.risk_level == "RiskLevel.LOW" or content.risk_level == "LOW"
    assert content.document_status == "DocumentStatus.AUTHENTIC" or content.document_status == "AUTHENTIC"
    assert content.hash_details is not None
    assert content.forensic_findings is None
    assert content.blockchain_proof is None

def test_json_report_generation(mock_evidence):
    engine = ReportEngine()
    asset_info, hash_ev, meta_ev, forensic_ev, trust_score_result, ai_exp = mock_evidence
    
    with tempfile.TemporaryDirectory() as temp_dir:
        result = engine.generate_report(
            db=None,
            verification_id=uuid.uuid4(),
            asset_info=asset_info,
            hash_result=hash_ev,
            metadata_result=meta_ev,
            forensics_result=forensic_ev,
            trust_score_result=trust_score_result,
            ai_explanation_result=ai_exp,
            blockchain_proof=None,
            report_format="JSON",
            output_dir=temp_dir
        )
        
        assert result.status == "COMPLETED"
        assert result.report_format == "JSON"
        assert os.path.exists(result.report_path)
        
        with open(result.report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert data["trust_score"] == 90.0

def test_html_report_generation_and_escaping(mock_evidence):
    engine = ReportEngine()
    asset_info, hash_ev, meta_ev, forensic_ev, trust_score_result, ai_exp = mock_evidence
    
    with tempfile.TemporaryDirectory() as temp_dir:
        result = engine.generate_report(
            db=None,
            verification_id=uuid.uuid4(),
            asset_info=asset_info,
            hash_result=hash_ev,
            metadata_result=meta_ev,
            forensics_result=forensic_ev,
            trust_score_result=trust_score_result,
            ai_explanation_result=ai_exp,
            blockchain_proof=None,
            report_format="HTML",
            output_dir=temp_dir
        )
        
        assert result.status == "COMPLETED"
        assert result.report_format == "HTML"
        assert os.path.exists(result.report_path)
        
        with open(result.report_path, "r", encoding="utf-8") as f:
            html = f.read()
            # Ensure script tags are escaped
            assert "<script>alert(1)</script>" not in html
            assert "&lt;script&gt;alert(1)&lt;/script&gt;" in html

def test_missing_blockchain_proof_handled_gracefully(mock_evidence):
    engine = ReportEngine()
    asset_info, hash_ev, meta_ev, forensic_ev, trust_score_result, ai_exp = mock_evidence
    
    with tempfile.TemporaryDirectory() as temp_dir:
        result = engine.generate_report(
            db=None,
            verification_id=uuid.uuid4(),
            asset_info=asset_info,
            hash_result=hash_ev,
            metadata_result=meta_ev,
            forensics_result=forensic_ev,
            trust_score_result=trust_score_result,
            ai_explanation_result=ai_exp,
            blockchain_proof=None,
            report_format="HTML",
            output_dir=temp_dir
        )
        assert result.status == "COMPLETED"
        with open(result.report_path, "r", encoding="utf-8") as f:
            html = f.read()
            assert "Blockchain proof was not available" in html

def test_invalid_report_format_rejected(mock_evidence):
    engine = ReportEngine()
    asset_info, hash_ev, meta_ev, forensic_ev, trust_score_result, ai_exp = mock_evidence
    
    with tempfile.TemporaryDirectory() as temp_dir:
        result = engine.generate_report(
            db=None,
            verification_id=uuid.uuid4(),
            asset_info=asset_info,
            hash_result=hash_ev,
            metadata_result=meta_ev,
            forensics_result=forensic_ev,
            trust_score_result=trust_score_result,
            ai_explanation_result=ai_exp,
            blockchain_proof=None,
            report_format="XML",
            output_dir=temp_dir
        )
        
        assert result.status == "FAILED"
        assert "Unsupported report format" in result.summary

def test_report_path_generated_safely(mock_evidence):
    engine = ReportEngine()
    asset_info, hash_ev, meta_ev, forensic_ev, trust_score_result, ai_exp = mock_evidence
    
    with tempfile.TemporaryDirectory() as temp_dir:
        result = engine.generate_report(
            db=None,
            verification_id=uuid.uuid4(),
            asset_info=asset_info,
            hash_result=hash_ev,
            metadata_result=meta_ev,
            forensics_result=forensic_ev,
            trust_score_result=trust_score_result,
            ai_explanation_result=ai_exp,
            blockchain_proof=None,
            report_format="JSON",
            output_dir=temp_dir
        )
        
        filename = os.path.basename(result.report_path)
        assert filename.startswith("report_")
        assert filename.endswith(".json")
        assert ".." not in filename

def test_engine_does_not_calculate_trust_score(mock_evidence):
    import copy
    engine = ReportEngine()
    asset_info, hash_ev, meta_ev, forensic_ev, trust_score_result, ai_exp = mock_evidence
    
    ts_copy = copy.deepcopy(trust_score_result)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        engine.generate_report(
            db=None,
            verification_id=uuid.uuid4(),
            asset_info=asset_info,
            hash_result=hash_ev,
            metadata_result=meta_ev,
            forensics_result=forensic_ev,
            trust_score_result=trust_score_result,
            ai_explanation_result=ai_exp,
            blockchain_proof=None,
            report_format="JSON",
            output_dir=temp_dir
        )
        
    assert trust_score_result.model_dump() == ts_copy.model_dump()

def test_engine_does_not_call_ai():
    import pathlib
    engine_file = pathlib.Path("app/services/report_engine.py")
    content = engine_file.read_text()
    assert "AIExplanationEngine" not in content
    assert "LocalLLM" not in content
    assert "Qwen" not in content
    assert "Ollama" not in content

def test_engine_does_not_access_blockchain():
    import pathlib
    engine_file = pathlib.Path("app/services/report_engine.py")
    content = engine_file.read_text()
    assert "BlockchainEngine" not in content
    assert "blockchain_service" not in content

def test_engine_does_not_require_raw_file_contents(mock_evidence):
    engine = ReportEngine()
    asset_info, hash_ev, meta_ev, forensic_ev, trust_score_result, ai_exp = mock_evidence
    
    with tempfile.TemporaryDirectory() as temp_dir:
        result = engine.generate_report(
            db=None,
            verification_id=uuid.uuid4(),
            asset_info=asset_info,
            hash_result=hash_ev,
            metadata_result=meta_ev,
            forensics_result=forensic_ev,
            trust_score_result=trust_score_result,
            ai_explanation_result=ai_exp,
            blockchain_proof=None,
            report_format="JSON",
            output_dir=temp_dir
        )
        
        # Report succeeded with only dictionary/object inputs
        assert result.status == "COMPLETED"
        assert result.report_path != ""

def test_engine_does_not_import_other_engines():
    import pathlib
    engine_file = pathlib.Path("app/services/report_engine.py")
    content = engine_file.read_text()
    
    assert "HashEngine" not in content
    assert "MetadataEngine" not in content
    assert "ForensicsEngine" not in content
    assert "TrustScoreEngine" not in content
    assert "AIExplanationEngine" not in content
    assert "BlockchainEngine" not in content
    assert "VerificationEngine" not in content
    assert "VerificationOrchestrator" not in content
    
    # Still allowed to save file
    assert "open(" in content
