# Case Management Module

The Case Management module provides functionality for creating, tracking, and managing fraud investigation cases within the Transaction Monitoring and Fraud Detection System.

## Features

- Create and manage fraud investigation cases
- Link transactions to cases for investigation
- Add notes and attachments to cases
- Track case activities and status changes
- Assign cases to users
- Filter and search cases
- Generate case reports

## Models

### Case
The main model for fraud investigation cases with the following fields:
- `case_id`: Unique identifier for the case
- `title`: Case title
- `description`: Detailed description of the case
- `priority`: Case priority (Low, Medium, High, Critical)
- `status`: Current status (Open, In Progress, Pending Review, Closed)
- `resolution`: Resolution when closed (Confirmed Fraud, False Positive, Inconclusive, Legitimate)
- `created_at`, `updated_at`, `closed_at`: Timestamps
- `created_by`, `assigned_to`: User references
- `financial_impact`: Estimated financial impact
- `risk_score`: Calculated risk score

### CaseTransaction
Links transactions to cases:
- `case`: Reference to the case
- `transaction_id`: ID of the linked transaction
- `added_at`: When the transaction was added
- `added_by`: User who added the transaction

### CaseNote
Stores notes added to cases:
- `case`: Reference to the case
- `content`: Note content
- `created_at`: When the note was created
- `created_by`: User who created the note

### CaseAttachment
Manages file attachments for cases:
- `case`: Reference to the case
- `file`: The uploaded file
- `filename`, `file_type`, `file_size`: File metadata
- `uploaded_at`: When the file was uploaded
- `uploaded_by`: User who uploaded the file

### CaseActivity
Tracks all activities related to a case:
- `case`: Reference to the case
- `activity_type`: Type of activity (create, update, assign, etc.)
- `description`: Description of the activity
- `performed_at`: When the activity was performed
- `performed_by`: User who performed the activity

## Views

- `case_list`: List all cases with filtering options
- `case_create`: Create a new case
- `case_detail`: View case details, transactions, notes, and activities
- `case_edit`: Edit case details
- `case_close`: Close a case with resolution
- `case_reopen`: Reopen a closed case
- `assign_case`: Assign a case to a user
- `add_transaction`: Add transactions to a case
- `remove_transaction`: Remove a transaction from a case
- `add_note`: Add a note to a case
- `delete_note`: Delete a note from a case
- `add_attachment`: Add a file attachment to a case
- `delete_attachment`: Delete an attachment from a case
- `search_transactions`: Search for transactions to add to a case

## Integration with Other Modules

- **Transactions Module**: Links transactions to cases for investigation
- **Fraud Engine**: Uses fraud detection results to create cases automatically
- **Dashboard**: Displays case statistics and metrics
- **Reporting**: Generates reports on case status and resolution
- **Notifications**: Sends alerts for case assignments and updates

## Usage

1. Create a case manually or automatically from a flagged transaction
2. Add relevant transactions to the case
3. Add notes and attachments during investigation
4. Update case status as investigation progresses
5. Close the case with appropriate resolution when complete

## Permissions

- **View Cases**: All authenticated users
- **Create Cases**: Fraud analysts, compliance officers
- **Edit Cases**: Case owner, assigned user, supervisors
- **Close Cases**: Case owner, assigned user, supervisors
- **Delete Cases**: Administrators only