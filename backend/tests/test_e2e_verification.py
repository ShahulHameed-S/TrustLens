import pytest
from fastapi.testclient import TestClient
import os
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database.session import get_db
from app.database.base import Base
from app.models.user import User
from app.models.role import Role
from app.models.asset import Asset
from app.models.asset_metadata import AssetMetadata
from app.models.verification import Verification
from app.models.ai_analysis import AIAnalysis
from app.models.blockchain_block import BlockchainBlock
from app.models.report import Report
from app.models.audit_log import AuditLog

# Setup SQLite in-memory database
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
    # SQLite doesn't have UUID, so we can just use a dummy string or random hex
    # For a server_default, hex(randomblob(16)) works in sqlite to generate a 32-char hex string
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
    yield
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)

def test_full_verification_flow():
    # 1. Create a user
    unique_id = uuid.uuid4().hex[:8]
    user_email = f"e2e_{unique_id}@example.com"
    user_pwd = "password123"
    
    reg_resp = client.post("/api/v1/auth/register", json={
        "email": user_email,
        "password": user_pwd,
        "full_name": "E2E Tester"
    })
    assert reg_resp.status_code == 200
    
    # 2. Login
    login_resp = client.post("/api/v1/auth/login", json={
        "email": user_email,
        "password": user_pwd
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["data"]["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Upload an asset
    # Create a dummy PDF file
    test_pdf_path = f"test_asset_{unique_id}.pdf"
    with open(test_pdf_path, "wb") as f:
        f.write(b"%PDF-1.4\n%E2E Test File\n")
        
    try:
        with open(test_pdf_path, "rb") as f:
            upload_resp = client.post("/api/v1/assets/upload", files={"file": ("test.pdf", f, "application/pdf")}, headers=headers)
    
        assert upload_resp.status_code == 200
        asset_id = upload_resp.json()["data"]["asset_id"]
    
        # 4. Trigger Verification
        verify_resp = client.post("/api/v1/verifications/pdf", json={
            "asset_id": asset_id,
            "register_to_blockchain": False,
            "generate_report": True
        }, headers=headers)
        if verify_resp.status_code != 200:
            print("VERIFY ERROR:", verify_resp.json())
        assert verify_resp.status_code == 200
        verification_id = verify_resp.json()["data"]["verification_id"]
        
        # 5. Fetch Verification Report
        report_resp = client.get(f"/api/v1/verifications/{verification_id}/report", headers=headers)
        assert report_resp.status_code == 200
        report_data = report_resp.json()["data"]
        
        # Basic checks on report data
        assert "report_url" in report_data
        assert "generated_at" in report_data
        
        # 5. List verifications
        list_resp = client.get("/api/v1/verifications", headers=headers)
        assert list_resp.status_code == 200
        assert len(list_resp.json()["data"]) >= 1
    
    finally:
        if os.path.exists(test_pdf_path):
            os.remove(test_pdf_path)
