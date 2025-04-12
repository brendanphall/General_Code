# Usage Guide for Notion Sync Tool

This guide explains how to use the Notion Sync Tool to synchronize data between Notion databases and spreadsheet files.

## Basic Operations

### Running the Tool

The tool can be run in two ways:

1. **Command Line Interface (CLI)**
   ```bash
   python "Notion Sync.py"
   ```
   This will present a menu with options for different operations.

2. **Jupyter Notebook Interface**
   If you're running the script in a Jupyter notebook, it will automatically display an interactive widget interface.

### Available Operations

The tool provides three main operations:

1. **Export from Notion to CSV**
   - Exports all data from your Notion database to a CSV file
   - The default output file is `notion_feature_requests_backup.csv`
   - This creates a backup of your Notion data

2. **Import from Spreadsheet to Notion**
   - Imports data from a spreadsheet file into your Notion database
   - Supports CSV, Excel (.xlsx), and OpenDocument (.ods) formats
   - Updates existing entries and creates new ones as needed

3. **Exit**
   - Closes the application

## Exporting from Notion to CSV

### Steps

1. Run the tool and select option 1
2. The tool will connect to your Notion database
3. It will fetch all pages from the database
4. Data will be exported to the CSV file specified in the configuration
5. A success message will display the number of rows exported

### Output Format

The exported CSV file will contain the following columns:

- `id`: The Notion page ID
- `Name`: The title of the page
- `Status`: The current status of the item
- `Priority`: The priority level
- `Type`: The type of item
- `Description`: The detailed description
- `Requested By`: Who requested the item
- `Assigned To`: Who is assigned to the item
- `Created Time`: When the item was created
- `Last Edited Time`: When the item was last modified

## Importing from Spreadsheet to Notion

### Supported File Formats

- CSV files (.csv)
- Excel files (.xlsx)
- OpenDocument files (.ods)

### Required Columns

Your spreadsheet should contain at least these columns:

- `Name` (required): The title of the item
- `Status`: The current status
- `Priority`: The priority level
- `Type`: The type of item
- `Description`: The detailed description
- `Requested By`: Who requested the item
- `Assigned To`: Who is assigned to the item

### Import Process

1. Run the tool and select option 2
2. Enter the path to your spreadsheet file when prompted
3. The tool will:
   - Load and clean the data from your spreadsheet
   - Match existing items by name
   - Update existing items with new information
   - Create new items for entries that don't exist in Notion
4. Progress messages will show as rows are processed
5. A summary will display the number of rows processed

### Data Validation

During import, the tool performs several validations:

- Checks for required fields
- Validates status values against allowed options
- Validates priority values against allowed options
- Validates type values against allowed options
- Cleans text data by removing extra whitespace

## Field Mappings

The tool maps spreadsheet columns to Notion properties as follows:

| Spreadsheet Column | Notion Property | Type | Required |
|-------------------|-----------------|------|----------|
| Name | Title | Title | Yes |
| Status | Status | Status | No |
| Priority | Priority | Select | No |
| Type | Type | Select | No |
| Description | Description | Rich Text | No |
| Requested By | Requested By | Rich Text | No |
| Assigned To | Assigned To | Rich Text | No |

## Best Practices

### For Exporting

- Export regularly to maintain backups of your Notion data
- Use the exported CSV as a reference for the correct format when preparing import files

### For Importing

- Always include the `Name` column as it's used to match existing items
- Use the exact values for Status, Priority, and Type as they appear in Notion
- Keep descriptions concise but informative
- Use consistent formatting for dates and names

### General Tips

- Test imports with a small dataset first
- Review the exported CSV to understand the expected format
- Keep backups of your data before large imports
- Check the console output for any warnings or errors

## Troubleshooting

### Common Issues

1. **"File not found" error**
   - Verify the file path is correct
   - Ensure the file exists in the specified location
   - Check for typos in the filename

2. **"Invalid column names" error**
   - Ensure your spreadsheet has the required columns
   - Check that column names match exactly (case-sensitive)
   - Verify there are no extra spaces in column names

3. **"Authentication failed" error**
   - Check your Notion API key
   - Verify your integration has access to the database
   - Ensure your database ID is correct

4. **"No data to import" error**
   - Check that your spreadsheet contains data
   - Verify that the data is in the correct format
   - Ensure the file is not corrupted

### Getting Help

If you encounter issues not covered in this guide:

1. Check the console output for error messages
2. Verify your configuration settings
3. Ensure all dependencies are installed correctly
4. Check the [field mappings](field_mappings.md) document for detailed information 