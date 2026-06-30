import pytest
import uuid
import os
from datetime import datetime
from unittest.mock import patch, MagicMock

from app.services.verification_service import VerificationService
from app.schemas.user import UserResponse
from app.schemas.metadata import AssetType

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def current_user():
    from datetime import datetime
    return UserResponse(
        id=uuid.uuid4(),
        email="test@example.com",
        full_name="Test User",
        is_active=True,
        is_superuser=False,
        role=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

def test_missing_asset_returns_proper_error(mock_db, current_user):
    service = VerificationService()
    
    with patch('app.services.verification_service.AssetRepository.get_by_id', return_value=None):
        resp = service.verify_pdf(mock_db, uuid.uuid4(), current_user)
        
    assert not resp.success
    assert "Asset not found" in resp.error

def test_user_cannot_verify_another_users_asset(mock_db, current_user):
    service = VerificationService()
    
    mock_asset = MagicMock()
    mock_asset.user_id = uuid.uuid4() # Different user
    
    with patch('app.services.verification_service.AssetRepository.get_by_id', return_value=mock_asset):
        resp = service.verify_pdf(mock_db, uuid.uuid4(), current_user)
        
    assert not resp.success
    assert "Unauthorized asset access" in resp.error

def test_wrong_endpoint_rejects_wrong_asset_type(mock_db, current_user):
    service = VerificationService()
    
    mock_asset = MagicMock()
    mock_asset.user_id = current_user.id
    mock_asset.asset_type = "IMAGE"
    
    with patch('app.services.verification_service.AssetRepository.get_by_id', return_value=mock_asset):
        resp = service.verify_pdf(mock_db, uuid.uuid4(), current_user)
        
    assert not resp.success
    assert "Invalid asset type" in resp.error
    assert "Expected PDF, got IMAGE" in resp.error

def test_missing_file_fails_safely(mock_db, current_user):
    service = VerificationService()
    
    mock_asset = MagicMock()
    mock_asset.user_id = current_user.id
    mock_asset.asset_type = "PDF"
    mock_asset.storage_path = "/nonexistent/path.pdf"
    
    with patch('app.services.verification_service.AssetRepository.get_by_id', return_value=mock_asset):
        with patch('os.path.exists', return_value=False):
            resp = service.verify_pdf(mock_db, uuid.uuid4(), current_user)
            
    assert not resp.success
    assert "Asset file missing on disk" in resp.error

@patch('app.services.verification_service.HashEngine.calculate_sha256')
@patch('app.services.verification_service.extract_metadata')
@patch('app.services.verification_service.analyze_file')
@patch('app.services.verification_service.calculate_score')
@patch('app.services.verification_service.BlockchainEngine.register_hash')
@patch('app.services.verification_service.AIExplanationEngine.generate_explanation')
@patch('app.services.verification_service.ReportEngine.generate_report')
def test_verify_pdf_successfully(
    mock_gen_report, mock_gen_exp, mock_reg_hash, mock_calc_score,
    mock_analyze_file, mock_extract_meta, mock_calc_hash,
    mock_db, current_user
):
    service = VerificationService()
    
    mock_asset = MagicMock()
    mock_asset.id = uuid.uuid4()
    mock_asset.user_id = current_user.id
    mock_asset.asset_type = "PDF"
    mock_asset.storage_path = "/real/path.pdf"
    mock_asset.original_filename = "test.pdf"
    mock_asset.size = 100
    
    mock_verif = MagicMock()
    mock_verif.id = uuid.uuid4()
    
    # Mock repositories
    with patch('app.services.verification_service.AssetRepository.get_by_id', return_value=mock_asset), \
         patch('os.path.exists', return_value=True), \
         patch.object(service.verification_repo, 'create_verification', return_value=mock_verif), \
         patch.object(service.verification_repo, 'update_verification_result') as mock_update_res, \
         patch.object(service.ai_analysis_repo, 'create_ai_analysis') as mock_ai_repo:
         
        # Set up mock engine outputs
        mock_calc_hash.return_value = MagicMock(hash="123")
        
        meta_mock = MagicMock()
        meta_mock.model_dump.return_value = {"meta": "data"}
        mock_extract_meta.return_value = meta_mock
        
        for_mock = MagicMock()
        for_mock.model_dump.return_value = {"for": "data"}
        mock_analyze_file.return_value = for_mock
        
        score_mock = MagicMock()
        score_mock.trust_score = 99.0
        
        risk_enum_mock = MagicMock()
        risk_enum_mock.value = "LOW"
        score_mock.risk_level = risk_enum_mock
        
        status_enum_mock = MagicMock()
        status_enum_mock.value = "AUTHENTIC"
        score_mock.document_status = status_enum_mock
        
        mock_calc_score.return_value = score_mock
        
        bc_mock = MagicMock()
        bc_mock.model_dump.return_value = {"tx_id": "123"}
        mock_reg_hash.return_value = bc_mock
        
        mock_exp = MagicMock()
        mock_exp.model_name = "MockModel"
        mock_exp.model_dump.return_value = {"exp": "data"}
        mock_gen_exp.return_value = mock_exp
        
        rep_mock = MagicMock()
        rep_mock.report_id = uuid.uuid4()
        rep_mock.report_format = "JSON"
        rep_mock.generated_at = datetime.utcnow()
        mock_gen_report.return_value = rep_mock
        
        resp = service.verify_pdf(mock_db, uuid.uuid4(), current_user, True, True)
        
        assert resp.success
        assert resp.data.verification_id == mock_verif.id
        assert resp.data.trust_score == 99.0
        assert resp.data.report["generated"] is True
        
        # Verify status update was called
        mock_update_res.assert_called_once_with(mock_db, mock_verif.id, score_mock)
        mock_ai_repo.assert_called_once()
        
def test_failed_verification_updates_status_to_failed(mock_db, current_user):
    service = VerificationService()
    
    mock_asset = MagicMock()
    mock_asset.user_id = current_user.id
    mock_asset.asset_type = "PDF"
    mock_asset.storage_path = "/real/path.pdf"
    
    mock_verif = MagicMock()
    mock_verif.id = uuid.uuid4()
    
    with patch('app.services.verification_service.AssetRepository.get_by_id', return_value=mock_asset), \
         patch('os.path.exists', return_value=True), \
         patch.object(service.verification_repo, 'create_verification', return_value=mock_verif), \
         patch.object(service.verification_repo, 'update_verification_status') as mock_update_stat, \
         patch.object(service.hash_engine, 'calculate_sha256', side_effect=Exception("Disk failure")):
         
        resp = service.verify_pdf(mock_db, uuid.uuid4(), current_user)
        
        assert not resp.success
        assert "Disk failure" in resp.error
        
        mock_update_stat.assert_called_once_with(mock_db, mock_verif.id, "FAILED")
        
@patch('app.services.verification_service.HashEngine.calculate_sha256')
@patch('app.services.verification_service.extract_metadata')
@patch('app.services.verification_service.analyze_file')
@patch('app.services.verification_service.calculate_score')
@patch('app.services.verification_service.BlockchainEngine.register_hash')
@patch('app.services.verification_service.AIExplanationEngine.generate_explanation')
@patch('app.services.verification_service.ReportEngine.generate_report')
def test_blockchain_skipped_when_disabled(
    mock_gen_report, mock_gen_exp, mock_reg_hash, mock_calc_score,
    mock_analyze_file, mock_extract_meta, mock_calc_hash,
    mock_db, current_user
):
    service = VerificationService()
    mock_asset = MagicMock()
    mock_asset.id = uuid.uuid4()
    mock_asset.user_id = current_user.id
    mock_asset.asset_type = "PDF"
    mock_asset.storage_path = "/real/path.pdf"
    mock_asset.original_filename = "test.pdf"
    
    mock_verif = MagicMock()
    mock_verif.id = uuid.uuid4()
    
    with patch('app.services.verification_service.AssetRepository.get_by_id', return_value=mock_asset), \
         patch('os.path.exists', return_value=True), \
         patch.object(service.verification_repo, 'create_verification', return_value=mock_verif), \
         patch.object(service.verification_repo, 'update_verification_result'), \
         patch.object(service.ai_analysis_repo, 'create_ai_analysis'):
         
        # Set up mock engine outputs
        mock_calc_hash.return_value = MagicMock(hash="123")
        
        meta_mock = MagicMock()
        meta_mock.model_dump.return_value = {"meta": "data"}
        mock_extract_meta.return_value = meta_mock
        
        for_mock = MagicMock()
        for_mock.model_dump.return_value = {"for": "data"}
        mock_analyze_file.return_value = for_mock
        
        score_mock = MagicMock()
        score_mock.trust_score = 99.0
        
        risk_enum_mock = MagicMock()
        risk_enum_mock.value = "LOW"
        score_mock.risk_level = risk_enum_mock
        
        status_enum_mock = MagicMock()
        status_enum_mock.value = "AUTHENTIC"
        score_mock.document_status = status_enum_mock
        
        mock_calc_score.return_value = score_mock
        
        mock_exp = MagicMock()
        mock_exp.model_name = "MockModel"
        mock_exp.model_dump.return_value = {"exp": "data"}
        mock_gen_exp.return_value = mock_exp
        
        rep_mock = MagicMock()
        rep_mock.report_id = uuid.uuid4()
        rep_mock.report_format = "JSON"
        rep_mock.generated_at = datetime.utcnow()
        mock_gen_report.return_value = rep_mock
         
        resp = service.verify_pdf(mock_db, uuid.uuid4(), current_user, register_to_blockchain=False, generate_report=False)
        
        assert resp.success
        mock_reg_hash.assert_not_called()
        assert resp.data.blockchain_proof is None
        
def test_engine_independence():
    import pathlib
    routes_file = pathlib.Path("app/api/v1/routes/verifications.py")
    content = routes_file.read_text()
    
    # Assert routes do not implement engine logic
    assert "TrustScoreEngine" not in content
    assert "BlockchainEngine" not in content
    assert "ForensicsEngine" not in content
    assert "AIExplanationEngine" not in content
    assert "ReportEngine" not in content
