import logging
from typing import Optional, Dict, Any
from datetime import datetime

from app.schemas.hash_result import HashResult
from app.schemas.metadata import MetadataResult
from app.schemas.forensics import ForensicsResult
from app.schemas.trust_score import TrustScoreResult, RiskLevel, DocumentStatus, Penalty

logger = logging.getLogger(__name__)

def calculate_score(
    hash_evidence: Optional[HashResult],
    metadata_evidence: Optional[MetadataResult],
    forensic_evidence: Optional[ForensicsResult],
    blockchain_evidence: Optional[Dict[str, Any]] = None
) -> TrustScoreResult:
    logger.info("Trust Score calculation started")
    
    trust_score = 100.0
    confidence = 100.0
    penalties = []
    
    score_breakdown = {
        "hash_integrity": 30.0,
        "metadata_integrity": 20.0,
        "forensic_integrity": 35.0,
        "blockchain_proof": 15.0
    }
    
    # 1. Hash Evidence (30 points)
    if not hash_evidence or not hash_evidence.hash:
        penalties.append(Penalty(reason="Hash missing or invalid", points_deducted=30.0))
        trust_score -= 30.0
        score_breakdown["hash_integrity"] -= 30.0
        
    # 2. Metadata Evidence (20 points)
    if not metadata_evidence:
        penalties.append(Penalty(reason="Metadata evidence completely missing", points_deducted=20.0))
        trust_score -= 20.0
        score_breakdown["metadata_integrity"] -= 20.0
    else:
        # Check basic vs advanced metadata missing
        if not metadata_evidence.technical_metadata:
            penalty = 10.0
            penalties.append(Penalty(reason="Technical metadata missing", points_deducted=penalty))
            trust_score -= penalty
            score_breakdown["metadata_integrity"] -= penalty
            
        if metadata_evidence.warnings:
            penalty = 5.0
            penalties.append(Penalty(reason="Metadata extraction warnings present", points_deducted=penalty))
            trust_score -= penalty
            score_breakdown["metadata_integrity"] -= penalty
            
    # 3. Forensic Evidence (35 points)
    tampering_detected = False
    if not forensic_evidence:
        penalties.append(Penalty(reason="Forensic evidence completely missing", points_deducted=35.0))
        trust_score -= 35.0
        score_breakdown["forensic_integrity"] -= 35.0
        confidence -= 20.0
    else:
        if forensic_evidence.tampering_detected:
            tampering_detected = True
            penalty = 30.0
            penalties.append(Penalty(reason="Strong tampering detected", points_deducted=penalty))
            trust_score -= penalty
            score_breakdown["forensic_integrity"] -= penalty
            
        elif forensic_evidence.forensic_score < 50:
            penalty = 25.0
            penalties.append(Penalty(reason="Forensic score below 50", points_deducted=penalty))
            trust_score -= penalty
            score_breakdown["forensic_integrity"] -= penalty
            
        elif forensic_evidence.forensic_score < 80:
            penalty = 10.0
            penalties.append(Penalty(reason="Forensic score below 80", points_deducted=penalty))
            trust_score -= penalty
            score_breakdown["forensic_integrity"] -= penalty
            
        if forensic_evidence.warnings:
            penalty = 5.0
            penalties.append(Penalty(reason="Forensic warnings present", points_deducted=penalty))
            trust_score -= penalty
            score_breakdown["forensic_integrity"] -= penalty
            
        if forensic_evidence.confidence < 100:
            confidence -= (100.0 - forensic_evidence.confidence) * 0.2
            
    # 4. Blockchain Evidence (15 points)
    if not blockchain_evidence:
        penalties.append(Penalty(reason="Blockchain evidence unavailable (confidence penalty only)", points_deducted=0.0))
        confidence -= 15.0
    else:
        is_matched = blockchain_evidence.get("is_matched", False)
        if not is_matched:
            penalty = 15.0
            penalties.append(Penalty(reason="Blockchain mismatch", points_deducted=penalty))
            trust_score -= penalty
            score_breakdown["blockchain_proof"] -= penalty
            
    # Clamping
    trust_score = max(0.0, min(100.0, trust_score))
    confidence = max(0.0, min(100.0, confidence))
    
    for k in score_breakdown:
        score_breakdown[k] = max(0.0, score_breakdown[k])
        
    # Classifications
    if trust_score >= 80:
        risk_level = RiskLevel.LOW
    elif trust_score >= 50:
        risk_level = RiskLevel.MEDIUM
    else:
        risk_level = RiskLevel.HIGH
        
    if trust_score >= 80 and not tampering_detected:
        document_status = DocumentStatus.AUTHENTIC
    elif trust_score >= 50 and not tampering_detected:
        document_status = DocumentStatus.SUSPICIOUS
    else:
        document_status = DocumentStatus.UNVERIFIED
        
    logger.info(f"Trust Score calculated: {trust_score} (Risk: {risk_level}, Status: {document_status})")
    
    return TrustScoreResult(
        trust_score=trust_score,
        risk_level=risk_level,
        document_status=document_status,
        confidence=confidence,
        score_breakdown=score_breakdown,
        penalties=penalties,
        calculated_at=datetime.utcnow()
    )
