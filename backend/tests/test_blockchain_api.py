import pytest
from fastapi.testclient import TestClient
import uuid
import hashlib
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database.session import get_db
from app.database.base import Base
from app.models.user import User
from app.models.role import Role
from app.services.blockchain_engine import BlockchainEngine

from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql.expression import FunctionElement
from sqlalchemy import BigInteger

@compiles(JSONB, 'sqlite')
def compile_jsonb_sqlite(type_, compiler, **kw):
    return "JSON"

@compiles(BigInteger, 'sqlite')
def compile_bigint_sqlite(type_, compiler, **kw):
    return "INTEGER"

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
    
    # Add an admin role
    admin_role = Role(name="admin", description="Admin Role")
    db.add(admin_role)
    db.commit()
    
    # Create an admin user
    admin_user = User(
        email="admin@example.com",
        password_hash="fakehash",
        is_active=True
    )
    admin_user.roles.append(admin_role)
    db.add(admin_user)
    
    # Create a normal user
    normal_user = User(
        email="user@example.com",
        password_hash="fakehash",
        is_active=True
    )
    db.add(normal_user)
    db.commit()
    
    yield
    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def admin_token():
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": "admin@example.com"})
    return f"Bearer {token}"

@pytest.fixture
def user_token():
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": "user@example.com"})
    return f"Bearer {token}"

@pytest.fixture
def populate_blockchain():
    db = TestingSessionLocal()
    engine = BlockchainEngine()
    
    # clear existing blocks for fresh test if needed
    from app.models.blockchain_block import BlockchainBlock
    db.query(BlockchainBlock).delete()
    db.commit()
    
    blocks = []
    for i in range(5):
        payload_hash = hashlib.sha256(f"test_payload_{i}".encode()).hexdigest()
        proof = engine.register_hash(db, payload_hash)
        blocks.append(proof)
        
    db.close()
    return blocks

def test_blockchain_list_blocks(user_token, populate_blockchain):
    res = client.get("/api/v1/blockchain", headers={"Authorization": user_token})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["total"] >= 5
    assert len(data["data"]["items"]) >= 5
    assert "payload_hash" in data["data"]["items"][0]

def test_blockchain_pagination(user_token, populate_blockchain):
    res = client.get("/api/v1/blockchain?page=1&limit=2", headers={"Authorization": user_token})
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["limit"] == 2

def test_blockchain_get_block_by_id(user_token, populate_blockchain):
    block_id = populate_blockchain[0].block_id
    res = client.get(f"/api/v1/blockchain/blocks/{block_id}", headers={"Authorization": user_token})
    assert res.status_code == 200
    assert res.json()["success"] is True
    assert res.json()["data"]["id"] == block_id

def test_blockchain_get_block_not_found(user_token):
    res = client.get("/api/v1/blockchain/blocks/99999", headers={"Authorization": user_token})
    assert res.status_code == 404
    assert res.json()["success"] is False
    assert res.json()["error"]["code"] == "BLOCK_NOT_FOUND"

def test_blockchain_search_by_payload_hash(user_token, populate_blockchain):
    phash = populate_blockchain[0].payload_hash
    res = client.get(f"/api/v1/blockchain/hash/{phash}", headers={"Authorization": user_token})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["type"] == "proof"
    assert data["data"]["proof"]["payload_hash"] == phash

def test_blockchain_search_by_block_hash(user_token, populate_blockchain):
    bhash = populate_blockchain[1].block_hash
    res = client.get(f"/api/v1/blockchain/hash/{bhash}", headers={"Authorization": user_token})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["type"] == "block"
    assert data["data"]["block"]["block_hash"] == bhash

def test_blockchain_invalid_hash(user_token):
    res = client.get("/api/v1/blockchain/hash/invalidhash", headers={"Authorization": user_token})
    assert res.status_code == 400
    assert res.json()["success"] is False
    assert res.json()["error"]["code"] == "INVALID_HASH"

def test_blockchain_hash_not_found(user_token):
    fake_hash = hashlib.sha256(b"fake").hexdigest()
    res = client.get(f"/api/v1/blockchain/hash/{fake_hash}", headers={"Authorization": user_token})
    assert res.status_code == 404
    assert res.json()["success"] is False
    assert res.json()["error"]["code"] == "HASH_NOT_FOUND"

def test_blockchain_validate_admin_only(user_token):
    res = client.get("/api/v1/blockchain/validate", headers={"Authorization": user_token})
    assert res.status_code == 403

def test_blockchain_validate_success(admin_token, populate_blockchain):
    res = client.get("/api/v1/blockchain/validate", headers={"Authorization": admin_token})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["blockchain_valid"] is True
    assert data["data"]["total_blocks"] >= 5

def test_blockchain_requires_jwt():
    res = client.get("/api/v1/blockchain")
    assert res.status_code == 401

def test_blockchain_validate_empty_chain():
    # To test empty chain, we can just instantiate a new clean DB context or clear the blocks
    db = TestingSessionLocal()
    from app.models.blockchain_block import BlockchainBlock
    db.query(BlockchainBlock).delete()
    db.commit()
    
    # Needs admin token
    from app.core.security import create_access_token
    token = create_access_token(data={"sub": "admin@example.com"})
    admin_token = f"Bearer {token}"
    
    res = client.get("/api/v1/blockchain/validate", headers={"Authorization": admin_token})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["data"]["blockchain_valid"] is True
    assert data["data"]["total_blocks"] == 0
    db.close()

def test_explicit_success_response_wrapper(user_token, populate_blockchain):
    res = client.get("/api/v1/blockchain?page=1&limit=1", headers={"Authorization": user_token})
    data = res.json()
    assert "success" in data
    assert data["success"] is True
    assert "data" in data
    assert isinstance(data["data"], dict)
    
def test_explicit_error_response_wrapper(user_token):
    res = client.get("/api/v1/blockchain/hash/invalid", headers={"Authorization": user_token})
    data = res.json()
    assert "success" in data
    assert data["success"] is False
    assert "error" in data
    assert "code" in data["error"]
    assert "message" in data["error"]
    assert "details" in data["error"]

def test_no_sensitive_exposure(user_token, populate_blockchain):
    res = client.get("/api/v1/blockchain", headers={"Authorization": user_token})
    data = res.json()
    items = data["data"]["items"]
    assert len(items) > 0
    
    for item in items:
        # Check standard properties
        item_str = str(item).lower()
        assert "storage_path" not in item_str
        assert "raw_file_content" not in item_str
        assert "password_hash" not in item_str

def test_validation_is_read_only(admin_token, populate_blockchain):
    # Capture state before
    res_before = client.get("/api/v1/blockchain", headers={"Authorization": admin_token})
    data_before = res_before.json()
    count_before = data_before["data"]["total"]
    hashes_before = [b["block_hash"] for b in data_before["data"]["items"]]
    
    # Call validation
    validate_res = client.get("/api/v1/blockchain/validate", headers={"Authorization": admin_token})
    assert validate_res.status_code == 200
    
    # Capture state after
    res_after = client.get("/api/v1/blockchain", headers={"Authorization": admin_token})
    data_after = res_after.json()
    count_after = data_after["data"]["total"]
    hashes_after = [b["block_hash"] for b in data_after["data"]["items"]]
    
    # Assert identical
    assert count_before == count_after
    assert hashes_before == hashes_after

