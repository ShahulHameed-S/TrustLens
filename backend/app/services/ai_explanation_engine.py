import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime

from app.schemas.hash_result import HashResult
from app.schemas.metadata import MetadataResult
from app.schemas.forensics import ForensicsResult
from app.schemas.trust_score import TrustScoreResult, RiskLevel, DocumentStatus
from app.schemas.ai_explanation import AIExplanationResult, ExplanationMode

logger = logging.getLogger(__name__)

class ExplanationProvider(ABC):
    @abstractmethod
    def generate_explanation(
        self,
        hash_evidence: Optional[HashResult],
        metadata_evidence: Optional[MetadataResult],
        forensic_evidence: Optional[ForensicsResult],
        trust_score_result: TrustScoreResult,
        blockchain_evidence: Optional[Dict[str, Any]] = None
    ) -> AIExplanationResult:
        pass

class RuleBasedExplanationProvider(ExplanationProvider):
    def generate_explanation(
        self,
        hash_evidence: Optional[HashResult],
        metadata_evidence: Optional[MetadataResult],
        forensic_evidence: Optional[ForensicsResult],
        trust_score_result: TrustScoreResult,
        blockchain_evidence: Optional[Dict[str, Any]] = None
    ) -> AIExplanationResult:
        warnings = []
        evidence_list = []
        
        # Summary
        if trust_score_result.document_status == DocumentStatus.AUTHENTIC:
            summary = "The asset appears authentic based on strong hash integrity, low forensic risk, and consistent metadata."
        elif trust_score_result.document_status == DocumentStatus.SUSPICIOUS:
            summary = "The asset shows some suspicious indicators and should be reviewed before being trusted."
        else:
            summary = "The asset cannot be trusted because strong tampering or integrity issues were detected."
            
        # Recommendation
        if trust_score_result.risk_level == RiskLevel.LOW:
            recommendation = "Asset can be accepted with normal confidence."
        elif trust_score_result.risk_level == RiskLevel.MEDIUM:
            recommendation = "Review the forensic findings before accepting this asset."
        else:
            recommendation = "Do not trust this asset without manual verification."
            
        if blockchain_evidence is None:
            recommendation += " Blockchain proof was not available, but this does not confirm tampering."
        elif not blockchain_evidence.get("is_matched", False):
            recommendation += " A blockchain mismatch was detected, which is a serious integrity concern."

        # Evidence List
        if not hash_evidence:
            evidence_list.append("Hash evidence is unavailable.")
        else:
            evidence_list.append(f"Hash verified using {hash_evidence.algorithm}.")
            
        if not metadata_evidence:
            evidence_list.append("Metadata evidence is unavailable.")
        elif metadata_evidence.warnings:
            evidence_list.append("Metadata extraction completed with warnings.")
        else:
            evidence_list.append("Metadata successfully extracted and parsed.")
            
        if not forensic_evidence:
            evidence_list.append("Forensic evidence is unavailable.")
        elif forensic_evidence.tampering_detected:
            evidence_list.append("Forensic analysis detected strong signs of tampering.")
        elif forensic_evidence.findings:
            evidence_list.append(f"Forensic analysis produced {len(forensic_evidence.findings)} findings of interest.")
        else:
            evidence_list.append("Forensic analysis revealed no structural concerns.")
            
        if not blockchain_evidence:
            evidence_list.append("Blockchain evidence is unavailable.")
        elif blockchain_evidence.get("is_matched", False):
            evidence_list.append("Blockchain record matched the asset.")
        else:
            evidence_list.append("Blockchain record did NOT match the asset.")
            
        # Reasoning
        reasoning_parts = []
        if trust_score_result.document_status == DocumentStatus.AUTHENTIC:
            reasoning_parts.append(f"The asset achieved a high trust score ({trust_score_result.trust_score}).")
        else:
            reasoning_parts.append(f"The asset achieved a score of {trust_score_result.trust_score} out of 100.")
            
        if trust_score_result.penalties:
            penalty_reasons = [p.reason for p in trust_score_result.penalties]
            reasoning_parts.append(f"The following penalties affected the score: {', '.join(penalty_reasons)}.")
        else:
            reasoning_parts.append("No integrity penalties were applied during the verification process.")
            
        reasoning = " ".join(reasoning_parts)
        
        return AIExplanationResult(
            summary=summary,
            evidence=evidence_list,
            reasoning=reasoning,
            recommendation=recommendation.strip(),
            confidence=100.0,
            generated_at=datetime.utcnow(),
            model_name="RuleBased-v1.0",
            explanation_mode=ExplanationMode.RULE_BASED,
            warnings=warnings
        )

class LocalLLMExplanationProvider(ExplanationProvider):
    def generate_explanation(
        self,
        hash_evidence: Optional[HashResult],
        metadata_evidence: Optional[MetadataResult],
        forensic_evidence: Optional[ForensicsResult],
        trust_score_result: TrustScoreResult,
        blockchain_evidence: Optional[Dict[str, Any]] = None
    ) -> AIExplanationResult:
        # Placeholder for v1.0
        raise NotImplementedError("Local LLM provider not fully implemented in v1.0.")

class AIExplanationEngine:
    def __init__(self, use_llm: bool = False):
        self.use_llm = use_llm
        if self.use_llm:
            logger.warning("Local LLM provider requested but not fully implemented in v1.0. Falling back to Rule-Based provider.")
            self.provider = RuleBasedExplanationProvider()
        else:
            self.provider = RuleBasedExplanationProvider()
            
    def generate_explanation(
        self,
        hash_evidence: Optional[HashResult],
        metadata_evidence: Optional[MetadataResult],
        forensic_evidence: Optional[ForensicsResult],
        trust_score_result: TrustScoreResult,
        blockchain_evidence: Optional[Dict[str, Any]] = None
    ) -> AIExplanationResult:
        logger.info("AI Explanation Engine started")
        
        try:
            result = self.provider.generate_explanation(
                hash_evidence,
                metadata_evidence,
                forensic_evidence,
                trust_score_result,
                blockchain_evidence
            )
            logger.info("AI Explanation generated successfully")
            return result
        except Exception as e:
            logger.error(f"Explanation Engine failed: {str(e)}")
            return AIExplanationResult(
                summary="An error occurred while generating the explanation.",
                evidence=[],
                reasoning="The system was unable to parse the evidence due to an internal fault.",
                recommendation="Please review the raw scores and evidence manually.",
                confidence=0.0,
                generated_at=datetime.utcnow(),
                model_name="Fallback",
                explanation_mode=ExplanationMode.FALLBACK,
                warnings=[str(e)]
            )
