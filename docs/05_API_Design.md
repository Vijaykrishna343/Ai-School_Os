# AI School OS — API Design & Interface Specification

## 1. Response & Error Envelopes

All API endpoints return standard JSON response envelopes:

### 1.1 Success Response (`ApiResponse.success`)
```json
{
  "success": true,
  "message": "Operation completed successfully.",
  "data": { ... },
  "errors": null
}
```

### 1.2 Error Response (`ApiResponse.error`)
```json
{
  "success": false,
  "message": "Validation failed.",
  "data": null,
  "errors": {
    "field": "Validation details"
  }
}
```

---

## 2. HTTP Status Code Conventions

- `200 OK`: Successful retrieval, update, or non-resource-creation POST operation.
- `201 Created`: Resource successfully created.
- `400 Bad Request`: Malformed payload or invalid request state (`BadRequestException`).
- `401 Unauthorized`: Missing, invalid, expired, or soft-deleted user JWT token (`UnauthorizedException`).
- `403 Forbidden`: Authenticated user lacks required permission (`ForbiddenException`).
- `404 Not Found`: Target entity or route does not exist (`NotFoundException`).
- `422 Unprocessable Content`: Domain rule or entity constraint validation error (`ValidationException`).

---

## 3. Academic Progression Endpoints (Phase 4B & 4C)

### 3.1 Generate Prospective Progression Preview
`POST /api/v1/academic-years/{academic_year_id}/progression-preview`
- **Permission**: `progression.view`
- **Request Body**:
  ```json
  {
    "target_academic_year_id": "uuid"
  }
  ```
- **Response**: Returns prospective promotion decisions, summary counts (promoted, retained, graduated, blocked), and deterministic `execution_plan_hash`.

### 3.2 Execute Academic Progression Rollover
`POST /api/v1/academic-years/{academic_year_id}/progression-execute`
- **Permission**: `progression.execute`
- **Headers**: `Idempotency-Key: <unique-uuid-or-string>`
- **Request Body**:
  ```json
  {
    "target_academic_year_id": "uuid",
    "execution_plan_hash": "sha256_hash_string"
  }
  ```
- **Response**: Transactional rollover execution result with processed counts.

---

## 4. Legacy Student Promotion Endpoints (Phase 4C.3 — Deprecated)

The following ad-hoc promotion endpoints remain supported for client backward compatibility but are **marked deprecated** in OpenAPI docs and enforce ClassProgressionRule matrix validation:

- `POST /api/v1/students/{student_id}/promote` `(Deprecated)`
- `POST /api/v1/students/{student_id}/retain` `(Deprecated)`
- `POST /api/v1/students/promote/bulk` `(Deprecated)`
- `POST /api/v1/students/retain/bulk` `(Deprecated)`

---

## 5. Security & Authentication Endpoints

- `POST /api/v1/auth/login`: Issue access & refresh JWT tokens.
- `POST /api/v1/auth/refresh`: Issue new access token from refresh token.
- `POST /api/v1/auth/logout`: Revoke active session tokens.
