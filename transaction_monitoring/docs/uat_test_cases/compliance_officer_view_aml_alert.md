# User Acceptance Testing (UAT) Test Case

## Test Case Information

| Field | Value |
|-------|-------|
| **Test Case ID** | TC-AML-001 |
| **Test Case Name** | Compliance Officer Views and Updates AML Alert |
| **Module** | AML Alerts |
| **Created By** | System Administrator |
| **Created Date** | 2023-06-15 |
| **User Role** | Compliance Officer |

## Test Case Details

### Objective
Verify that a Compliance Officer can view AML alert details and update the alert status and notes.

### Preconditions
- User is logged in with Compliance Officer role
- At least one AML alert exists in the system
- The user has permission to view and update AML alerts

### Test Data
- Compliance Officer credentials: username = compliance_officer, password = securepassword123
- Test AML alert with ID: AML-2023-06-001

## Test Steps

| Step # | Step Description | Expected Result |
|--------|------------------|-----------------|
| 1 | Log in to the system using Compliance Officer credentials | User is successfully logged in and redirected to the dashboard |
| 2 | Navigate to the AML Alerts page by clicking on "AML Alerts" in the sidebar menu | AML Alerts page is displayed with a list of alerts |
| 3 | Verify that the alert list displays key information (Alert ID, Date, Type, Status, Priority) | Alert list shows the required information for each alert |
| 4 | Use the filter options to filter alerts by status "Open" | Only alerts with "Open" status are displayed |
| 5 | Click on the alert with ID "AML-2023-06-001" | Alert details page is displayed with complete information about the alert |
| 6 | Verify that the alert details include transaction information, risk factors, and customer details | All required information is displayed correctly |
| 7 | Click on the "Update Status" button | A modal dialog appears with status options |
| 8 | Select "Under Investigation" from the status dropdown | Status is changed to "Under Investigation" |
| 9 | Enter "Starting investigation on suspicious transaction pattern" in the notes field | Notes are entered correctly |
| 10 | Click "Save" button | Alert is updated and a success message is displayed |
| 11 | Verify that the alert status is now "Under Investigation" | Alert status is updated correctly |
| 12 | Click on the "Add Note" button | A modal dialog appears for adding a note |
| 13 | Enter "Contacted customer for additional information" in the note field | Note is entered correctly |
| 14 | Click "Save" button | Note is added and a success message is displayed |
| 15 | Verify that the new note appears in the alert timeline | Note is displayed in the timeline with correct timestamp and user |

## Test Execution

| Field | Value |
|-------|-------|
| **Executed By** | [To be filled during execution] |
| **Execution Date** | [To be filled during execution] |
| **Execution Time** | [To be filled during execution] |
| **Test Environment** | UAT Environment |
| **Test Status** | [To be filled during execution] |

## Results

| Step # | Actual Result | Status (Pass/Fail) | Comments |
|--------|---------------|-------------------|----------|
| 1 | [To be filled during execution] | [To be filled during execution] | [To be filled during execution] |
| 2 | [To be filled during execution] | [To be filled during execution] | [To be filled during execution] |
| 3 | [To be filled during execution] | [To be filled during execution] | [To be filled during execution] |
| 4 | [To be filled during execution] | [To be filled during execution] | [To be filled during execution] |
| 5 | [To be filled during execution] | [To be filled during execution] | [To be filled during execution] |
| 6 | [To be filled during execution] | [To be filled during execution] | [To be filled during execution] |
| 7 | [To be filled during execution] | [To be filled during execution] | [To be filled during execution] |
| 8 | [To be filled during execution] | [To be filled during execution] | [To be filled during execution] |
| 9 | [To be filled during execution] | [To be filled during execution] | [To be filled during execution] |
| 10 | [To be filled during execution] | [To be filled during execution] | [To be filled during execution] |
| 11 | [To be filled during execution] | [To be filled during execution] | [To be filled during execution] |
| 12 | [To be filled during execution] | [To be filled during execution] | [To be filled during execution] |
| 13 | [To be filled during execution] | [To be filled during execution] | [To be filled during execution] |
| 14 | [To be filled during execution] | [To be filled during execution] | [To be filled during execution] |
| 15 | [To be filled during execution] | [To be filled during execution] | [To be filled during execution] |

## Issues Found

| Issue # | Issue Description | Severity | Priority | Status |
|---------|-------------------|----------|----------|--------|
| [To be filled if issues are found] | [To be filled if issues are found] | [To be filled if issues are found] | [To be filled if issues are found] | [To be filled if issues are found] |

## Additional Information

### Screenshots
[Screenshots will be added during test execution]

### Notes
This test case verifies the core functionality for Compliance Officers to manage AML alerts, which is a critical compliance requirement.

## Sign-off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Tester | [To be filled after execution] | | |
| Business Analyst | [To be filled after execution] | | |
| Project Manager | [To be filled after execution] | | |