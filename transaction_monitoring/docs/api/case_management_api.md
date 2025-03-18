# Case Management API Documentation

## Overview

The Case Management API provides programmatic access to create, read, update, and delete fraud investigation cases and their associated data. This API allows integration with external systems and automation of case management workflows.

## Base URL

All API endpoints are relative to the base URL:

```
https://api.transaction-monitoring.com/api/v1
```

## Authentication

All API requests require authentication using an API token. Include the token in the Authorization header:

```
Authorization: Token YOUR_API_TOKEN
```

## Response Format

All responses are returned in JSON format. Successful responses include a `data` field containing the requested information. Error responses include an `error` field with details about the error.

## Pagination

List endpoints support pagination using the following query parameters:

- `page`: Page number (default: 1)
- `page_size`: Number of items per page (default: 20, max: 100)

Paginated responses include the following metadata:

```json
{
  "data": [...],
  "pagination": {
    "count": 100,
    "page": 1,
    "page_size": 20,
    "pages": 5
  }
}
```

## Error Handling

The API uses standard HTTP status codes to indicate success or failure:

- `200 OK`: Request succeeded
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication failed
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses include details about the error:

```json
{
  "error": {
    "code": "invalid_parameter",
    "message": "Invalid case ID format",
    "details": {
      "case_id": "Must be in format CASE-XXXXXXXX"
    }
  }
}
```

## Rate Limiting

API requests are rate-limited to 1000 requests per hour per API token. Rate limit information is included in the response headers:

- `X-RateLimit-Limit`: Maximum requests per hour
- `X-RateLimit-Remaining`: Remaining requests in the current period
- `X-RateLimit-Reset`: Time when the rate limit resets (Unix timestamp)

## Endpoints

### Cases

#### List Cases

```
GET /cases
```

Retrieves a paginated list of cases.

**Query Parameters:**

- `case_id`: Filter by case ID
- `title`: Filter by title (partial match)
- `status`: Filter by status (open, in_progress, pending_review, closed)
- `priority`: Filter by priority (low, medium, high, critical)
- `assigned_to`: Filter by assigned user ID
- `created_from`: Filter by creation date (ISO 8601 format)
- `created_to`: Filter by creation date (ISO 8601 format)
- `sort`: Sort field (created_at, updated_at, priority, status)
- `order`: Sort order (asc, desc)

**Response:**

```json
{
  "data": [
    {
      "id": 1,
      "case_id": "CASE-12345678",
      "title": "Suspicious Transaction Pattern",
      "description": "Multiple high-value transactions from different locations",
      "priority": "high",
      "status": "open",
      "resolution": null,
      "created_at": "2025-03-15T10:30:00Z",
      "updated_at": "2025-03-15T10:30:00Z",
      "closed_at": null,
      "created_by": {
        "id": 5,
        "username": "analyst1"
      },
      "assigned_to": {
        "id": 8,
        "username": "investigator2"
      },
      "financial_impact": 5000.00,
      "risk_score": 0.85,
      "transaction_count": 3,
      "note_count": 2,
      "attachment_count": 1
    },
    // More cases...
  ],
  "pagination": {
    "count": 45,
    "page": 1,
    "page_size": 20,
    "pages": 3
  }
}
```

#### Get Case

```
GET /cases/{case_id}
```

Retrieves detailed information about a specific case.

**Response:**

```json
{
  "data": {
    "id": 1,
    "case_id": "CASE-12345678",
    "title": "Suspicious Transaction Pattern",
    "description": "Multiple high-value transactions from different locations",
    "priority": "high",
    "status": "open",
    "resolution": null,
    "created_at": "2025-03-15T10:30:00Z",
    "updated_at": "2025-03-15T10:30:00Z",
    "closed_at": null,
    "created_by": {
      "id": 5,
      "username": "analyst1"
    },
    "assigned_to": {
      "id": 8,
      "username": "investigator2"
    },
    "financial_impact": 5000.00,
    "risk_score": 0.85
  }
}
```

#### Create Case

```
POST /cases
```

Creates a new case.

**Request Body:**

```json
{
  "title": "Suspicious Transaction Pattern",
  "description": "Multiple high-value transactions from different locations",
  "priority": "high",
  "status": "open",
  "assigned_to": 8,
  "transaction_ids": ["tx_123456", "tx_789012"]
}
```

**Response:**

```json
{
  "data": {
    "id": 1,
    "case_id": "CASE-12345678",
    "title": "Suspicious Transaction Pattern",
    "description": "Multiple high-value transactions from different locations",
    "priority": "high",
    "status": "open",
    "resolution": null,
    "created_at": "2025-03-15T10:30:00Z",
    "updated_at": "2025-03-15T10:30:00Z",
    "closed_at": null,
    "created_by": {
      "id": 5,
      "username": "analyst1"
    },
    "assigned_to": {
      "id": 8,
      "username": "investigator2"
    },
    "financial_impact": 0.00,
    "risk_score": 0.00
  }
}
```

#### Update Case

```
PUT /cases/{case_id}
```

Updates an existing case.

**Request Body:**

```json
{
  "title": "Updated Case Title",
  "description": "Updated description with new information",
  "priority": "critical",
  "status": "in_progress",
  "assigned_to": 10
}
```

**Response:**

```json
{
  "data": {
    "id": 1,
    "case_id": "CASE-12345678",
    "title": "Updated Case Title",
    "description": "Updated description with new information",
    "priority": "critical",
    "status": "in_progress",
    "resolution": null,
    "created_at": "2025-03-15T10:30:00Z",
    "updated_at": "2025-03-15T11:45:00Z",
    "closed_at": null,
    "created_by": {
      "id": 5,
      "username": "analyst1"
    },
    "assigned_to": {
      "id": 10,
      "username": "investigator4"
    },
    "financial_impact": 5000.00,
    "risk_score": 0.85
  }
}
```

#### Close Case

```
POST /cases/{case_id}/close
```

Closes a case with resolution.

**Request Body:**

```json
{
  "resolution": "confirmed_fraud",
  "notes": "Investigation confirmed fraudulent activity based on device fingerprinting and transaction patterns."
}
```

**Response:**

```json
{
  "data": {
    "id": 1,
    "case_id": "CASE-12345678",
    "title": "Suspicious Transaction Pattern",
    "status": "closed",
    "resolution": "confirmed_fraud",
    "closed_at": "2025-03-17T14:20:00Z",
    "updated_at": "2025-03-17T14:20:00Z"
  }
}
```

#### Reopen Case

```
POST /cases/{case_id}/reopen
```

Reopens a previously closed case.

**Request Body:**

```json
{
  "notes": "New evidence requires further investigation."
}
```

**Response:**

```json
{
  "data": {
    "id": 1,
    "case_id": "CASE-12345678",
    "title": "Suspicious Transaction Pattern",
    "status": "open",
    "resolution": null,
    "closed_at": null,
    "updated_at": "2025-03-18T09:15:00Z"
  }
}
```

### Case Transactions

#### List Case Transactions

```
GET /cases/{case_id}/transactions
```

Retrieves transactions associated with a case.

**Response:**

```json
{
  "data": [
    {
      "id": 1,
      "case_id": "CASE-12345678",
      "transaction_id": "tx_123456",
      "added_at": "2025-03-15T10:35:00Z",
      "added_by": {
        "id": 5,
        "username": "analyst1"
      },
      "transaction_details": {
        "amount": 1500.00,
        "currency": "USD",
        "user_id": "user_789",
        "channel": "pos",
        "timestamp": "2025-03-14T22:45:00Z"
      }
    },
    // More transactions...
  ],
  "pagination": {
    "count": 3,
    "page": 1,
    "page_size": 20,
    "pages": 1
  }
}
```

#### Add Transaction to Case

```
POST /cases/{case_id}/transactions
```

Adds one or more transactions to a case.

**Request Body:**

```json
{
  "transaction_ids": ["tx_123456", "tx_789012"]
}
```

**Response:**

```json
{
  "data": {
    "added": 2,
    "transaction_ids": ["tx_123456", "tx_789012"]
  }
}
```

#### Remove Transaction from Case

```
DELETE /cases/{case_id}/transactions/{transaction_id}
```

Removes a transaction from a case.

**Response:**

```json
{
  "data": {
    "success": true,
    "message": "Transaction removed from case"
  }
}
```

### Case Notes

#### List Case Notes

```
GET /cases/{case_id}/notes
```

Retrieves notes associated with a case.

**Response:**

```json
{
  "data": [
    {
      "id": 1,
      "case_id": "CASE-12345678",
      "content": "Initial investigation shows unusual transaction patterns across multiple devices.",
      "created_at": "2025-03-15T10:40:00Z",
      "created_by": {
        "id": 5,
        "username": "analyst1"
      }
    },
    // More notes...
  ],
  "pagination": {
    "count": 2,
    "page": 1,
    "page_size": 20,
    "pages": 1
  }
}
```

#### Add Note to Case

```
POST /cases/{case_id}/notes
```

Adds a note to a case.

**Request Body:**

```json
{
  "content": "Customer contacted and confirmed they did not authorize these transactions."
}
```

**Response:**

```json
{
  "data": {
    "id": 3,
    "case_id": "CASE-12345678",
    "content": "Customer contacted and confirmed they did not authorize these transactions.",
    "created_at": "2025-03-16T11:20:00Z",
    "created_by": {
      "id": 5,
      "username": "analyst1"
    }
  }
}
```

#### Delete Note from Case

```
DELETE /cases/{case_id}/notes/{note_id}
```

Deletes a note from a case.

**Response:**

```json
{
  "data": {
    "success": true,
    "message": "Note deleted from case"
  }
}
```

### Case Attachments

#### List Case Attachments

```
GET /cases/{case_id}/attachments
```

Retrieves attachments associated with a case.

**Response:**

```json
{
  "data": [
    {
      "id": 1,
      "case_id": "CASE-12345678",
      "filename": "transaction_evidence.pdf",
      "file_type": "application/pdf",
      "file_size": 256000,
      "file_url": "https://api.transaction-monitoring.com/files/attachments/12345.pdf",
      "uploaded_at": "2025-03-15T14:30:00Z",
      "uploaded_by": {
        "id": 5,
        "username": "analyst1"
      }
    },
    // More attachments...
  ],
  "pagination": {
    "count": 1,
    "page": 1,
    "page_size": 20,
    "pages": 1
  }
}
```

#### Add Attachment to Case

```
POST /cases/{case_id}/attachments
```

Adds an attachment to a case. This endpoint uses multipart/form-data.

**Form Parameters:**

- `file`: The file to upload
- `description` (optional): Description of the attachment

**Response:**

```json
{
  "data": {
    "id": 2,
    "case_id": "CASE-12345678",
    "filename": "customer_statement.pdf",
    "file_type": "application/pdf",
    "file_size": 128000,
    "file_url": "https://api.transaction-monitoring.com/files/attachments/67890.pdf",
    "uploaded_at": "2025-03-16T15:45:00Z",
    "uploaded_by": {
      "id": 5,
      "username": "analyst1"
    }
  }
}
```

#### Delete Attachment from Case

```
DELETE /cases/{case_id}/attachments/{attachment_id}
```

Deletes an attachment from a case.

**Response:**

```json
{
  "data": {
    "success": true,
    "message": "Attachment deleted from case"
  }
}
```

### Case Activities

#### List Case Activities

```
GET /cases/{case_id}/activities
```

Retrieves activity log for a case.

**Response:**

```json
{
  "data": [
    {
      "id": 1,
      "case_id": "CASE-12345678",
      "activity_type": "create",
      "description": "Case CASE-12345678 was created.",
      "performed_at": "2025-03-15T10:30:00Z",
      "performed_by": {
        "id": 5,
        "username": "analyst1"
      }
    },
    {
      "id": 2,
      "activity_type": "add_transaction",
      "description": "Transaction tx_123456 added to the case.",
      "performed_at": "2025-03-15T10:35:00Z",
      "performed_by": {
        "id": 5,
        "username": "analyst1"
      }
    },
    // More activities...
  ],
  "pagination": {
    "count": 5,
    "page": 1,
    "page_size": 20,
    "pages": 1
  }
}
```

## Webhooks

The API supports webhooks to notify external systems about case events. Configure webhooks in the API settings.

### Available Events

- `case.created`: Triggered when a new case is created
- `case.updated`: Triggered when a case is updated
- `case.closed`: Triggered when a case is closed
- `case.reopened`: Triggered when a case is reopened
- `case.transaction_added`: Triggered when a transaction is added to a case
- `case.note_added`: Triggered when a note is added to a case
- `case.attachment_added`: Triggered when an attachment is added to a case

### Webhook Payload

```json
{
  "event": "case.created",
  "timestamp": "2025-03-15T10:30:00Z",
  "data": {
    "case_id": "CASE-12345678",
    "title": "Suspicious Transaction Pattern",
    "status": "open",
    "priority": "high",
    "created_at": "2025-03-15T10:30:00Z",
    "created_by": {
      "id": 5,
      "username": "analyst1"
    }
  }
}
```

## SDK Libraries

Official SDK libraries are available for the following languages:

- Python: [GitHub Repository](https://github.com/transaction-monitoring/python-sdk)
- JavaScript: [GitHub Repository](https://github.com/transaction-monitoring/js-sdk)
- Java: [GitHub Repository](https://github.com/transaction-monitoring/java-sdk)
- Ruby: [GitHub Repository](https://github.com/transaction-monitoring/ruby-sdk)

## API Versioning

The API uses a versioned URL path (e.g., `/api/v1/`) to ensure backward compatibility. When breaking changes are introduced, a new API version will be released.