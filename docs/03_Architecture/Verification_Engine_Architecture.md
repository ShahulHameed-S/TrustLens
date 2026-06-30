# Verification Engine Architecture

## 1. Verification Engine Overview

The Verification Engine is the core intellectual property of the TrustLens Digital Trust Intelligence Platform. Its purpose is to systematically analyze digital assets to determine their authenticity, integrity, provenance, and overall trustworthiness. It acts as the central intelligence hub, orchestrating various subsystems—Digital Forensics, Cryptographic Hashing, Explainable AI, and Blockchain—into a cohesive, scalable, and deterministic pipeline. By isolating responsibilities and keeping trust scoring strictly deterministic, it ensures enterprise-grade reliability and legal defensibility for all digital asset analyses.

---

## 2. High-Level Verification Flow

The execution of a verification request follows a strict, unidirectional data flow:

```text
User Upload
      ↓
Asset Service
      ↓
Verification Engine
      ↓
Verification Pipeline Dispatcher
      ↓
Pipeline Execution (Format-Specific Analysis)
      ↓
Trust Score Engine (Deterministic Scoring)
      ↓
AI Explanation Engine (Contextual Reasoning)
      ↓
Blockchain Engine (Immutable Proof)
      ↓
Report Engine (Aggregation)
      ↓
Database (Storage)
      ↓
API Response
```

---

## 3. Verification Dispatcher

The Verification Dispatcher is the entry point of the engine. It automatically identifies the true underlying format of the asset (ignoring potentially spoofed file extensions) and routes it to the correct, specialized verification pipeline.

**Currently Supported Asset Types:**
- **PDF**: Portable Document Format files.
- **IMAGE**: JPEG, PNG, WEBP images.
- **AUDIO**: MP3, WAV, MP4 audio files.

**Future Extensibility:**
- VIDEO
- OCR Documents
- Email (EML/MSG)
- ZIP Archives

The dispatcher acts as a factory, instantiating the appropriate pipeline without exposing the internal complexity of the analysis stages to the calling service.

---

## 4. Verification Pipelines

To satisfy the Single Responsibility Principle and Extensibility, TrustLens utilizes independent pipelines for different formats:

1. **PDF Pipeline**: Specialized in analyzing document structures, fonts, embedded objects, and PDF metadata.
2. **IMAGE Pipeline**: Specialized in EXIF analysis, steganography detection, noise analysis, and error level analysis (ELA).
3. **AUDIO Pipeline**: Specialized in spectrogram analysis, frequency tampering, and audio metadata evaluation.

While the forensic logic within each pipeline is unique, **every pipeline executes identical, standardized stages** to guarantee uniform outputs.

---

## 5. Pipeline Stages

Every verification pipeline (regardless of asset type) must execute the following ten stages sequentially:

- **Stage 1: Input Validation** -> Validates file integrity, magic bytes, and sanitizes input.
- **Stage 2: SHA-256 Hash Generation** -> Computes the cryptographic hash of the asset for blockchain and integrity checks.
- **Stage 3: Metadata Extraction** -> Extracts EXIF, ID3, or document properties.
- **Stage 4: Digital Forensics Analysis** -> Executes format-specific tampering detection algorithms.
- **Stage 5: Evidence Collection** -> Normalizes all findings into the structured Evidence Model.
- **Stage 6: Trust Score Engine** -> Calculates the deterministic trust score based on the evidence.
- **Stage 7: Risk Level Classification** -> Categorizes the score into a Risk Level.
- **Stage 8: Explainable AI Engine** -> Passes evidence to the LLM to generate human-readable explanations.
- **Stage 9: Blockchain Registration / Verification** -> Registers the hash or verifies existing provenance on the blockchain.
- **Stage 10: Report Generation** -> Compiles all outputs into a final Verification Report.

---

## 6. Evidence Model

Pipelines **DO NOT** calculate or return a Trust Score. Their sole responsibility is to analyze the asset and return a standardized, objective data structure known as **Evidence**. 

**Evidence Model Schema:**
```json
{
    "hash_integrity": 100,
    "metadata_integrity": 96,
    "forensic_integrity": 91,
    "tampering_detected": false,
    "confidence": 97
}
```
This strict contract ensures that the rules for determining "Trust" are decoupled from the forensic algorithms.

---

## 7. Trust Score Engine

The Trust Score Engine is a dedicated, completely **deterministic** module. 

- **Input:** Evidence Model.
- **Output:** Trust Score (0-100) & Risk Level.
- **Rule:** The Trust Score Engine must never utilize AI, LLMs, or randomness. Given the exact same Evidence Model, it must mathematically guarantee the exact same Trust Score every time. It applies weighted algorithms to the evidence integrity values to produce the final score.

---

## 8. Risk Classification Engine

The Risk Classification Engine translates the numeric Trust Score into actionable risk intelligence using configurable thresholds. 

- **LOW Risk**: Score 80 - 100 (Asset is trustworthy and unaltered)
- **MEDIUM Risk**: Score 50 - 79 (Minor anomalies or suspicious metadata detected)
- **HIGH Risk**: Score 0 - 49 (Definite tampering, malicious indicators, or severe integrity failure)

---

## 9. Explainable AI Engine

The Explainable AI Engine bridges the gap between complex forensic data and end-user comprehension. 

- **Input:** Evidence Model + Trust Score + Risk Level
- **Output:**
```json
{
    "summary": "The image appears to be authentic with minor metadata anomalies.",
    "evidence": "Metadata integrity is at 96% due to missing GPS coordinates. Forensic integrity is 91% with no signs of pixel tampering.",
    "reasoning": "Because no active tampering was detected and hash integrity is 100%, the asset achieves a high trust score.",
    "recommendation": "Safe to process, but note the lack of location data.",
    "confidence": 97
}
```
**CRITICAL RULE:** The LLM NEVER decides the trust score. It ONLY explains the deterministic output provided to it.

---

## 10. Blockchain Engine

The Verification Engine communicates with the Blockchain Engine asynchronously to ensure immutable provenance. 

- **Hash Registration**: If the asset is new, its SHA-256 hash and timestamp are committed to the ledger.
- **Integrity Check**: If the asset exists, the engine verifies the hash against the blockchain to detect historical modifications.
- **Proof Retrieval**: Fetches the transaction ID and block confirmation details.
- **Immutable Audit Trail**: Ensures that the verification event itself is logged for cryptographic non-repudiation.

---

## 11. Report Engine

The Report Engine is the final stage, responsible for assembling all processed data into a single, cohesive artifact.

**Report Composition:**
- **Verification Summary**: ID, Asset Name, User.
- **Evidence**: The raw structured output from the pipeline.
- **Trust Score & Risk**: The deterministic evaluation.
- **Blockchain Proof**: Ledger transaction data and timestamps.
- **AI Explanation**: The JSON output from the Explainable AI Engine.
- **Metadata**: Basic file metrics (size, type).
- **Timestamp**: Exact UTC time of the completed verification.

---

## 12. Error Handling

The architecture implements a robust, fail-safe error routing mechanism:

- **Unsupported File**: Dispatcher traps the error immediately; aborts pipeline; returns `HTTP 400 Bad Request`.
- **Corrupted File**: Stage 1 (Input Validation) catches byte-level corruption; aborts pipeline; logs forensic failure.
- **Invalid Metadata**: Stage 3 gracefully degrades (returns 0 for metadata integrity); pipeline continues.
- **Verification Failure**: Internal faults (e.g., memory exhaustion during Stage 4) trigger a rollback; returns `HTTP 500`.
- **Blockchain Failure**: If the ledger is unreachable, Stage 9 degrades gracefully, marking the blockchain status as "Pending" or "Unavailable" without failing the entire verification.
- **AI Failure**: If the LLM times out, Stage 8 falls back to a deterministic, templated textual explanation based on the Risk Level; pipeline succeeds.

---

## 13. Future Scalability

This architecture is designed for infinite horizontal scalability and feature expansion without requiring structural redesigns.

- **Video Verification & Deepfake Detection**: Simply requires creating a new `VIDEO Pipeline` class implementing the standard 10 stages. The Dispatcher is updated to route video MIME types. The Trust Score Engine and AI Engine require zero changes as they consume the normalized Evidence Model.
- **OCR & Text Analysis**: Can be bolted on as an extension of the PDF or Image pipeline forensics stage.
- **Cloud Storage**: The Asset Service handles file ingestion; the verification engine consumes byte streams agnostic of whether the file lives on AWS S3, Azure Blob, or local disk.
- **Enterprise Modules**: Can be integrated by adding new stages (e.g., `Stage 4b: Custom Enterprise Policy Check`) into the pipeline interface.

---

## 14. Module Interaction Diagram

```text
+---------------------------------------------------------------------------------------------------+
|                                     Verification Engine                                           |
+---------------------------------------------------------------------------------------------------+
                                              |
                                     [ Asset Upload ]
                                              |
+---------------------------------------------------------------------------------------------------+
|                            Verification Pipeline Dispatcher                                       |
|                       (Identifies format: PDF, IMAGE, AUDIO)                                      |
+---------------------------------------------------------------------------------------------------+
           /                                  |                                  \
+---------------------+             +---------------------+             +---------------------+
|    PDF Pipeline     |             |   IMAGE Pipeline    |             |   AUDIO Pipeline    |
+---------------------+             +---------------------+             +---------------------+
| 1. Input Validation |             | 1. Input Validation |             | 1. Input Validation |
| 2. SHA-256 Hash     |             | 2. SHA-256 Hash     |             | 2. SHA-256 Hash     |
| 3. Meta Extraction  |             | 3. Meta Extraction  |             | 3. Meta Extraction  |
| 4. Digital Forensics|             | 4. Digital Forensics|             | 4. Digital Forensics|
| 5. Evidence Collect |             | 5. Evidence Collect |             | 5. Evidence Collect |
+---------------------+             +---------------------+             +---------------------+
           \                                  |                                  /
            ----------------------------------+----------------------------------
                                              |
                                      [ Evidence Model ] 
                                              |
                                              v
+---------------------------------------------------------------------------------------------------+
|                                  Trust Score Engine                                               |
|                    (Deterministic evaluation -> outputs Trust Score & Risk Level)                 |
+---------------------------------------------------------------------------------------------------+
                                              |
               +------------------------------+------------------------------+
               |                                                             |
               v                                                             v
+---------------------------------------+                  +----------------------------------------+
|      Explainable AI Engine (LLM)      |                  |          Blockchain Engine             |
|  (Reads Evidence + Score -> JSON Exp) |                  | (Registers hash, verifies integrity)   |
+---------------------------------------+                  +----------------------------------------+
               |                                                             |
               +------------------------------+------------------------------+
                                              |
                                              v
+---------------------------------------------------------------------------------------------------+
|                                      Report Engine                                                |
|            (Aggregates Score, Risk, Evidence, AI Explanation, Blockchain Proof)                   |
+---------------------------------------------------------------------------------------------------+
                                              |
                                        [ Database ]
                                      [ API Response ]
```

---

## 15. Engineering Decisions

- **Modular Monolith & Single Responsibility Principle**: Each stage and engine has a strictly defined boundary. This allows disparate teams (AI researchers, Blockchain engineers, Backend devs) to work on different stages of the pipeline simultaneously without merge conflicts or logical entanglement.
- **Deterministic Trust**: By explicitly separating the forensic evidence generation from the trust calculation, and forbidding the AI from generating the score, the system becomes legally defensible. Customers can mathematically verify why an asset scored an 85.
- **Explainable AI as an Overlay**: Using the LLM strictly as an interpreter of deterministic data prevents AI hallucinations from corrupting the core integrity verdict. It provides the UX benefits of GenAI without the reliability risks.
- **Standardized Evidence Model**: Normalizing output across all asset types means the downstream engines (Trust Score, AI, Blockchain, Report) do not need to care whether they are processing a PDF or a WAV file. This guarantees Extensibility. Adding deepfake video detection simply involves writing a new pipeline that emits the standard Evidence Model.
- **Graceful Degradation (Resilience)**: Fallbacks for AI (templated responses) and Blockchain (pending states) ensure that the core verification pipeline never stalls due to third-party network outages, ensuring Enterprise Readiness and high availability.
