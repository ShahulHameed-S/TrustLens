# TrustLens: API Design (v1.0)

## 1. API Overview
The TrustLens API is a RESTful web service built with FastAPI, designed to integrate seamlessly with the React frontend client and external systems. It provides robust endpoints for user management, digital asset uploads (PDF, Image, Audio), deterministic verification, AI-driven explanations, and blockchain-backed integrity checks.

## 2. API Versioning
The API uses URI versioning to ensure backward compatibility as the platform evolves. The current version is `v1`.

## 3. Base URL

TrustLens supports separate environments for development and production.

### Development Environment

```text
http://localhost:8000/api/v1
```

This endpoint is used during local development when the React frontend communicates with the FastAPI backend.

### Production Environment

```text
https://api.trustlens.io/api/v1
```

This endpoint is used after deployment.

The frontend should switch automatically between environments using environment variables (`.env`) rather than hardcoded URLs.

Example:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

Development and production URLs must remain configurable to support Docker, local development, staging, and cloud deployment.

## 4. Authentication Method
The API secures protected routes using **JSON Web Tokens (JWT)** passed in the `Authorization` header as a Bearer token.
```http
Authorization: Bearer <your_jwt_token>
```

## 5. Standard Response Format
All successful API responses follow a structured JSON format:
```json
{
  "success": true,
  "data": { ... }
}
```
For paginated list endpoints, the `data` object will include pagination metadata:
```json
{
  "success": true,
  "data": {
    "items": [ ... ],
    "total": 100,
    "page": 1,
    "limit": 20,
    "total_pages": 5
  }
}
```

## 6. Standard Error Format
All API errors return a standard JSON structure to facilitate easy frontend error handling:
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error description.",
    "details": {} 
  }
}
```

## 7. HTTP Status Codes
*   **200 OK:** Request succeeded.
*   **201 Created:** Resource successfully created.
*   **400 Bad Request:** Invalid input or validation error.
*   **401 Unauthorized:** Missing or invalid JWT token.
*   **403 Forbidden:** User lacks permission to access the resource.
*   **404 Not Found:** Resource does not exist.
*   **413 Payload Too Large:** Uploaded asset exceeds size limits.
*   **429 Too Many Requests:** Rate limit exceeded.
*   **500 Internal Server Error:** Unexpected server-side issue.

## 8. Authentication APIs

### `POST /api/v1/auth/register`
*   **Purpose:** Register a new user account.
*   **Authentication:** Not Required
*   **Request Body:** `{"email": "user@example.com", "password": "securepassword"}`
*   **Success Response:** `{"success": true, "data": {"id": "uuid", "email": "user@example.com"}}`
*   **Error Response:** `{"success": false, "error": {"code": "EMAIL_EXISTS", "message": "Email is already registered."}}`

### `POST /api/v1/auth/login`
*   **Purpose:** Authenticate a user and issue JWTs.
*   **Authentication:** Not Required
*   **Request Body:** `{"email": "user@example.com", "password": "securepassword"}`
*   **Success Response:** `{"success": true, "data": {"access_token": "jwt...", "refresh_token": "jwt...", "token_type": "bearer"}}`
*   **Error Response:** `{"success": false, "error": {"code": "INVALID_CREDENTIALS", "message": "Invalid email or password."}}`

### `POST /api/v1/auth/refresh`
*   **Purpose:** Obtain a new access token using a valid refresh token.
*   **Authentication:** Required (Refresh Token)
*   **Request Body:** `{"refresh_token": "jwt..."}`
*   **Success Response:** `{"success": true, "data": {"access_token": "new_jwt..."}}`
*   **Error Response:** `{"success": false, "error": {"code": "TOKEN_EXPIRED", "message": "Refresh token expired."}}`

### `POST /api/v1/auth/logout`
*   **Purpose:** Invalidate the current session tokens.
*   **Authentication:** Required
*   **Request Body:** None
*   **Success Response:** `{"success": true, "data": {"message": "Successfully logged out."}}`
*   **Error Response:** `{"success": false, "error": {"code": "UNAUTHORIZED", "message": "Invalid token."}}`

### `GET /api/v1/auth/me`
*   **Purpose:** Retrieve the currently authenticated user's session details and roles.
*   **Authentication:** Required
*   **Request Parameters:** None
*   **Success Response:** `{"success": true, "data": {"id": "uuid", "email": "user@example.com", "roles": ["user"]}}`
*   **Error Response:** `{"success": false, "error": {"code": "UNAUTHORIZED", "message": "Invalid or missing token."}}`

## 9. User APIs

### `GET /api/v1/users/me`
*   **Purpose:** Get full profile details for the authenticated user.
*   **Authentication:** Required
*   **Request Parameters:** None
*   **Success Response:** `{"success": true, "data": {"id": "uuid", "email": "user@example.com", "created_at": "timestamp"}}`
*   **Error Response:** `{"success": false, "error": {"code": "USER_NOT_FOUND", "message": "User profile not found."}}`

### `PUT /api/v1/users/me`
*   **Purpose:** Update user profile settings.
*   **Authentication:** Required
*   **Request Body:** `{"preferences": {...}}`
*   **Success Response:** `{"success": true, "data": {"id": "uuid", "updated_at": "timestamp"}}`
*   **Error Response:** `{"success": false, "error": {"code": "VALIDATION_ERROR", "message": "Invalid payload."}}`

### `DELETE /api/v1/users/me`
*   **Purpose:** Permanently delete the user account and associated data.
*   **Authentication:** Required
*   **Request Parameters:** None
*   **Success Response:** `{"success": true, "data": {"message": "Account deleted."}}`
*   **Error Response:** `{"success": false, "error": {"code": "ACTION_FAILED", "message": "Unable to delete account."}}`

## 10. Asset APIs

### `POST /api/v1/assets/upload`
*   **Purpose:** Upload a digital asset (PDF, Image, Audio) for storage and subsequent verification.
*   **Authentication:** Required
*   **Request Body:** `multipart/form-data` containing the `file`.
*   **Success Response:** `{"success": true, "data": {"asset_id": "uuid", "filename": "doc.pdf", "asset_type": "PDF"}}`
*   **Error Response:** `{"success": false, "error": {"code": "UNSUPPORTED_TYPE", "message": "File type not supported."}}`

### `GET /api/v1/assets`
*   **Purpose:** List all uploaded assets for the user.
*   **Authentication:** Required
*   **Request Parameters:** `?page=1&limit=20&sort=uploaded_at&order=desc`
*   **Success Response:** `{"success": true, "data": {"items": [...], "total": 5}}`
*   **Error Response:** `{"success": false, "error": {"code": "UNAUTHORIZED", "message": "Missing token."}}`

### `GET /api/v1/assets/{asset_id}`
*   **Purpose:** Retrieve metadata for a specific uploaded asset.
*   **Authentication:** Required
*   **Request Parameters:** `asset_id` (UUID in path)
*   **Success Response:** `{"success": true, "data": {"asset_id": "uuid", "file_hash": "sha256...", "size": 1024}}`
*   **Error Response:** `{"success": false, "error": {"code": "NOT_FOUND", "message": "Asset not found."}}`

### `DELETE /api/v1/assets/{asset_id}`
*   **Purpose:** Delete an asset and its associated verifications.
*   **Authentication:** Required
*   **Request Parameters:** `asset_id` (UUID in path)
*   **Success Response:** `{"success": true, "data": {"message": "Asset deleted."}}`
*   **Error Response:** `{"success": false, "error": {"code": "NOT_FOUND", "message": "Asset not found."}}`

## 11. Verification APIs

### `POST /api/v1/verifications/pdf`
*   **Purpose:** Trigger the verification pipeline for a PDF asset.
*   **Authentication:** Required
*   **Request Body:** `{"asset_id": "uuid"}`
*   **Success Response:** *See standard Verification Response Schema (Section 17).*
*   **Error Response:** `{"success": false, "error": {"code": "INVALID_ASSET_TYPE", "message": "Asset is not a PDF."}}`

### `POST /api/v1/verifications/image`
*   **Purpose:** Trigger the verification pipeline for an Image asset.
*   **Authentication:** Required
*   **Request Body:** `{"asset_id": "uuid"}`
*   **Success Response:** *See standard Verification Response Schema (Section 17).*
*   **Error Response:** `{"success": false, "error": {"code": "INVALID_ASSET_TYPE", "message": "Asset is not an Image."}}`

### `POST /api/v1/verifications/audio`
*   **Purpose:** Trigger the verification pipeline for an Audio asset.
*   **Authentication:** Required
*   **Request Body:** `{"asset_id": "uuid"}`
*   **Success Response:** *See standard Verification Response Schema (Section 17).*
*   **Error Response:** `{"success": false, "error": {"code": "INVALID_ASSET_TYPE", "message": "Asset is not Audio."}}`

### `GET /api/v1/verifications`
*   **Purpose:** List verification history for the authenticated user.
*   **Authentication:** Required
*   **Request Parameters:** `?page=1&limit=20&sort=created_at&order=desc`
*   **Success Response:** `{"success": true, "data": {"items": [...], "total": 12}}`
*   **Error Response:** `{"success": false, "error": {"code": "UNAUTHORIZED", "message": "Missing token."}}`

### `GET /api/v1/verifications/{verification_id}`
*   **Purpose:** Retrieve the full results of a specific verification.
*   **Authentication:** Required
*   **Request Parameters:** `verification_id` (UUID in path)
*   **Success Response:** *See standard Verification Response Schema (Section 17).*
*   **Error Response:** `{"success": false, "error": {"code": "NOT_FOUND", "message": "Verification not found."}}`

### `DELETE /api/v1/verifications/{verification_id}`
*   **Purpose:** Remove a verification record from the user's dashboard.
*   **Authentication:** Required
*   **Request Parameters:** `verification_id` (UUID in path)
*   **Success Response:** `{"success": true, "data": {"message": "Verification deleted."}}`
*   **Error Response:** `{"success": false, "error": {"code": "NOT_FOUND", "message": "Verification not found."}}`

## 12. Blockchain APIs

### `GET /api/v1/blockchain`
*   **Purpose:** Retrieve the latest blocks anchored by the platform.
*   **Authentication:** Required
*   **Request Parameters:** `?page=1&limit=10`
*   **Success Response:** `{"success": true, "data": {"items": [{"block_hash": "...", "timestamp": "..."}]}}`
*   **Error Response:** `{"success": false, "error": {"code": "SERVER_ERROR", "message": "Blockchain unavailable."}}`

### `GET /api/v1/blockchain/blocks/{block_id}`
*   **Purpose:** Retrieve details for a specific blockchain block.
*   **Authentication:** Required
*   **Request Parameters:** `block_id` (ID in path)
*   **Success Response:** `{"success": true, "data": {"block_hash": "...", "previous_block_hash": "..."}}`
*   **Error Response:** `{"success": false, "error": {"code": "NOT_FOUND", "message": "Block not found."}}`

### `GET /api/v1/blockchain/hash/{hash}`
*   **Purpose:** Search the ledger for a specific SHA-256 asset hash.
*   **Authentication:** Required
*   **Request Parameters:** `hash` (SHA-256 string in path)
*   **Success Response:** `{"success": true, "data": {"registered": true, "block_id": 123}}`
*   **Error Response:** `{"success": false, "error": {"code": "NOT_FOUND", "message": "Hash not found in ledger."}}`

### `GET /api/v1/blockchain/validate`
*   **Purpose:** Trigger an integrity check of the entire block sequence to verify immutability.
*   **Authentication:** Required (Admin only)
*   **Request Parameters:** None
*   **Success Response:** `{"success": true, "data": {"valid": true, "blocks_checked": 1500}}`
*   **Error Response:** `{"success": false, "error": {"code": "INTEGRITY_ERROR", "message": "Chain validation failed."}}`

## 13. Analytics APIs

### `GET /api/v1/analytics/dashboard`
*   **Purpose:** Retrieve top-level summary metrics for the user's dashboard.
*   **Authentication:** Required
*   **Request Parameters:** None
*   **Success Response:** `{"success": true, "data": {"total_verifications": 100, "average_trust_score": 92.5}}`
*   **Error Response:** `{"success": false, "error": {"code": "UNAUTHORIZED", "message": "Missing token."}}`

### `GET /api/v1/analytics/risk-distribution`
*   **Purpose:** Retrieve the count of verifications segmented by Risk Level (LOW, MEDIUM, HIGH).
*   **Authentication:** Required
*   **Request Parameters:** None
*   **Success Response:** `{"success": true, "data": {"LOW": 80, "MEDIUM": 15, "HIGH": 5}}`
*   **Error Response:** `{"success": false, "error": {"code": "UNAUTHORIZED", "message": "Missing token."}}`

### `GET /api/v1/analytics/verification-trends`
*   **Purpose:** Retrieve verification volume data over time (e.g., last 30 days).
*   **Authentication:** Required
*   **Request Parameters:** `?timeframe=30d`
*   **Success Response:** `{"success": true, "data": {"dates": ["2026-06-01", ...], "counts": [5, ...]}}`
*   **Error Response:** `{"success": false, "error": {"code": "INVALID_PARAMS", "message": "Invalid timeframe."}}`

### `GET /api/v1/analytics/asset-types`
*   **Purpose:** Retrieve the breakdown of analyzed asset types (PDF vs. Image vs. Audio).
*   **Authentication:** Required
*   **Request Parameters:** None
*   **Success Response:** `{"success": true, "data": {"PDF": 40, "IMAGE": 50, "AUDIO": 10}}`
*   **Error Response:** `{"success": false, "error": {"code": "UNAUTHORIZED", "message": "Missing token."}}`

## 14. Report APIs

### `POST /api/v1/reports/generate/{verification_id}`
*   **Purpose:** Trigger the asynchronous generation of a detailed PDF verification report.
*   **Authentication:** Required
*   **Request Parameters:** `verification_id` (UUID in path)
*   **Success Response:** `{"success": true, "data": {"report_id": "uuid", "status": "GENERATING"}}`
*   **Error Response:** `{"success": false, "error": {"code": "NOT_FOUND", "message": "Verification not found."}}`

### `GET /api/v1/reports/{report_id}`
*   **Purpose:** Check the generation status or fetch metadata for a specific report.
*   **Authentication:** Required
*   **Request Parameters:** `report_id` (UUID in path)
*   **Success Response:** `{"success": true, "data": {"report_id": "uuid", "status": "READY", "download_url": "..."}}`
*   **Error Response:** `{"success": false, "error": {"code": "NOT_FOUND", "message": "Report not found."}}`

### `GET /api/v1/reports/download/{report_id}`
*   **Purpose:** Download the generated PDF report file.
*   **Authentication:** Required
*   **Request Parameters:** `report_id` (UUID in path)
*   **Success Response:** *(Returns the binary PDF file)*
*   **Error Response:** `{"success": false, "error": {"code": "NOT_FOUND", "message": "Report not ready or missing."}}`

## 15. Audit Log APIs

### `GET /api/v1/audit-logs`
*   **Purpose:** Retrieve immutable logs of user and system actions.
*   **Authentication:** Required
*   **Request Parameters:** `?page=1&limit=50&sort=timestamp&order=desc`
*   **Success Response:** `{"success": true, "data": {"items": [{"action": "UPLOAD_ASSET", "timestamp": "..."}], "total": 200}}`
*   **Error Response:** `{"success": false, "error": {"code": "UNAUTHORIZED", "message": "Missing token."}}`

## 16. Request and Response Examples
*(Covered inline within Sections 8-15 for clarity and conciseness)*

## 17. Verification Response Schema
All verification initiation and retrieval endpoints return the following highly structured schema. 
**Important Note:** The deterministic Trust Score Engine calculates `trust_score` and `risk_level`. The LLM ONLY generates the `ai_explanation` JSONB object based on the engine's findings.

```json
{
  "success": true,
  "data": {
    "verification_id": "uuid",
    "asset_id": "uuid",
    "filename": "example.pdf",
    "asset_type": "PDF",
    "file_hash": "sha256_hash",
    "verification_status": "COMPLETED",
    "document_status": "AUTHENTIC | SUSPICIOUS | UNVERIFIED",
    "trust_score": 98.5,
    "risk_level": "LOW | MEDIUM | HIGH",
    "blockchain_proof": {
      "registered": true,
      "block_number": 1,
      "block_hash": "hash",
      "previous_hash": "hash"
    },
    "ai_explanation": {
      "summary": "The document appears to be authentic and untampered.",
      "evidence": "No structural anomalies detected. Metadata matches expected origin.",
      "reasoning": "Because the cryptographic signature and structural layers are intact, the risk of forgery is minimal.",
      "recommendation": "Accept the document as verified.",
      "confidence": 99
    },
    "metadata": {},
    "created_at": "timestamp"
  }
}
```

## 18. Security Rules
*   **JWT Protection:** All endpoints except `/auth/register` and `/auth/login` demand a valid JWT in the `Authorization` header.
*   **Validation:** Strict file type (MIME) and file size limits are enforced on upload endpoints to prevent malicious payload execution and denial of service.
*   **Rate Limiting:** Upload and verification endpoints are strictly rate-limited per user to manage compute costs.
*   **Data Masking:** `password_hash` and internal cryptographic secrets are never exposed in any API response.
*   **Path Obfuscation:** Internal storage paths (e.g., local disk or S3 URIs) are never exposed directly to the public client.
*   **UUID Identifiers:** Sequential integers are completely avoided for primary keys exposed to the client to prevent ID enumeration.
*   **Structured Errors:** Stack traces are suppressed in production; only structured JSON error codes are returned.

## 19. Pagination Rules
For all list endpoints (e.g., `/assets`, `/verifications`, `/audit-logs`), the API relies on query parameters:
*   `page`: The page number to retrieve (default: 1).
*   `limit`: The number of items per page (default: 20, max: 100).
*   `sort`: The field to sort by (e.g., `created_at`).
*   `order`: The sort direction (`asc` or `desc`).

## 20. API Design Decisions Summary
*   **FastAPI & Pydantic:** Adopted to ensure rigorous automatic payload validation and seamless generation of OpenAPI (Swagger) documentation.
*   **Strict AI Boundary:** The API explicitly separates deterministic scoring metrics (`trust_score`, `risk_level`) from LLM outputs (`ai_explanation`), enforcing the platform's rule that AI explains but does not decide.
*   **Consistent Response Wrapping:** Ensuring every response uses the `{ "success": true/false, "data" | "error": { ... } }` wrapper drastically simplifies client-side state management in the React frontend.
