import pytest
from fastapi.testclient import TestClient
import uuid
import os
import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database.session import get_db
from app.database.base import Base
from app.models.user import User
from app.models.asset import Asset
from app.models.verification import Verification
from app.models.report import Report
from app.models.blockchain_block import BlockchainBlock

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
    
    user1 = User(email="user1_analytics@example.com", password_hash="fakehash", is_active=True)
    user2 = User(email="user2_analytics@example.com", password_hash="fakehash", is_active=True)
    db.add_all([user1, user2])
    db.commit()
    
    yield
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def user1_token():
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": "user1_analytics@example.com"})
    return f"Bearer {token}"

@pytest.fixture
def user2_token():
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": "user2_analytics@example.com"})
    return f"Bearer {token}"

@pytest.fixture
def populate_analytics():
    db = TestingSessionLocal()
    
    # Clear tables
    db.query(BlockchainBlock).delete()
    db.query(Report).delete()
    db.query(Verification).delete()
    db.query(Asset).delete()
    db.commit()
    
    user1 = db.query(User).filter(User.email == "user1_analytics@example.com").first()
    user2 = db.query(User).filter(User.email == "user2_analytics@example.com").first()
    
    # --- User 1 Data ---
    # Assets
    asset1 = Asset(user_id=user1.id, original_filename="doc1.pdf", storage_path="/path1", asset_type="PDF", file_hash="hash1")
    asset2 = Asset(user_id=user1.id, original_filename="img1.jpg", storage_path="/path2", asset_type="IMAGE", file_hash="hash2")
    asset3 = Asset(user_id=user1.id, original_filename="aud1.mp3", storage_path="/path3", asset_type="AUDIO", file_hash="hash3")
    db.add_all([asset1, asset2, asset3])
    db.commit()
    
    # Verifications
    now_date = datetime.utcnow()
    past_date = now_date - timedelta(days=5)
    
    verif1 = Verification(asset_id=asset1.id, status="COMPLETED", trust_score=90.0, risk_level="LOW", started_at=now_date)
    verif2 = Verification(asset_id=asset2.id, status="FAILED", trust_score=None, risk_level=None, started_at=past_date)
    verif3 = Verification(asset_id=asset3.id, status="COMPLETED", trust_score=50.0, risk_level="HIGH", started_at=now_date)
    db.add_all([verif1, verif2, verif3])
    db.commit()
    
    # Reports
    report1 = Report(verification_id=verif1.id, report_url="/report1.json")
    db.add(report1)
    
    # Blockchain blocks
    block1 = BlockchainBlock(id=1, verification_id=verif1.id, block_hash="bh1", previous_block_hash="ph1", payload_hash="phash1")
    db.add(block1)
    db.commit()
    
    # --- User 2 Data (to test isolation) ---
    asset_u2 = Asset(user_id=user2.id, original_filename="doc_u2.pdf", storage_path="/path_u2", asset_type="PDF", file_hash="hash_u2")
    db.add(asset_u2)
    db.commit()
    verif_u2 = Verification(asset_id=asset_u2.id, status="COMPLETED", trust_score=100.0, risk_level="LOW")
    db.add(verif_u2)
    db.commit()
    
    db.close()
    return {}

# 1. Average trust score calculated correctly
def test_average_trust_score(user1_token, populate_analytics):
    res = client.get("/api/v1/analytics/dashboard", headers={"Authorization": user1_token})
    assert res.status_code == 200
    metrics = res.json()["data"]
    # User 1 has verif1 (90.0) and verif3 (50.0) -> Average is 70.0
    assert metrics["average_trust_score"] == 70.0

# 2. Completed verification count calculated correctly
def test_completed_verifications(user1_token, populate_analytics):
    res = client.get("/api/v1/analytics/dashboard", headers={"Authorization": user1_token})
    assert res.status_code == 200
    metrics = res.json()["data"]
    # User 1 has 2 COMPLETED verifications
    assert metrics["completed_verifications"] == 2

# 3. Failed verification count calculated correctly
def test_failed_verifications(user1_token, populate_analytics):
    res = client.get("/api/v1/analytics/dashboard", headers={"Authorization": user1_token})
    assert res.status_code == 200
    metrics = res.json()["data"]
    # User 1 has 1 FAILED verification
    assert metrics["failed_verifications"] == 1

# 4. Asset type counts calculated correctly
def test_asset_types_distribution(user1_token, populate_analytics):
    res = client.get("/api/v1/analytics/asset-types", headers={"Authorization": user1_token})
    assert res.status_code == 200
    data = res.json()["data"]
    # User 1 has 1 PDF, 1 IMAGE, 1 AUDIO
    assert data["PDF"] == 1
    assert data["IMAGE"] == 1
    assert data["AUDIO"] == 1

# 5. Risk distribution counts calculated correctly
def test_risk_distribution_counts(user1_token, populate_analytics):
    res = client.get("/api/v1/analytics/risk-distribution", headers={"Authorization": user1_token})
    assert res.status_code == 200
    data = res.json()["data"]
    # User 1 has 1 LOW, 0 MEDIUM, 1 HIGH
    assert data["LOW"] == 1
    assert data["MEDIUM"] == 0
    assert data["HIGH"] == 1

# 6. Response wrapper is correct
def test_response_wrapper_format(user1_token, populate_analytics):
    # Success response
    res = client.get("/api/v1/analytics/dashboard", headers={"Authorization": user1_token})
    assert res.status_code == 200
    data = res.json()
    assert "success" in data
    assert data["success"] is True
    assert "data" in data
    
    # Error response
    res_err = client.get("/api/v1/analytics/verification-trends?timeframe=invalid_123", headers={"Authorization": user1_token})
    assert res_err.status_code == 400
    err_data = res_err.json()
    assert err_data["success"] is False
    assert "error" in err_data
    assert "code" in err_data["error"]
    assert "message" in err_data["error"]
    assert "details" in err_data["error"]

# 7. User cannot see another user's analytics
def test_analytics_isolation(user1_token, user2_token, populate_analytics):
    res_u1 = client.get("/api/v1/analytics/dashboard", headers={"Authorization": user1_token})
    data_u1 = res_u1.json()["data"]
    
    res_u2 = client.get("/api/v1/analytics/dashboard", headers={"Authorization": user2_token})
    data_u2 = res_u2.json()["data"]
    
    # Assert they are different and isolated
    assert data_u1["total_assets"] == 3
    assert data_u2["total_assets"] == 1
    assert data_u1["average_trust_score"] == 70.0
    assert data_u2["average_trust_score"] == 100.0

# 8. No sensitive fields exposed
def test_no_sensitive_fields_exposed(user1_token, populate_analytics):
    endpoints = [
        "/api/v1/analytics/dashboard",
        "/api/v1/analytics/risk-distribution",
        "/api/v1/analytics/verification-trends",
        "/api/v1/analytics/asset-types"
    ]
    
    for endpoint in endpoints:
        res = client.get(endpoint, headers={"Authorization": user1_token})
        res_str = str(res.json()).lower()
        assert "storage_path" not in res_str
        assert "password_hash" not in res_str
        assert "raw_file" not in res_str
        assert "/path1" not in res_str

# 9. Verification trends returns expected timeframe
def test_verification_trends_timeframes(user1_token, populate_analytics):
    # Test 7d
    res_7d = client.get("/api/v1/analytics/verification-trends?timeframe=7d", headers={"Authorization": user1_token})
    assert res_7d.status_code == 200
    assert res_7d.json()["data"]["timeframe"] == "7d"
    
    # Test 30d
    res_30d = client.get("/api/v1/analytics/verification-trends?timeframe=30d", headers={"Authorization": user1_token})
    assert res_30d.status_code == 200
    assert res_30d.json()["data"]["timeframe"] == "30d"
    
    # Test 90d
    res_90d = client.get("/api/v1/analytics/verification-trends?timeframe=90d", headers={"Authorization": user1_token})
    assert res_90d.status_code == 200
    assert res_90d.json()["data"]["timeframe"] == "90d"
    
    # Test invalid timeframe
    res_invalid = client.get("/api/v1/analytics/verification-trends?timeframe=5d", headers={"Authorization": user1_token})
    assert res_invalid.status_code == 400
    assert res_invalid.json()["error"]["code"] == "INVALID_TIMEFRAME"

# Additional security test just in case
def test_analytics_requires_auth():
    res = client.get("/api/v1/analytics/dashboard")
    assert res.status_code == 401
