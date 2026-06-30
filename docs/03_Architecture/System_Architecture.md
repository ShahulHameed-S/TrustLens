# TrustLens: System Architecture

## 1. Architecture Overview
TrustLens is a Digital Trust Intelligence Platform designed to verify the authenticity, integrity, provenance, and trustworthiness of digital assets (documents, images, and audio). The architecture integrates Explainable AI, Digital Forensics, Cryptographic Hashing, and Blockchain Technology into a cohesive, high-performance system. The platform is engineered to ingest digital assets, process them through multiple deterministic and AI-driven analysis engines, and deliver clear, actionable trust metrics and reports.

## 2. Architecture Style: Modular Monolith
For Version 1.0, TrustLens adopts a **Modular Monolith** architecture. While the system operates as a single deployable unit, its internal structure is strictly partitioned into distinct, logically separated modules (e.g., Verification Engine, Blockchain Engine, AI Intelligence Engine). Each module encapsulates its own domain logic and communicates with other modules through well-defined internal interfaces.

## 3. Why Modular Monolith is Chosen for TrustLens v1.0
*   **Speed of Development:** Reduces the overhead of managing distributed infrastructure, allowing for rapid iteration and feature delivery.
*   **Simplified Operations:** A single deployment unit simplifies CI/CD pipelines, logging, tracing, and monitoring.
*   **Performance:** In-memory method calls between modules are significantly faster than network hops required in microservices.
*   **Clear Boundaries:** Enforcing strict modular boundaries sets a strong foundation for an eventual transition to microservices when scaling demands it.
*   **Reduced Complexity:** Avoids the complexities of distributed data management, eventual consistency, and network partitions during the crucial initial launch phase.

## 4. High-Level System Diagram

```text
+-------------------------------------------------------------+
|                        Client Layer                         |
|  [ Web Browser (React UI) ]     [ RESTful API Clients ]     |
+------------------------------+------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                       API Gateway / LB                      |
+------------------------------+------------------------------+
                               |
+-------------------------------------------------------------+
|                TrustLens Modular Monolith (FastAPI)         |
|                                                             |
|  +---------------+  +---------------+  +---------------+    |
|  |    Auth &     |  | Verification  |  | AI & Forensics|    |
|  |  User Mgmt    |  |    Engine     |  |    Engines    |    |
|  +-------+-------+  +-------+-------+  +-------+-------+    |
|          |                  |                  |            |
|  +-------+-------+  +-------+-------+  +-------+-------+    |
|  |  Blockchain   |  |   Analytics   |  |    Report     |    |
|  |    Engine     |  |    Engine     |  |  Generation   |    |
|  +---------------+  +---------------+  +---------------+    |
+------------------------------+------------------------------+
                               |
      +------------------------+------------------------+
      |                        |                        |
      v                        v                        v
+------------+          +------------+          +------------+
| PostgreSQL |          | Local Disk |          |  External  |
| (Database) |          | (Storage)  |          | LLM (Qwen) |
+------------+          +------------+          +------------+
```

## 5. Core System Modules

*   **Authentication Module:** Manages secure user access, JWT token issuance, session validation, and API key authentication.
*   **User Management Module:** Handles user profiles, role-based access controls (RBAC), and user-specific configurations.
*   **Verification Engine:** The central orchestrator that guides a digital asset through the multi-stage verification pipeline, coordinating inputs and outputs across other engines.
*   **AI Intelligence Engine:** Integrates with the LLM to process deterministic forensic data and generate human-readable, explainable AI reports.
*   **Digital Forensics Engine:** Performs deterministic analysis on assets, extracting metadata, calculating structural anomalies, and analyzing pixel/audio data for signs of tampering.
*   **Blockchain Engine:** Manages cryptographic hashing of assets and validates or anchors these hashes against a cryptographic ledger for proof of existence.
*   **Analytics Engine:** Aggregates verification statistics, system usage metrics, and historical trends for user dashboards.
*   **Report Generation Engine:** Compiles data from the Verification, Forensics, AI, and Blockchain engines into structured, downloadable verification reports.
*   **Notification Module:** Dispatches asynchronous alerts and updates to users upon completion of complex verifications.
*   **Admin Module:** A secure interface for system administrators to monitor platform health, manage users, and configure system parameters.

## 6. Frontend Architecture
The user interface is a high-performance Single Page Application (SPA) designed for seamless asset upload and intuitive data visualization.
*   **React:** Core UI library for building component-based, reactive interfaces.
*   **TypeScript:** Enforces static typing to ensure robust code quality and catch errors at compile time.
*   **Vite:** Ultra-fast build tool and development server.
*   **Tailwind CSS:** Utility-first CSS framework for rapid, highly customizable styling aligned with the product's premium identity.
*   **Framer Motion:** Powers smooth micro-interactions and dynamic animations to enhance the user experience.
*   **React Query:** Manages asynchronous state, caching, and synchronization of API data.

## 7. Backend Architecture
The backend is a high-throughput API designed for asynchronous processing of compute-heavy digital forensics and AI tasks.
*   **FastAPI:** High-performance asynchronous Python web framework for building the core RESTful APIs.
*   **SQLAlchemy:** Advanced Object-Relational Mapper (ORM) for interacting with the relational database.
*   **Alembic:** Database migration tool to track and manage schema changes over time.
*   **PostgreSQL:** Robust, ACID-compliant relational database for structured data storage.
*   **JWT Authentication:** Stateless, secure token-based authentication for securing API endpoints.
*   **Pydantic:** Data validation and settings management using Python type annotations.

## 8. AI Layer Architecture
The AI layer is strictly designed to augment deterministic analysis with human-readable explanations.
*   **Qwen 3 4B:** Utilized **exclusively for explanation only**. It translates raw forensic and verification data into understandable insights.
*   **PyMuPDF & pdfplumber:** Specialized libraries for deep structural analysis, text extraction, and metadata inspection of PDF documents.
*   **OpenCV, Pillow, ImageHash:** Computer vision and image processing libraries for pixel-level forensics, anomaly detection, and perceptual hashing of image assets.
*   **Librosa & torchaudio:** Audio processing libraries for frequency analysis, spectrogram generation, and audio tampering detection.
*   **Custom Trust Score Engine:** A deterministic algorithm that aggregates evidence from all forensic modules to calculate the final Trust Score.
*   **Important Rule:** AI does NOT directly decide the trust score. Evidence-based, deterministic modules calculate the trust score. The LLM (Qwen) is strictly confined to explaining the final result based on the provided evidence.

## 9. Blockchain Architecture
TrustLens utilizes a cryptographic ledger system to guarantee the immutability of digital asset verification records.
*   **SHA256 Hashing:** Generates a unique, cryptographically secure fingerprint for every uploaded asset.
*   **Block Creation:** Verification records are batched and formalized into cryptographic blocks.
*   **Previous Hash Linking:** Each new block contains the hash of the preceding block, creating an unbreakable chain.
*   **Block Hash Validation:** Continuous integrity checks ensure that historical verification records have not been altered.
*   **Audit Trail:** Provides a mathematically guaranteed, verifiable history of an asset's provenance.

## 10. Storage Architecture
*   **PostgreSQL:** Serves as the primary datastore for all structured data, including user accounts, verification history, trust scores, and platform analytics.
*   **Local Storage (v1.0):** Temporary staging and processing of digital assets during the active verification pipeline in v1.0.
*   **S3/MinIO-Compatible Storage:** Planned migration for scalable, distributed object storage for long-term retention in future scaling.

## 11. Verification Workflow
Every asset processed by TrustLens follows a strict, sequential pipeline:
1.  **Upload asset:** Client securely transmits the digital file.
2.  **Validate file:** System confirms format compatibility and structural integrity.
3.  **Generate hash:** A SHA256 cryptographic fingerprint is immediately generated.
4.  **Extract metadata:** EXIF, XMP, and underlying structural data are extracted.
5.  **Run forensics:** Deep deterministic analysis (pixels, audio frequencies, document layers) is performed.
6.  **Run AI-specific analysis:** Specialized models scan for synthetic generation or advanced manipulation.
7.  **Check blockchain:** The system queries the ledger to determine historical provenance.
8.  **Calculate trust score:** The Custom Trust Score Engine aggregates all forensic evidence to output a deterministic score.
9.  **Generate AI explanation:** The LLM consumes the forensic evidence and trust score to generate a human-readable explanation.
10. **Generate report:** All data is compiled into a final, downloadable Verification Report.

## 12. Authentication Flow
1.  User submits credentials via the frontend application.
2.  Authentication Module validates credentials against securely hashed passwords in PostgreSQL.
3.  Upon success, a short-lived JWT Access Token is issued to the client.
4.  Subsequent API requests include the JWT in the Authorization header.
5.  FastAPI middleware validates the JWT signature and expiration before routing the request to the target module.

## 13. Data Flow
1.  **Client to API:** Encrypted payloads and digital assets are sent over HTTPS.
2.  **API to Verification Engine:** The request is routed to the orchestration layer.
3.  **Verification Engine to Forensics/AI/Blockchain:** The orchestrator dispatches tasks to internal modules.
4.  **Modules to Storage:** Results, metadata, and calculated scores are persisted to PostgreSQL.
5.  **Modules to LLM:** Raw forensic evidence is sent to Qwen 3 4B for explanation generation.
6.  **Verification Engine to Client:** The final Verification Report is returned to the client application.

## 14. Deployment Architecture
*   **Docker Compose:** For streamlined local development and testing.
*   **Vercel:** Edge deployment for the React/Vite frontend SPA, ensuring low latency and high availability.
*   **Render/Railway:** Managed Platform-as-a-Service (PaaS) hosting the FastAPI backend.
*   **PostgreSQL Managed Database:** Fully managed database service provided by the PaaS or an external provider.

## 15. Scalability Strategy
While starting as a Modular Monolith, TrustLens is designed for scale:
*   **Stateless Backend:** The FastAPI application is entirely stateless (sessions managed via JWT), allowing horizontal scaling by deploying multiple instances.
*   **Asynchronous Processing:** Python's `asyncio` handles concurrent operations without blocking the main event loop.
*   **Database Connection Pooling:** SQLAlchemy utilizes robust connection pooling to manage high concurrent database access efficiently.

## 16. Security Considerations
*   **Data in Transit:** All communications are strictly enforced over secure protocols.
*   **Least Privilege:** Database users, API keys, and internal service roles adhere to the principle of least privilege.
*   **Input Validation:** Pydantic models rigorously sanitize and validate all incoming API payloads.
*   **No Black Box Trust:** Trust scores are derived purely from auditable, deterministic evidence.

## 17. Future Migration to Microservices
The strict boundaries established by the Modular Monolith allow for targeted extraction of highly loaded components. In the future, compute-heavy modules like the Digital Forensics Engine and AI Intelligence Engine can be decoupled into independent microservices, scaling independently while the core API remains lean.

## 18. Architecture Decisions Summary
| Component | Decision | Rationale |
| :--- | :--- | :--- |
| **Architecture Style** | Modular Monolith | Balances rapid development speed with clear boundaries for future scaling. |
| **Backend** | FastAPI (Python) | High performance, async support, and excellent AI/Forensics ecosystem. |
| **Frontend** | React, Vite, Tailwind | Industry standard, fast builds, excellent developer experience. |
| **Database** | PostgreSQL | Proven reliability, ACID compliance, and structured data handling. |
| **AI Explanation** | Qwen 3 4B | Efficient LLM constrained strictly to generating explanations. |
| **Trust Scoring** | Deterministic Engine | Ensures trust scores are evidence-based, reproducible, and auditable. |
