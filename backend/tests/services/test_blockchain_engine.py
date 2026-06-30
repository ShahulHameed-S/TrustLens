import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import hashlib

from app.database.base import Base
# Ensure the model is imported before Base.metadata.create_all
from app.models.blockchain_block import BlockchainBlock
from app.services.blockchain_engine import BlockchainEngine
from app.schemas.blockchain import BlockchainValidationResult

# In-memory database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    # Only create the BlockchainBlock table to avoid PostgreSQL specific types like JSONB failing on SQLite
    # SQLite requires Integer for autoincrement, not BigInteger
    from sqlalchemy import Integer
    BlockchainBlock.__table__.columns['id'].type = Integer()
    
    BlockchainBlock.__table__.create(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        BlockchainBlock.__table__.drop(bind=engine)

@pytest.fixture
def blockchain_engine():
    return BlockchainEngine()

def valid_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

def test_register_first_block(db: Session, blockchain_engine: BlockchainEngine):
    payload_hash = valid_hash("payload1")
    proof = blockchain_engine.register_hash(db, payload_hash)
    
    assert proof.registered is True
    assert proof.previous_block_hash == "0"
    assert proof.payload_hash == payload_hash
    assert proof.block_id is not None

def test_first_block_previous_hash_is_zero(db: Session, blockchain_engine: BlockchainEngine):
    payload_hash = valid_hash("payload1")
    proof = blockchain_engine.register_hash(db, payload_hash)
    
    assert proof.previous_block_hash == "0"

def test_register_second_block(db: Session, blockchain_engine: BlockchainEngine):
    payload_hash_1 = valid_hash("payload1")
    proof_1 = blockchain_engine.register_hash(db, payload_hash_1)
    
    payload_hash_2 = valid_hash("payload2")
    proof_2 = blockchain_engine.register_hash(db, payload_hash_2)
    
    assert proof_2.previous_block_hash == proof_1.block_hash
    assert proof_2.block_id > proof_1.block_id

def test_block_hash_is_deterministic(db: Session, blockchain_engine: BlockchainEngine):
    payload_hash = valid_hash("test_payload")
    
    from datetime import datetime, timezone
    ts = datetime(2023, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    
    hash1 = blockchain_engine.generate_block_hash(payload_hash, "0", ts, None)
    hash2 = blockchain_engine.generate_block_hash(payload_hash, "0", ts, None)
    
    assert hash1 == hash2

def test_invalid_payload_hash_is_rejected(db: Session, blockchain_engine: BlockchainEngine):
    with pytest.raises(ValueError, match="payload_hash must be a valid SHA-256"):
        blockchain_engine.register_hash(db, "invalid_hash_string")

def test_get_block_by_id(db: Session, blockchain_engine: BlockchainEngine):
    payload_hash = valid_hash("payload1")
    proof = blockchain_engine.register_hash(db, payload_hash)
    
    block = blockchain_engine.get_block_by_id(db, proof.block_id)
    assert block is not None
    assert block.id == proof.block_id
    assert block.block_hash == proof.block_hash

def test_get_block_by_block_hash(db: Session, blockchain_engine: BlockchainEngine):
    payload_hash = valid_hash("payload1")
    proof = blockchain_engine.register_hash(db, payload_hash)
    
    block = blockchain_engine.get_block_by_hash(db, proof.block_hash)
    assert block is not None
    assert block.id == proof.block_id

def test_get_block_by_payload_hash(db: Session, blockchain_engine: BlockchainEngine):
    payload_hash = valid_hash("payload1")
    proof = blockchain_engine.register_hash(db, payload_hash)
    
    block = blockchain_engine.get_block_by_payload_hash(db, payload_hash)
    assert block is not None
    assert block.id == proof.block_id

def test_validate_empty_chain(db: Session, blockchain_engine: BlockchainEngine):
    result = blockchain_engine.validate_chain(db)
    assert result.blockchain_valid is True
    assert result.total_blocks == 0
    assert result.broken_block is None

def test_validate_valid_chain(db: Session, blockchain_engine: BlockchainEngine):
    blockchain_engine.register_hash(db, valid_hash("p1"))
    blockchain_engine.register_hash(db, valid_hash("p2"))
    blockchain_engine.register_hash(db, valid_hash("p3"))
    
    result = blockchain_engine.validate_chain(db)
    assert result.blockchain_valid is True
    assert result.total_blocks == 3
    assert result.broken_block is None

def test_detect_broken_previous_hash(db: Session, blockchain_engine: BlockchainEngine):
    proof1 = blockchain_engine.register_hash(db, valid_hash("p1"))
    proof2 = blockchain_engine.register_hash(db, valid_hash("p2"))
    
    # Tamper with the database
    block2 = blockchain_engine.get_block_by_id(db, proof2.block_id)
    block2.previous_block_hash = valid_hash("tampered")
    db.commit()
    
    result = blockchain_engine.validate_chain(db)
    assert result.blockchain_valid is False
    assert result.broken_block == proof2.block_id
    assert "Previous hash mismatch" in result.message

def test_detect_tampered_block_hash(db: Session, blockchain_engine: BlockchainEngine):
    proof1 = blockchain_engine.register_hash(db, valid_hash("p1"))
    
    # Tamper with the payload, so recalculated hash won't match stored block_hash
    block1 = blockchain_engine.get_block_by_id(db, proof1.block_id)
    block1.payload_hash = valid_hash("tampered")
    db.commit()
    
    result = blockchain_engine.validate_chain(db)
    assert result.blockchain_valid is False
    assert result.broken_block == proof1.block_id
    assert "Block hash mismatch" in result.message

def test_validation_returns_broken_block_when_chain_is_invalid(db: Session, blockchain_engine: BlockchainEngine):
    proof1 = blockchain_engine.register_hash(db, valid_hash("p1"))
    proof2 = blockchain_engine.register_hash(db, valid_hash("p2"))
    proof3 = blockchain_engine.register_hash(db, valid_hash("p3"))
    
    # Tamper block 2
    block2 = blockchain_engine.get_block_by_id(db, proof2.block_id)
    block2.previous_block_hash = valid_hash("tampered")
    db.commit()
    
    result = blockchain_engine.validate_chain(db)
    assert result.blockchain_valid is False
    assert result.broken_block == proof2.block_id

def test_no_ai_imports():
    import pathlib
    import re
    engine_file = pathlib.Path("app/services/blockchain_engine.py")
    content = engine_file.read_text()
    # Check for direct AI module imports instead of just 'ai' substring
    assert not re.search(r'import.* openai', content)
    assert not re.search(r'import.* anthropic', content)
    assert not re.search(r'import.* ai', content)
    assert not re.search(r'from ai_.* import', content)

def test_no_file_system_access():
    import pathlib
    engine_file = pathlib.Path("app/services/blockchain_engine.py")
    content = engine_file.read_text()
    assert "open(" not in content
    assert "pathlib" not in content
    assert "os." not in content
