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
from app.models.role import Role
from app.models.audit_log import AuditLog
from app.services.audit_log_service import AuditLogService
from app.schemas.audit_log import AuditAction

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql.expression import FunctionElement
from sqlalchemy.pool import StaticPool
from sqlalchemy import event

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
    
    role_admin = Role(name="admin", description="Administrator")
    role_user = Role(name="user", description="Normal User")
    db.add_all([role_admin, role_user])
    db.commit()
    
    user1 = User(email="user1_audit@example.com", password_hash="fakehash", is_active=True)
    user1.roles.append(role_user)
    
    user2 = User(email="user2_audit@example.com", password_hash="fakehash", is_active=True)
    user2.roles.append(role_user)
    
    admin = User(email="admin_audit@example.com", password_hash="fakehash", is_active=True)
    admin.roles.append(role_admin)
    
    db.add_all([user1, user2, admin])
    db.commit()
    
    yield
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def user1_token():
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": "user1_audit@example.com"})
    return f"Bearer {token}"

@pytest.fixture
def user2_token():
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": "user2_audit@example.com"})
    return f"Bearer {token}"

@pytest.fixture
def admin_token():
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": "admin_audit@example.com"})
    return f"Bearer {token}"

@pytest.fixture
def populate_audit_logs():
    db = TestingSessionLocal()
    db.query(AuditLog).delete()
    db.commit()
    
    user1 = db.query(User).filter(User.email == "user1_audit@example.com").first()
    user2 = db.query(User).filter(User.email == "user2_audit@example.com").first()
    
    service = AuditLogService()
    service.log_event(db, action=AuditAction.ASSET_UPLOAD, user_id=user1.id, resource_type="asset", resource_id="asset-1")
    service.log_event(db, action=AuditAction.VERIFICATION_COMPLETED, user_id=user1.id, resource_type="verification", resource_id="verif-1")
    service.log_event(db, action=AuditAction.REPORT_GENERATED, user_id=user1.id, resource_type="report", resource_id="report-1")
    
    service.log_event(db, action=AuditAction.ASSET_UPLOAD, user_id=user2.id, resource_type="asset", resource_id="asset-2")
    service.log_event(db, action=AuditAction.ASSET_DELETE, user_id=user2.id, resource_type="asset", resource_id="asset-2")
    
    db.close()
    return {}

def test_list_audit_logs_user1(user1_token, populate_audit_logs):
    res = client.get("/api/v1/audit-logs", headers={"Authorization": user1_token})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total"] == 3
    assert len(data["items"]) == 3
    for item in data["items"]:
        assert item["resource_id"] in ["asset-1", "verif-1", "report-1"]

def test_list_audit_logs_user2(user2_token, populate_audit_logs):
    res = client.get("/api/v1/audit-logs", headers={"Authorization": user2_token})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total"] == 2
    assert len(data["items"]) == 2
    for item in data["items"]:
        assert item["resource_id"] == "asset-2"

def test_list_audit_logs_admin(admin_token, populate_audit_logs):
    res = client.get("/api/v1/audit-logs", headers={"Authorization": admin_token})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total"] == 5
    assert len(data["items"]) == 5

def test_get_audit_log_user1(user1_token, populate_audit_logs):
    res_list = client.get("/api/v1/audit-logs", headers={"Authorization": user1_token})
    log_id = res_list.json()["data"]["items"][0]["id"]
    
    res = client.get(f"/api/v1/audit-logs/{log_id}", headers={"Authorization": user1_token})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["id"] == log_id

def test_get_audit_log_forbidden(user1_token, user2_token, populate_audit_logs):
    res_list = client.get("/api/v1/audit-logs", headers={"Authorization": user1_token})
    log_id = res_list.json()["data"]["items"][0]["id"]
    
    res = client.get(f"/api/v1/audit-logs/{log_id}", headers={"Authorization": user2_token})
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"

def test_get_audit_log_not_found(user1_token, populate_audit_logs):
    fake_uuid = str(uuid.uuid4())
    res = client.get(f"/api/v1/audit-logs/{fake_uuid}", headers={"Authorization": user1_token})
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "AUDIT_LOG_NOT_FOUND"

def test_protected_endpoints():
    res = client.get("/api/v1/audit-logs")
    assert res.status_code == 401

def test_response_format_and_secrets(user1_token, populate_audit_logs):
    res = client.get("/api/v1/audit-logs", headers={"Authorization": user1_token})
    res_str = str(res.json()).lower()
    
    assert res.json()["success"] is True
    assert "data" in res.json()
    assert "items" in res.json()["data"]
    
    # Assert no secrets
    assert "password_hash" not in res_str
    assert "storage_path" not in res_str
    assert "raw_file" not in res_str
    assert "token" not in res_str
    assert "password" not in res_str
    assert "access_token" not in res_str
    assert "refresh_token" not in res_str
    assert "\\" not in res_str  # rough check for internal windows paths
    assert "d:" not in res_str

def test_pagination(admin_token, populate_audit_logs):
    res = client.get("/api/v1/audit-logs?page=1&limit=2", headers={"Authorization": admin_token})
    data = res.json()["data"]
    assert len(data["items"]) == 2
    assert data["total"] == 5
    assert data["total_pages"] == 3

def test_auth_audit_integration():
    # Register
    email = f"newuser_{uuid.uuid4()}@example.com"
    res = client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "Password123!",
        "full_name": "New User"
    })
    assert res.status_code == 200
    user_id = res.json()["data"]["id"]
    
    # Login
    res_login = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Password123!"
    })
    assert res_login.status_code == 200
    token = res_login.json()["data"]["access_token"]
    
    # Logout
    res_logout = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert res_logout.status_code == 200
    
    # Check Audit Logs as Admin
    db = TestingSessionLocal()
    admin = db.query(User).filter(User.email == "admin_audit@example.com").first()
    from app.core.security import create_access_token
    admin_tok = create_access_token(data={"sub": admin.email})
    db.close()
    
    res_audit = client.get("/api/v1/audit-logs", headers={"Authorization": f"Bearer {admin_tok}"})
    assert res_audit.status_code == 200
    logs = res_audit.json()["data"]["items"]
    
    actions = [log["action"] for log in logs if log["user_id"] == user_id]
    assert "AUTH_REGISTER" in actions
    assert "AUTH_LOGIN" in actions
    assert "AUTH_LOGOUT" in actions
    
    # Ensure no secrets
    res_str = str(res_audit.json()).lower()
    assert "password_hash" not in res_str
    assert "token" not in res_str

def test_blockchain_audit_integration(admin_token):
    # Call blockchain validate
    res = client.get("/api/v1/blockchain/validate", headers={"Authorization": admin_token})
    # Might be 200 or 400 depending on chain validity, but it should log either way
    
    res_audit = client.get("/api/v1/audit-logs", headers={"Authorization": admin_token})
    logs = res_audit.json()["data"]["items"]
    
    actions = [log["action"] for log in logs]
    assert "BLOCKCHAIN_VALIDATED" in actions

def test_full_workflow_audit_integration(user1_token, admin_token):
    # 1. ASSET_UPLOAD
    with open("test_dummy.pdf", "wb") as f:
        f.write(b"dummy pdf content")
        
    with open("test_dummy.pdf", "rb") as f:
        res_upload = client.post(
            "/api/v1/assets/upload", 
            headers={"Authorization": user1_token},
            files={"file": ("test_dummy.pdf", f, "application/pdf")}
        )
    assert res_upload.status_code == 200
    asset_id = res_upload.json()["data"]["asset_id"]
    
    # 2. VERIFICATION_STARTED & VERIFICATION_COMPLETED
    # A valid PDF upload triggers both if we don't break it
    res_verify = client.post(
        "/api/v1/verifications/pdf", 
        json={"asset_id": str(asset_id), "register_to_blockchain": False, "generate_report": True}, 
        headers={"Authorization": user1_token}
    )
    assert res_verify.status_code == 200, res_verify.text
    verification_id = res_verify.json()["data"]["verification_id"]
    
    # 3. REPORT_GENERATED
    res_report = client.post(f"/api/v1/reports/generate/{verification_id}", headers={"Authorization": user1_token})
    assert res_report.status_code == 200, res_report.text
    
    # 4. ASSET_DELETE
    res_delete = client.delete(f"/api/v1/assets/{asset_id}", headers={"Authorization": user1_token})
    assert res_delete.status_code == 200
    
    # Check logs as admin
    res_audit = client.get("/api/v1/audit-logs", headers={"Authorization": admin_token})
    logs = res_audit.json()["data"]["items"]
    actions = [log["action"] for log in logs if log["resource_id"] in [asset_id, verification_id] or log["resource_id"] is not None]
    
    assert "ASSET_UPLOAD" in actions
    assert "VERIFICATION_STARTED" in actions
    assert "VERIFICATION_COMPLETED" in actions
    assert "REPORT_GENERATED" in actions
    assert "ASSET_DELETE" in actions
    
    # Cleanup
    if os.path.exists("test_dummy.pdf"):
        os.remove("test_dummy.pdf")

def test_verification_failed_audit(user1_token, admin_token, monkeypatch):
    # Upload asset
    with open("test_fail.pdf", "wb") as f:
        f.write(b"dummy fail content")
        
    with open("test_fail.pdf", "rb") as f:
        res_upload = client.post(
            "/api/v1/assets/upload", 
            headers={"Authorization": user1_token},
            files={"file": ("test_fail.pdf", f, "application/pdf")}
        )
    asset_id = res_upload.json()["data"]["asset_id"]
    # We do not get storage_path in AssetUploadData response!
    # Instead, let's fetch the asset from the DB to get storage_path.
    db = TestingSessionLocal()
    from app.models.asset import Asset
    asset_uuid = uuid.UUID(asset_id)
    asset = db.query(Asset).filter(Asset.id == asset_uuid).first()
    storage_path = asset.storage_path
    db.close()
    
    # Force failure by mocking HashEngine to raise an exception AFTER verification record is created
    def mock_calc_hash(*args, **kwargs):
        raise Exception("Simulated Hash Failure")
        
    from app.services.hash_engine import HashEngine
    monkeypatch.setattr(HashEngine, "calculate_sha256", mock_calc_hash)
        
    res_verify = client.post("/api/v1/verifications/pdf", json={"asset_id": str(asset_id), "register_to_blockchain": False}, headers={"Authorization": user1_token})
    # Since hash engine fails, verify will fail
    assert res_verify.json()["success"] is False
    
    res_audit = client.get("/api/v1/audit-logs", headers={"Authorization": admin_token})
    logs = res_audit.json()["data"]["items"]
    
    fail_logs = [log for log in logs if log["action"] == "VERIFICATION_FAILED"]
    assert len(fail_logs) > 0
    
    # Ensure no raw exception stack trace is logged in resource_id or action
    for log in fail_logs:
        assert "stack trace" not in str(log).lower()
        assert "file missing" not in str(log["resource_id"]).lower()
    
    # Cleanup
    if os.path.exists("test_fail.pdf"):
        os.remove("test_fail.pdf")

def test_audit_logging_failure_swallowed(user1_token, monkeypatch):
    # Mock AuditLogRepository.create_log to raise an exception
    def mock_create_log(*args, **kwargs):
        raise Exception("Simulated DB Failure")
        
    from app.repositories.audit_log_repository import AuditLogRepository
    monkeypatch.setattr(AuditLogRepository, "create_log", mock_create_log)
    
    # Execute main operation (logout)
    res_logout = client.post("/api/v1/auth/logout", headers={"Authorization": user1_token})
    
    # Assert main operation still succeeds!
    assert res_logout.status_code == 200
    assert res_logout.json()["success"] is True
