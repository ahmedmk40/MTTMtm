# Case Management User Guide

## Introduction

The Case Management module is designed to help fraud analysts and compliance officers investigate suspicious transactions, document their findings, and collaborate on case resolution. This guide will walk you through the key features and workflows of the Case Management system.

## Getting Started

### Accessing the Case Management Module

1. Log in to the Transaction Monitoring System
2. Click on the "Cases" link in the main navigation menu
3. You will be taken to the Case List page, which displays all cases you have access to

### Understanding the Case List Page

The Case List page provides an overview of all cases in the system:

- **Case Statistics**: At the top of the page, you'll see statistics showing the total number of cases, as well as counts by status (Open, In Progress, Closed)
- **Filter Options**: Use the filter button to narrow down the list of cases by various criteria
- **Case Table**: The main table shows all cases with key information including Case ID, Title, Priority, Status, Created Date, and Assigned User
- **Actions**: Each case has action buttons for viewing details, editing, or performing other operations

## Creating a New Case

### Manual Case Creation

1. From the Case List page, click the "New Case" button
2. Fill in the required information:
   - **Title**: A descriptive title for the case
   - **Description**: Detailed information about the case
   - **Priority**: Select the appropriate priority level (Low, Medium, High, Critical)
   - **Status**: Initial status (typically "Open")
   - **Assign To**: Select a user to assign the case to (optional)
3. Click "Create Case" to save the new case

### Creating a Case from a Transaction

1. From the Transaction Detail page, click the "Create Case" button
2. The case creation form will open with the transaction pre-selected
3. Fill in the required case information
4. Click "Create Case" to save the new case with the linked transaction

## Working with Cases

### Viewing Case Details

1. From the Case List page, click on a case ID or the "View" button
2. The Case Detail page shows comprehensive information about the case:
   - **Case Summary**: Basic case information and status
   - **Description**: Detailed case description
   - **Tabs**: Navigate between Transactions, Notes, Attachments, and Activity

### Adding Transactions to a Case

1. From the Case Detail page, select the "Transactions" tab
2. Click the "Add Transaction" button
3. Enter one or more transaction IDs in the form
4. Click "Add Transaction" to link the transactions to the case

### Adding Notes to a Case

1. From the Case Detail page, select the "Notes" tab
2. Enter your note in the text field
3. Click "Add Note" to save the note to the case
4. Notes are displayed in chronological order with the newest at the top

### Adding Attachments to a Case

1. From the Case Detail page, select the "Attachments" tab
2. Click the "Add Attachment" button
3. Select a file from your computer
4. Add a description for the attachment (optional)
5. Click "Upload" to add the attachment to the case

### Viewing Case Activity

1. From the Case Detail page, select the "Activity" tab
2. View a chronological log of all actions taken on the case
3. Each activity entry shows the action, user, and timestamp

## Managing Cases

### Editing a Case

1. From the Case Detail page, click the "Edit" button
2. Update any case information as needed
3. Click "Save Changes" to update the case

### Assigning a Case

1. From the Case Detail page, click the "Assign" button next to the current assignment
2. Select a user from the dropdown list
3. Click "Assign" to update the case assignment

### Changing Case Status

1. From the Case Detail page, use the status dropdown or dedicated buttons
2. To mark a case as "In Progress", select that status from the dropdown
3. To close a case, click the "Close Case" button and select a resolution

### Closing a Case

1. From the Case Detail page, click the "Close Case" button
2. Select a resolution type:
   - **Confirmed Fraud**: Investigation confirms fraudulent activity
   - **False Positive**: Investigation determines no fraud occurred
   - **Inconclusive**: Unable to determine if fraud occurred
   - **Legitimate**: Transaction confirmed as legitimate
3. Add any closing notes
4. Click "Close Case" to finalize

### Reopening a Case

1. From a closed case's Detail page, click the "Reopen Case" button
2. The case status will change back to "Open"
3. Add a note explaining why the case was reopened

## Advanced Features

### Case Filtering

1. From the Case List page, click the "Filter" button
2. Set filter criteria:
   - **Case ID**: Filter by specific case ID
   - **Title**: Filter by text in the title
   - **Status**: Filter by case status
   - **Priority**: Filter by priority level
   - **Assigned To**: Filter by assigned user
   - **Date Range**: Filter by creation date
3. Click "Apply Filters" to update the case list

### Exporting Case Data

1. From the Case List page, click the "Export" button
2. Select the export format (CSV, Excel, PDF)
3. Choose what data to include in the export
4. Click "Export" to download the file

### Bulk Actions

1. From the Case List page, select multiple cases using the checkboxes
2. Use the "Bulk Actions" dropdown to select an action:
   - **Assign**: Assign multiple cases to a user
   - **Update Status**: Change status for multiple cases
   - **Update Priority**: Change priority for multiple cases
3. Complete the action in the popup dialog

## Best Practices

1. **Create Descriptive Titles**: Use clear, descriptive titles that summarize the case
2. **Document Everything**: Add detailed notes for all investigation steps
3. **Link All Relevant Transactions**: Ensure all related transactions are linked to the case
4. **Update Status Promptly**: Keep the case status current as investigation progresses
5. **Use Attachments Wisely**: Attach only relevant documents to keep cases organized
6. **Close Cases Properly**: Always select the appropriate resolution when closing a case

## Troubleshooting

### Common Issues

1. **Can't find a transaction**: Use the transaction search feature with various criteria
2. **Case not appearing in list**: Check your filter settings or permissions
3. **Can't add an attachment**: Verify the file size is within limits
4. **Can't close a case**: Ensure all required fields are completed

### Getting Help

For additional assistance:
- Click the "Help" icon in the top navigation
- Contact your system administrator
- Email support at support@transaction-monitoring.com