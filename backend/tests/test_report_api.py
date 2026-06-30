import pytest
from fastapi.testclient import TestClient
import uuid
import os
import json
from datetime import datetime, timezone
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database.session import get_db
from app.database.base import Base
from app.models.user import User
from app.models.asset import Asset
from app.models.verification import Verification
from app.models.report import Report
from app.schemas.report import ReportContent

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql.expression import FunctionElement

@compiles(JSONB, 'sqlite')
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

class now(FunctionElement):
    type = None
    name = 'NOW'

@compiles(now, 'sqlite')
def sqlite_now(element, compiler, **kw):
    return "CURRENT_TIMESTAMP"

class uuid_generate_v4(FunctionElement):
    type = None
    name = 'uuid_generate_v4'

@compiles(uuid_generate_v4, 'sqlite')
def sqlite_uuid(element, compiler, **kw):
    return "lower(hex(randomblob(16)))"

from sqlalchemy.pool import StaticPool
from sqlalchemy import event

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

@event.listens_for(engine, "before_cursor_execute", retval=True)
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    statement = statement.replace("NOW()", "CURRENT_TIMESTAMP")
    statement = statement.replace("uuid_generate_v4()", "lower(hex(randomblob(16)))")
    return statement, parameters

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    app.dependency_overrides[get_db] = override_get_db
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    
    # Create two users
    user1 = User(email="user1@example.com", password_hash="fakehash", is_active=True)
    user2 = User(email="user2@example.com", password_hash="fakehash", is_active=True)
    db.add_all([user1, user2])
    db.commit()
    
    yield
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def user1_token():
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": "user1@example.com"})
    return f"Bearer {token}"

@pytest.fixture
def user2_token():
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": "user2@example.com"})
    return f"Bearer {token}"

@pytest.fixture
def populate_reports(tmp_path):
    db = TestingSessionLocal()
    
    # Clear tables
    db.query(Report).delete()
    db.query(Verification).delete()
    db.query(Asset).delete()
    db.commit()
    
    user1 = db.query(User).filter(User.email == "user1@example.com").first()
    user2 = db.query(User).filter(User.email == "user2@example.com").first()
    
    # Create asset and verification for user 1
    asset1 = Asset(user_id=user1.id, original_filename="test1.pdf", storage_path="fake/path", asset_type="PDF", file_hash="fakehash1")
    db.add(asset1)
    db.commit()
    
    verif1 = Verification(asset_id=asset1.id, status="COMPLETED", trust_score=95.0, risk_level="LOW")
    db.add(verif1)
    db.commit()
    
    # Create JSON report on disk for verif1
    report_content = {
        "verification_summary": "Test Summary",
        "asset_details": {"filename": "test1.pdf"},
        "hash_details": None,
        "metadata_details": None,
        "forensic_findings": None,
        "trust_score": 95.0,
        "risk_level": "LOW",
        "document_status": "AUTHENTIC",
        "ai_explanation": None,
        "blockchain_proof": None,
        "generated_at": datetime.utcnow().isoformat()
    }
    
    report_path = str(tmp_path / f"report_{uuid.uuid4().hex}.json")
    with open(report_path, "w") as f:
        json.dump(report_content, f)
        
    report1 = Report(verification_id=verif1.id, report_url=report_path)
    db.add(report1)
    db.commit()
    
    # Create asset and verification for user 2
    asset2 = Asset(user_id=user2.id, original_filename="test2.pdf", storage_path="fake/path", asset_type="PDF", file_hash="fakehash2")
    db.add(asset2)
    db.commit()
    
    verif2 = Verification(asset_id=asset2.id, status="COMPLETED", trust_score=50.0, risk_level="HIGH")
    db.add(verif2)
    db.commit()
    
    # Missing file report for user 1
    asset3 = Asset(user_id=user1.id, original_filename="test3.pdf", storage_path="fake/path", asset_type="PDF", file_hash="fakehash3")
    db.add(asset3)
    db.commit()
    verif3 = Verification(asset_id=asset3.id, status="COMPLETED")
    db.add(verif3)
    db.commit()
    
    report3 = Report(verification_id=verif3.id, report_url=str(tmp_path / "missing.json"))
    db.add(report3)
    db.commit()
    
    res = {
        "user1": {
            "asset_id": asset1.id, 
            "verif_id": verif1.id, 
            "report_id": report1.id, 
            "verif_missing_file_id": verif3.id, 
            "report_missing_file_id": report3.id
        },
        "user2": {
            "asset_id": asset2.id, 
            "verif_id": verif2.id, 
            "report_id": None
        },
        "tmp_path": tmp_path
    }
    db.close()
    
    return res

def test_reports_requires_jwt():
    res = client.get("/api/v1/reports")
    assert res.status_code == 401

def test_generate_json_report_returns_existing(user1_token, populate_reports):
    verif_id = populate_reports["user1"]["verif_id"]
    res = client.post(f"/api/v1/reports/generate/{verif_id}", json={"report_format": "JSON"}, headers={"Authorization": user1_token})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["report_format"] == "JSON"
    assert data["data"]["verification_id"] == str(verif_id)

@patch("app.services.ai_explanation_engine.AIExplanationEngine.generate_explanation")
@patch("app.services.trust_score_engine.calculate_score")
def test_generate_html_report(mock_ts, mock_ai, user1_token, populate_reports):
    verif_id = populate_reports["user1"]["verif_id"]
    res = client.post(f"/api/v1/reports/generate/{verif_id}", json={"report_format": "HTML"}, headers={"Authorization": user1_token})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["report_format"] == "HTML"
    
    # Ensure neither AI nor Trust score engines were called (since we generate from existing JSON)
    mock_ts.assert_not_called()
    mock_ai.assert_not_called()

def test_generate_invalid_format(user1_token, populate_reports):
    verif_id = populate_reports["user1"]["verif_id"]
    res = client.post(f"/api/v1/reports/generate/{verif_id}", json={"report_format": "XML"}, headers={"Authorization": user1_token})
    assert res.status_code == 400
    assert res.json()["error"]["code"] == "INVALID_REPORT_FORMAT"

def test_generate_missing_report_fails(user2_token, populate_reports):
    verif_id = populate_reports["user2"]["verif_id"]
    res = client.post(f"/api/v1/reports/generate/{verif_id}", json={"report_format": "JSON"}, headers={"Authorization": user2_token})
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "REPORT_NOT_FOUND"

def test_get_report_metadata(user1_token, populate_reports):
    report_id = populate_reports["user1"]["report_id"]
    res = client.get(f"/api/v1/reports/{report_id}", headers={"Authorization": user1_token})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["report_id"] == str(report_id)
    # Check no sensitive data
    res_str = str(data).lower()
    assert "storage_path" not in res_str
    assert "raw_file_content" not in res_str
    assert "password_hash" not in res_str

def test_get_report_unauthorized_user(user2_token, populate_reports):
    report_id = populate_reports["user1"]["report_id"]
    res = client.get(f"/api/v1/reports/{report_id}", headers={"Authorization": user2_token})
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"

def test_download_json_report(user1_token, populate_reports):
    report_id = populate_reports["user1"]["report_id"]
    res = client.get(f"/api/v1/reports/download/{report_id}", headers={"Authorization": user1_token})
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/json"
    assert b"Test Summary" in res.content

def test_download_missing_file(user1_token, populate_reports):
    report_id = populate_reports["user1"]["report_missing_file_id"]
    res = client.get(f"/api/v1/reports/download/{report_id}", headers={"Authorization": user1_token})
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "REPORT_FILE_NOT_FOUND"

def test_list_reports(user1_token, populate_reports):
    res = client.get("/api/v1/reports", headers={"Authorization": user1_token})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["total"] >= 1
    
    # Assert response wrapper
    assert "success" in data
    assert "error" not in data
    
    # Sensitive fields check in list
    res_str = str(data).lower()
    assert "storage_path" not in res_str
    assert "raw_file_content" not in res_str
    assert "password_hash" not in res_str

def test_pagination_works(user1_token, populate_reports):
    res = client.get("/api/v1/reports?page=1&limit=1", headers={"Authorization": user1_token})
    data = res.json()["data"]
    assert len(data["items"]) == 1
    assert data["page"] == 1
    assert data["limit"] == 1
