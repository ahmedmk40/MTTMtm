# User Acceptance Testing (UAT) Test Case

## Test Case Information

| Field | Value |
|-------|-------|
| **Test Case ID** | TC-RISK-001 |
| **Test Case Name** | Risk Manager Reviews Dashboard and Configures Risk Thresholds |
| **Module** | Risk Management |
| **Created By** | System Administrator |
| **Created Date** | 2023-06-15 |
| **User Role** | Risk Manager |

## Test Case Details

### Objective
Verify that a Risk Manager can review the risk dashboard, analyze key metrics, and configure risk thresholds.

### Preconditions
- User is logged in with Risk Manager role
- The user has permission to view risk metrics and configure thresholds
- Test transaction data and risk metrics are available in the system

### Test Data
- Risk Manager credentials: username = risk_manager, password = securepassword123

## Test Steps

| Step # | Step Description | Expected Result |
|--------|------------------|-----------------|
| 1 | Log in to the system using Risk Manager credentials | User is successfully logged in and redirected to the dashboard |
| 2 | Verify that the Risk Dashboard is displayed by default | Risk Dashboard is displayed with key risk metrics and visualizations |
| 3 | Check that the dashboard displays the following sections: Transaction Volume, Fraud Rate, AML Risk, and Rule Effectiveness | All required sections are displayed correctly |
| 4 | Verify that the Transaction Volume chart shows data for the last 30 days by default | Transaction Volume chart displays correct data for the last 30 days |
| 5 | Change the time period to "Last 7 days" using the date filter | Chart updates to show data for the last 7 days |
| 6 | Click on the "Fraud Rate" section to expand it | Fraud Rate section expands to show detailed metrics |
| 7 | Verify that the Fraud Rate section shows the current fraud rate and trend compared to the previous period | Fraud Rate metrics are displayed correctly with trend indicators |
| 8 | Click on the "View Details" button in the Fraud Rate section | Detailed Fraud Rate analysis page is displayed |
| 9 | Verify that the detailed analysis shows fraud rates by transaction type, channel, and merchant category | Detailed metrics are displayed correctly |
| 10 | Navigate back to the Risk Dashboard | Risk Dashboard is displayed again |
| 11 | Click on the "Configure Thresholds" button | Risk Threshold configuration page is displayed |
| 12 | Verify that the current thresholds for different risk categories are displayed | Current thresholds are displayed correctly |
| 13 | Change the "High Risk Transaction Amount Threshold" from the current value to 2000 USD | Threshold value is updated to 2000 USD |
| 14 | Change the "Fraud Rate Alert Threshold" from the current value to 0.5% | Threshold value is updated to 0.5% |
| 15 | Click "Save Changes" button | Changes are saved and a success message is displayed |
| 16 | Navigate back to the Risk Dashboard | Risk Dashboard is displayed again |
| 17 | Verify that the dashboard reflects the updated thresholds | Dashboard displays updated threshold values |
| 18 | Click on the "Generate Risk Report" button | Report generation dialog is displayed |
| 19 | Select "Monthly Risk Summary" from the report type dropdown | Report type is selected correctly |
| 20 | Select the current month from the date picker | Month is selected correctly |
| 21 | Click "Generate" button | Report is generated and a success message is displayed |
| 22 | Click on the download link in the success message | Report is downloaded successfully |
| 23 | Open the downloaded report | Report opens and contains the expected risk metrics and analysis |

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

## Issues Found

| Issue # | Issue Description | Severity | Priority | Status |
|---------|-------------------|----------|----------|--------|
| [To be filled if issues are found] | [To be filled if issues are found] | [To be filled if issues are found] | [To be filled if issues are found] | [To be filled if issues are found] |

## Additional Information

### Screenshots
[Screenshots will be added during test execution]

### Notes
This test case verifies the risk management functionality, which is critical for monitoring and controlling the overall risk exposure of the system.

## Sign-off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Tester | [To be filled after execution] | | |
| Business Analyst | [To be filled after execution] | | |
| Project Manager | [To be filled after execution] | | |