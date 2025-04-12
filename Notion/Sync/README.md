# 🔄 Notion Sync Tool

A powerful Python utility for bidirectional synchronization between Notion databases and spreadsheet files (CSV, Excel, ODS).

[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## 📋 Overview

The Notion Sync Tool allows you to:
- Export data from Notion databases to spreadsheet files
- Import data from spreadsheets into Notion databases
- Maintain data consistency with smart matching using Group_ID or Title
- Handle various data types and formats with intelligent validation

## ✨ Features

- 🔁 **Bidirectional Sync**: Export Notion to CSV or import spreadsheet to Notion
- 📊 **Multiple Format Support**: Works with CSV, Excel (`.xls`, `.xlsx`), and ODS files
- 🔑 **Smart Matching**: Uses `Group_ID` as primary key when present (falls back to `Title`)
- ✅ **Data Validation**: Handles rich text, select, status, and multi-select fields
- 🧼 **Spreadsheet Hygiene**: Removes unnamed columns and fully empty rows
- 🧠 **Intelligent Status Handling**: Preserves existing status when input is invalid
- 🧪 **Rate-Limited Operations**: Prevents API throttling with 0.4s delay per operation
- 🧑‍💻 **Multiple Interfaces**: Runs as script or notebook widget UI using `ipywidgets`

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- Notion API key
- Notion database ID

### Installation

1. Clone this repository or download the files
2. Install required dependencies:

```bash
pip install notion-client pandas openpyxl odfpy ipywidgets
```

### Configuration

Edit the `Notion Sync.py` file to set your Notion API key and database ID:

```python
# 🔐 Configure
NOTION_TOKEN = "your_notion_api_key_here"
DATABASE_ID = "your_database_id_here"
BACKUP_FILE = "notion_feature_requests_backup.csv"
```

### Usage

#### Command Line Interface

```bash
# Run the script
python "Notion Sync.py"

# Choose an option:
# 1 - Export Notion → CSV
# 2 - Import Spreadsheet → Notion
```

#### Jupyter Notebook Interface

Open `notion.ipynb` in Jupyter to use the interactive widget interface.

## 📝 Detailed Documentation

For more detailed information, see:
- [Setup Guide](notion%20sync.md#setup)
- [Usage Examples](notion%20sync.md#examples)
- [API Reference](notion%20sync.md#api)

## 🔧 How It Works

### Export Process (Notion → CSV)
1. Fetches all pages from the specified Notion database
2. Extracts properties and converts them to spreadsheet format
3. Saves data to a CSV file with appropriate column headers

### Import Process (CSV → Notion)
1. Loads data from the spreadsheet file
2. Cleans up data (removes empty rows, handles encoding issues)
3. Matches rows to existing Notion pages using Group_ID or Title
4. Updates existing pages or creates new ones as needed
5. Validates and normalizes data before sending to Notion

### Smart Matching Logic
- Primary key: `Group_ID` (if present)
- Fallback key: `Title` (for backward compatibility)
- Creates new pages when no match is found

## 🧩 Field Mapping

| Spreadsheet Column | Notion Property | Type |
|-------------------|-----------------|------|
| `#` | `Group_ID` | Rich Text |
| `Title` | `Title` | Title |
| `Status` | `Status` | Status |
| `Priority` | `Priority` | Select |
| `Expected Changes` | `Expected Changes` | Rich Text |
| `General Notes` | `General Notes` | Rich Text |
| `Estimate` | `Estimate` | Rich Text |
| `Cost` | `Cost` | Rich Text |
| `Feature Request Response` | `Feature request response` | Rich Text |
| `Tags` | `Tags` | Multi-select |

## 🔍 Troubleshooting

### Common Issues

- **API Rate Limits**: The tool includes a 0.4s delay between operations to prevent rate limiting
- **Encoding Issues**: The tool tries multiple encodings (UTF-8, ISO-8859-1, latin1) to handle different file formats
- **Missing Columns**: The tool requires a `Title` column and will warn about missing required columns
- **Invalid Status Values**: The tool will preserve existing status values when invalid values are provided

### Getting Help

If you encounter issues:
1. Check that your Notion API key and database ID are correct
2. Ensure your spreadsheet has the required columns
3. Verify that your Notion database has the expected property types

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Notion API](https://developers.notion.com/) for providing the API
- [notion-client](https://github.com/ramnes/notion-sdk-py) Python library
- [pandas](https://pandas.pydata.org/) for data manipulation