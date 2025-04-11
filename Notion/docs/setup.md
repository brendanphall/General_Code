# Setup Guide for Notion Sync Tool

This guide will help you set up the Notion Sync Tool for your environment.

## Prerequisites

Before you begin, ensure you have:

- Python 3.7 or higher installed
- A Notion account with access to the database you want to sync
- A Notion integration with appropriate permissions

## Installation

### 1. Clone or Download the Repository

```bash
git clone https://github.com/yourusername/notion-sync.git
cd notion-sync
```

Or download the files directly and extract them to your desired location.

### 2. Install Required Dependencies

```bash
pip install notion-client pandas openpyxl odfpy ipywidgets
```

### 3. Configure Your Notion Integration

1. Go to [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations)
2. Click "New integration"
3. Give your integration a name (e.g., "Notion Sync Tool")
4. Select the workspace where your database is located
5. Click "Submit" to create the integration
6. Copy the "Internal Integration Token" that is displayed

### 4. Share Your Database with the Integration

1. Open your Notion database in a browser
2. Click the "..." menu in the top right corner
3. Select "Add connections"
4. Find and select your integration from the list
5. Click "Confirm" to grant access

### 5. Get Your Database ID

1. Open your Notion database in a browser
2. The URL will look like: `https://www.notion.so/workspace/1ad44833-084d-801b-9107-e32cfb219f33?v=...`
3. Copy the ID part: `1ad44833-084d-801b-9107-e32cfb219f33`

### 6. Configure the Script

Edit the `Notion Sync.py` file to set your Notion API key and database ID:

```python
# 🔐 Configure
NOTION_TOKEN = "your_notion_api_key_here"
DATABASE_ID = "your_database_id_here"
BACKUP_FILE = "notion_feature_requests_backup.csv"
```

Replace:
- `your_notion_api_key_here` with the token you copied in step 3
- `your_database_id_here` with the database ID you copied in step 5
- Optionally, change `BACKUP_FILE` to your preferred backup file name

## Verifying Your Setup

To verify that your setup is working correctly:

1. Run the script:
   ```bash
   python "Notion Sync.py"
   ```

2. Choose option 1 to export from Notion to CSV
   - If successful, you should see a message indicating that data was exported
   - Check that the CSV file was created with the expected data

3. Choose option 2 to import from CSV to Notion
   - Provide the path to a CSV file with the correct format
   - If successful, you should see messages about rows being processed

## Troubleshooting Setup Issues

### API Key Issues

If you see errors related to authentication:

- Verify that you've copied the correct API key
- Ensure there are no extra spaces or characters
- Check that your integration is still active in Notion

### Database Access Issues

If you see errors about not being able to access the database:

- Verify that you've shared the database with your integration
- Check that the database ID is correct
- Ensure your integration has the necessary permissions

### Dependency Issues

If you encounter errors about missing modules:

- Verify that all dependencies are installed correctly
- Try reinstalling the dependencies:
  ```bash
  pip install --upgrade notion-client pandas openpyxl odfpy ipywidgets
  ```

## Next Steps

Once you've completed the setup, you can:

- [Learn how to use the tool](usage.md)
- [Understand the field mappings](field_mappings.md)
- [Explore advanced features](advanced_features.md) 