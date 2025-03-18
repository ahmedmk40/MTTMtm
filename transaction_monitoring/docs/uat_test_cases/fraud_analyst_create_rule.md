# User Acceptance Testing (UAT) Test Case

## Test Case Information

| Field | Value |
|-------|-------|
| **Test Case ID** | TC-RULE-001 |
| **Test Case Name** | Fraud Analyst Creates and Tests a New Fraud Detection Rule |
| **Module** | Rule Engine |
| **Created By** | System Administrator |
| **Created Date** | 2023-06-15 |
| **User Role** | Fraud Analyst |

## Test Case Details

### Objective
Verify that a Fraud Analyst can create, configure, test, and activate a new fraud detection rule.

### Preconditions
- User is logged in with Fraud Analyst role
- The user has permission to create and manage rules
- Test transaction data is available in the system

### Test Data
- Fraud Analyst credentials: username = fraud_analyst, password = securepassword123
- Test transaction data for rule testing

## Test Steps

| Step # | Step Description | Expected Result |
|--------|------------------|-----------------|
| 1 | Log in to the system using Fraud Analyst credentials | User is successfully logged in and redirected to the dashboard |
| 2 | Navigate to the Rules page by clicking on "Rules" in the sidebar menu | Rules page is displayed with a list of existing rules |
| 3 | Click on the "Create New Rule" button | Rule creation form is displayed |
| 4 | Enter "High Value E-commerce Transaction Alert" in the Rule Name field | Rule name is entered correctly |
| 5 | Select "E-commerce Transactions" from the Transaction Type dropdown | Transaction type is selected correctly |
| 6 | Select "Amount" from the Condition Type dropdown | Condition type is selected correctly |
| 7 | Select "Greater Than" from the Operator dropdown | Operator is selected correctly |
| 8 | Enter "1000" in the Value field | Value is entered correctly |
| 9 | Select "USD" from the Currency dropdown | Currency is selected correctly |
| 10 | Click "Add Condition" button | Condition is added to the rule |
| 11 | Select "AND" for the logical operator | Logical operator is selected correctly |
| 12 | Select "Location" from the Condition Type dropdown | Condition type is selected correctly |
| 13 | Select "Country" from the Field dropdown | Field is selected correctly |
| 14 | Select "In List" from the Operator dropdown | Operator is selected correctly |
| 15 | Enter "US,CA,MX" in the Value field | Value is entered correctly |
| 16 | Click "Add Condition" button | Second condition is added to the rule |
| 17 | In the Actions section, select "Create Alert" from the Action Type dropdown | Action type is selected correctly |
| 18 | Select "Medium" from the Priority dropdown | Priority is selected correctly |
| 19 | Enter "High value e-commerce transaction detected" in the Message field | Message is entered correctly |
| 20 | Click "Add Action" button | Action is added to the rule |
| 21 | Click "Test Rule" button | Test interface is displayed |
| 22 | Select a test transaction from the dropdown | Test transaction is selected |
| 23 | Click "Run Test" button | Test results are displayed showing whether the rule would trigger for the selected transaction |
| 24 | Verify that the test results match the expected outcome based on the rule conditions | Test results are as expected |
| 25 | Click "Save Rule" button | Rule is saved and a success message is displayed |
| 26 | Toggle the "Active" switch to activate the rule | Rule is activated and status changes to "Active" |
| 27 | Navigate back to the Rules list | Rules list is displayed with the new rule included |
| 28 | Verify that the new rule appears in the list with the correct status | New rule is displayed with "Active" status |

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
| 16 | [To be filled during execution] | [To be filled during execution] | [To be filled during execution] |
| 17 | [To be filled during execution] | [To be filled during execution] | [To be filled during execution] |
| 18 | [To be filled during execution] | [To be filled during execution] | [To be filled during execution] |
| 19 | [To be filled during execution] | [To be filled during execution] | [To be filled during execution] |
| 20 | [To be filled during execution] | [To be filled during execution] | [To be filled during execution] |
| 21 | [To be filled during execution] | [To be filled during execution] | [To be filled during execution] |
| 22 | [To be filled during execution] | [To be filled during execution] | [To be filled during execution] |
| 23 | [To be filled during execution] | [To be filled during execution] | [To be filled during execution] |
| 24 | [To be filled during execution] | [To be filled during execution] | [To be filled during execution] |
| 25 | [To be filled during execution] | [To be filled during execution] | [To be filled during execution] |
| 26 | [To be filled during execution] | [To be filled during execution] | [To be filled during execution] |
| 27 | [To be filled during execution] | [To be filled during execution] | [To be filled during execution] |
| 28 | [To be filled during execution] | [To be filled during execution] | [To be filled during execution] |

## Issues Found

| Issue # | Issue Description | Severity | Priority | Status |
|---------|-------------------|----------|----------|--------|
| [To be filled if issues are found] | [To be filled if issues are found] | [To be filled if issues are found] | [To be filled if issues are found] | [To be filled if issues are found] |

## Additional Information

### Screenshots
[Screenshots will be added during test execution]

### Notes
This test case verifies the rule creation functionality, which is a critical feature for Fraud Analysts to configure the system's fraud detection capabilities.

## Sign-off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Tester | [To be filled after execution] | | |
| Business Analyst | [To be filled after execution] | | |
| Project Manager | [To be filled after execution] | | |