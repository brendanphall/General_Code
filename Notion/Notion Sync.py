"""
Notion Sync Tool

A Python utility for bidirectional synchronization between Notion databases and spreadsheet files.
This module provides functionality to export data from Notion to CSV files and import data from
spreadsheets (CSV, Excel, ODS) into Notion databases.

The tool uses smart matching with Group_ID as the primary key (falling back to Title if needed)
and includes intelligent handling of various data types and validation.

Example:
    >>> from notion_sync import run_sync
    >>> run_sync("1")  # Export Notion to CSV
    >>> run_sync("2", "data.csv")  # Import CSV to Notion

Dependencies:
    - notion-client: For interacting with the Notion API
    - pandas: For data manipulation and CSV handling
    - openpyxl/odfpy: For Excel/ODS file support
    - ipywidgets: For Jupyter notebook UI (optional)
"""

from notion_client import Client
import pandas as pd
import time
import sys
import os
import re

# 🔐 Configure
NOTION_TOKEN = "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"
DATABASE_ID = "1ad44833-084d-801b-9107-e32cfb219f33"
BACKUP_FILE = "notion_feature_requests_backup.csv"

notion = Client(auth=NOTION_TOKEN)


def text_block(text):
    """
    Create a rich text block for Notion properties.
    
    Args:
        text: The text content to convert to a Notion rich text block.
             Can be None, empty string, or any value that can be converted to string.
    
    Returns:
        list: A list containing a single rich text block dictionary, or an empty list
              if the input is None or empty.
    
    Example:
        >>> text_block("Hello World")
        [{'type': 'text', 'text': {'content': 'Hello World'}}]
        >>> text_block(None)
        []
    """
    # Convert to string and ensure it's not None/empty
    if text is None:
        return []

    text_str = str(text).strip()
    if not text_str:
        return []

    return [{"type": "text", "text": {"content": text_str}}]


def safe_rich_text(props, field):
    """
    Safely extract rich text content from Notion properties.
    
    Args:
        props (dict): The properties dictionary from a Notion page.
        field (str): The name of the field to extract.
    
    Returns:
        str: The concatenated plain text content of the rich text field,
             or an empty string if the field doesn't exist or has no content.
    
    Example:
        >>> props = {"Description": {"rich_text": [{"plain_text": "Hello"}, {"plain_text": "World"}]}}
        >>> safe_rich_text(props, "Description")
        'Hello World'
    """
    try:
        return " ".join([r["plain_text"] for r in props.get(field, {}).get("rich_text", [])])
    except Exception:
        return ""


def safe_select(props, field):
    """
    Safely extract select value from Notion properties.
    
    Args:
        props (dict): The properties dictionary from a Notion page.
        field (str): The name of the field to extract.
    
    Returns:
        str: The name of the selected option, or an empty string if no option is selected.
    
    Example:
        >>> props = {"Priority": {"select": {"name": "High"}}}
        >>> safe_select(props, "Priority")
        'High'
    """
    select_value = props.get(field, {}).get("select")
    return select_value.get("name") if select_value else ""


def safe_status(props, field):
    """
    Safely extract status value from Notion properties.
    
    Args:
        props (dict): The properties dictionary from a Notion page.
        field (str): The name of the field to extract.
    
    Returns:
        str: The name of the status, or an empty string if no status is set.
    
    Example:
        >>> props = {"Status": {"status": {"name": "In Progress"}}}
        >>> safe_status(props, "Status")
        'In Progress'
    """
    try:
        status_value = props.get(field, {}).get("status")
        if status_value:
            return status_value.get("name", "")
        return ""
    except Exception as e:
        print(f"⚠️ Error extracting status: {e}")
        return ""


def fetch_notion_pages():
    """
    Fetch all pages from the configured Notion database.
    
    This function handles pagination automatically, fetching all pages
    from the database specified by DATABASE_ID.
    
    Returns:
        list: A list of all page objects from the database.
    
    Example:
        >>> pages = fetch_notion_pages()
        >>> print(f"Found {len(pages)} pages")
        Found 42 pages
    """
    pages = []
    start_cursor = None
    while True:
        query = notion.databases.query(database_id=DATABASE_ID, start_cursor=start_cursor)
        pages.extend(query["results"])
        if not query.get("has_more"):
            break
        start_cursor = query["next_cursor"]
    return pages


def notion_to_csv():
    """
    Export data from Notion to a CSV file.
    
    This function fetches all pages from the configured Notion database,
    extracts their properties, and saves them to a CSV file specified by
    BACKUP_FILE. The function handles various property types including
    rich text, select, status, and multi-select fields.
    
    The exported CSV will have the following columns:
    - # (Group_ID)
    - Title
    - Status
    - Priority
    - Expected Changes
    - General Notes
    - Estimate
    - Cost
    - Feature Request Response
    - Tags
    
    Returns:
        None
    
    Example:
        >>> notion_to_csv()
        📥 Exporting Notion → CSV...
        ✅ Notion data exported to `notion_feature_requests_backup.csv`
    """
    print("📥 Exporting Notion → CSV...")
    pages = fetch_notion_pages()
    notion_lookup = {}
    
    # Create lookup by composite key (Group_ID + Tags) instead of just Group_ID
    for page in pages:
        props = page.get("properties", {})
        group_id = ""
        if "Group_ID" in props:
            group_id_prop = props["Group_ID"]
            if group_id_prop.get("type") == "rich_text" and group_id_prop.get("rich_text"):
                group_id = " ".join([r["plain_text"] for r in group_id_prop["rich_text"]])
        
        # Get Tags
        tags = []
        if "Tags" in props and props["Tags"].get("type") == "multi_select":
            tags = [t.get("name", "") for t in props["Tags"].get("multi_select", [])]
        
        # Create composite key
        composite_key = f"{group_id}|{','.join(sorted(tags))}" if group_id and tags else ""
        
        # Only add to lookup if composite key exists
        if composite_key:
            notion_lookup[composite_key] = page
        else:
            # For backward compatibility, also store by Title if no composite key
            if "Title" in props and props["Title"].get("title"):
                title = props["Title"]["title"][0]["plain_text"]
                notion_lookup[title] = page

    backup = []
    for identifier, page in notion_lookup.items():
        props = page.get("properties", {})

        # Get Group_ID if it exists
        group_id = ""
        if "Group_ID" in props:
            group_id_prop = props["Group_ID"]
            if group_id_prop.get("type") == "rich_text" and group_id_prop.get("rich_text"):
                group_id = " ".join([r["plain_text"] for r in group_id_prop["rich_text"]])

        # Get Title
        title = ""
        if "Title" in props and props["Title"].get("title"):
            title = props["Title"]["title"][0]["plain_text"]

        backup.append({
            "#": group_id,  # Map Group_ID to # column
            "Title": title,
            "Status": safe_status(props, "Status"),
            "Priority": safe_select(props, "Priority"),
            "Expected Changes": safe_rich_text(props, "Expected Changes"),
            "General Notes": safe_rich_text(props, "General Notes"),
            "Estimate": safe_rich_text(props, "Estimate"),
            "Cost": safe_rich_text(props, "Cost"),
            "Feature Request Response": safe_rich_text(props, "Feature request response"),
            "Tags": ", ".join(t.get("name") for t in props.get("Tags", {}).get("multi_select", []))
        })

    pd.DataFrame(backup).to_csv(BACKUP_FILE, index=False)
    print(f"✅ Notion data exported to `{BACKUP_FILE}`")


def load_spreadsheet(file_path):
    """
    Load data from various spreadsheet formats.
    
    This function supports CSV, Excel (.xls, .xlsx), and ODS files.
    It handles encoding issues by trying multiple encodings (UTF-8, ISO-8859-1, latin1)
    and performs data cleaning by removing unnamed columns and fully empty rows.
    
    Args:
        file_path (str): Path to the spreadsheet file.
    
    Returns:
        pandas.DataFrame: The loaded and processed data.
    
    Raises:
        ValueError: If the file format is unsupported or required columns are missing.
        FileNotFoundError: If the file doesn't exist.
    
    Example:
        >>> data = load_spreadsheet("data.csv")
        📄 Loading spreadsheet from: data.csv
        ✅ Loaded 42 rows using UTF-8.
        >>> print(data.head())
        #  Title  Status  Priority  ...
        1  Feature 1  In Progress  High  ...
        2  Feature 2  New  Medium  ...
    """
    print(f"📄 Loading spreadsheet from: {file_path}")
    ext = os.path.splitext(file_path)[1].lower()

    try:
        # Force string type for all columns
        if ext == '.csv':
            try:
                # Try with UTF-8 first
                data = pd.read_csv(file_path, encoding="utf-8", dtype=str).fillna("")
                print(f"✅ Loaded {len(data)} rows using UTF-8.")
            except UnicodeDecodeError as e:
                print(f"⚠️ UTF-8 decode failed: {e}")
                try:
                    # Try with ISO-8859-1 next
                    data = pd.read_csv(file_path, encoding="ISO-8859-1", dtype=str).fillna("")
                    print(f"✅ Loaded {len(data)} rows using ISO-8859-1.")
                except Exception as e2:
                    print(f"⚠️ ISO-8859-1 decode failed: {e2}")
                    # Try with latin1 as a last resort
                    data = pd.read_csv(file_path, encoding="latin1", dtype=str).fillna("")
                    print(f"✅ Loaded {len(data)} rows using latin1.")
        elif ext == '.ods':
            data = pd.read_excel(file_path, engine="odf", dtype=str).fillna("")
            print(f"✅ Loaded {len(data)} rows from ODS file.")
        elif ext in ['.xls', '.xlsx']:
            data = pd.read_excel(file_path, dtype=str).fillna("")
            print(f"✅ Loaded {len(data)} rows from Excel file.")
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        # Remove unnamed columns
        unnamed_cols = [col for col in data.columns if col.startswith('Unnamed:')]
        if unnamed_cols:
            print(f"⚠️ Removing {len(unnamed_cols)} unnamed columns")
            data = data.drop(columns=unnamed_cols)
        
        # Check for required columns
        required_columns = ['Title']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            print(f"⚠️ Missing required columns: {', '.join(missing_columns)}")
            print(f"⚠️ Available columns: {', '.join(data.columns)}")
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")

        # Remove completely empty rows (where all values are empty strings)
        empty_rows_before = len(data)
        data = data[~data.apply(lambda row: row.astype(str).str.strip().eq('').all(), axis=1)]
        empty_rows_removed = empty_rows_before - len(data)
        if empty_rows_removed > 0:
            print(f"✅ Removed {empty_rows_removed} completely empty rows")

        # Create columns dict for the new dataframe
        columns_dict = {}

        # Copy all columns except special ones
        for col in data.columns:
            if col not in ['#', 'nathan']:
                columns_dict[col] = data[col]

        # Handle special columns
        if 'nathan' in data.columns:
            columns_dict['Feature Request Response'] = data['nathan']
            print("✅ Mapped 'nathan' column to 'Feature Request Response'")

        if '#' in data.columns:
            columns_dict['Group_ID'] = data['#']

        # Create new dataframe in one operation to avoid fragmentation
        processed_data = pd.DataFrame(columns_dict)
        
        # Check for empty dataframe
        if processed_data.empty:
            print("⚠️ Warning: The processed dataframe is empty!")
        else:
            print(f"✅ Successfully processed {len(processed_data)} rows")
            
        # Check for duplicate titles
        if 'Title' in processed_data.columns:
            duplicates = processed_data[processed_data.duplicated(subset=['Title'], keep=False)]
            if not duplicates.empty:
                print(f"⚠️ Warning: Found {len(duplicates)} rows with duplicate titles:")
                for title, count in duplicates['Title'].value_counts().items():
                    if count > 1:
                        print(f"   - '{title}' appears {count} times")

        return processed_data

    except Exception as e:
        print(f"❌ Failed to load spreadsheet: {e}")
        raise


def spreadsheet_to_notion(file_path):
    """
    Import data from a spreadsheet file into a Notion database.
    
    This function loads data from a spreadsheet file, cleans it up,
    and syncs it with the configured Notion database. It uses a composite key
    of Group_ID and Tags as the primary key for matching rows to existing pages,
    falling back to Title if the composite key is not available.
    
    Args:
        file_path (str): Path to the spreadsheet file (CSV, Excel, or ODS).
    
    Returns:
        None
    
    Raises:
        FileNotFoundError: If the specified file doesn't exist.
        ValueError: If the file format is unsupported or required columns are missing.
    
    Example:
        >>> spreadsheet_to_notion("data.csv")
        📤 Importing Spreadsheet → Notion...
        📄 Loading spreadsheet from: data.csv
        ✅ Loaded 42 rows using UTF-8.
        ✅ Removed empty rows, 40 rows remaining
        📚 Found 35 existing pages in Notion
        ✅ Found valid status options: New, In Progress, Done, Rejected
        🔄 Processing 40 rows...
        🔄 Progress: 10/40 rows processed
        🔄 Progress: 20/40 rows processed
        🔄 Progress: 30/40 rows processed
        🔄 Progress: 40/40 rows processed
        ✅ All 40 rows were processed
        ✅ Spreadsheet Sync Done: 5 created, 35 updated, 0 skipped.
    """
    print("📤 Importing Spreadsheet → Notion...")
    
    if not os.path.isfile(file_path):
        print(f"❌ File `{file_path}` does not exist on disk.")
        return

    # Load spreadsheet data
    try:
        data = load_spreadsheet(file_path)
        print(f"📊 Total rows loaded from spreadsheet: {len(data)}")
    except Exception as e:
        print(f"❌ Failed to process spreadsheet: {e}")
        return

    # Clean up data - remove empty rows
    data = data.dropna(subset=['Title'], how='all')
    print(f"✅ Removed empty rows, {len(data)} rows remaining")

    # Fetch existing Notion pages
    pages = fetch_notion_pages()
    notion_lookup = {}
    
    # Create lookup by composite key (Group_ID + Tags) instead of just Group_ID
    for page in pages:
        props = page.get("properties", {})
        group_id = ""
        if "Group_ID" in props:
            group_id_prop = props["Group_ID"]
            if group_id_prop.get("type") == "rich_text" and group_id_prop.get("rich_text"):
                group_id = " ".join([r["plain_text"] for r in group_id_prop["rich_text"]])
        
        # Get Tags
        tags = []
        if "Tags" in props and props["Tags"].get("type") == "multi_select":
            tags = [t.get("name", "") for t in props["Tags"].get("multi_select", [])]
        
        # Create composite key
        composite_key = f"{group_id}|{','.join(sorted(tags))}" if group_id and tags else ""
        
        # Only add to lookup if composite key exists
        if composite_key:
            notion_lookup[composite_key] = page
        else:
            # For backward compatibility, also store by Title if no composite key
            if "Title" in props and props["Title"].get("title"):
                title = props["Title"]["title"][0]["plain_text"]
                notion_lookup[title] = page
    
    print(f"📚 Found {len(notion_lookup)} existing pages in Notion")

    # Get valid status options from database metadata
    valid_statuses = []
    try:
        database = notion.databases.retrieve(database_id=DATABASE_ID)
        status_property = database["properties"].get("Status", {})
        if status_property and status_property.get("type") == "status":
            valid_statuses = [option["name"] for option in status_property["status"]["options"]]
            print(f"✅ Found valid status options: {', '.join(valid_statuses)}")
    except Exception as e:
        print(f"⚠️ Failed to retrieve valid status options: {e}")

    created, updated, skipped = 0, 0, 0
    row_count = 0
    total_rows = len(data)
    
    print(f"🔄 Processing {total_rows} rows...")

    # Iterate rows in spreadsheet
    for index, row in data.iterrows():
        row_count += 1
        
        # Check if Title exists and is not empty
        if "Title" not in row:
            skipped += 1
            continue
            
        title = row["Title"] if pd.notna(row["Title"]) else None

        # Skip rows without a title
        if not title or str(title).strip() == "":
            skipped += 1
            continue

        # Get Group_ID if it exists
        group_id = None
        if "Group_ID" in row and pd.notna(row["Group_ID"]) and str(row["Group_ID"]).strip():
            group_id = str(row["Group_ID"]).strip()
        
        # Get Tags if they exist
        tags = []
        if "Tags" in row and pd.notna(row["Tags"]) and str(row["Tags"]).strip():
            tags = [t.strip() for t in str(row["Tags"]).split(",") if t.strip()]
        
        # Create composite key
        composite_key = f"{group_id}|{','.join(sorted(tags))}" if group_id and tags else None
        
        # Use composite key as primary key if available, otherwise fall back to Title
        identifier = composite_key if composite_key else title
        existing = notion_lookup.get(identifier)
        
        properties = {
            "Title": {"title": text_block(title)}
        }

        # Add Group_ID field if it exists in the data
        if group_id:
            properties["Group_ID"] = {"rich_text": text_block(group_id)}

        # Rich text fields
        rich_text_fields = {
            "Expected Changes": "Expected Changes",
            "General Notes": "General Notes",
            "Estimate": "Estimate",
            "Cost": "Cost",
            "Feature Request Response": "Feature request response"
        }

        for csv_field, notion_field in rich_text_fields.items():
            if csv_field in row and pd.notna(row[csv_field]) and str(row[csv_field]).strip():
                properties[notion_field] = {"rich_text": text_block(str(row[csv_field]))}

        # Status field - validate and preserve existing status
        if "Status" in row and pd.notna(row["Status"]) and str(row["Status"]).strip():
            status_value = str(row["Status"]).strip()

            # Check if status is valid
            if valid_statuses and status_value not in valid_statuses:
                # Get existing status if available
                existing_status = ""
                try:
                    existing_props = existing.get("properties", {}) if existing else {}
                    if "Status" in existing_props:
                        existing_status = safe_status(existing_props, "Status")
                        if existing_status and existing_status in valid_statuses:
                            properties["Status"] = {"status": {"name": existing_status}}
                except Exception as e:
                    print(f"⚠️ Error getting existing status: {e}")

                # Fallback if no existing status
                if "Status" not in properties:
                    # Map 'Cancelled' to 'Rejected' if available
                    if status_value == "Cancelled" and "Rejected" in valid_statuses:
                        properties["Status"] = {"status": {"name": "Rejected"}}
                    # Otherwise use New as fallback
                    elif "New" in valid_statuses:
                        properties["Status"] = {"status": {"name": "New"}}
            else:
                # Use valid status from spreadsheet
                properties["Status"] = {"status": {"name": status_value}}

        # For new items, always set a status
        elif not existing and ("Status" not in properties) and valid_statuses:
            if "New" in valid_statuses:
                properties["Status"] = {"status": {"name": "New"}}

        # Priority field
        if "Priority" in row and pd.notna(row["Priority"]) and str(row["Priority"]).strip():
            priority_value = str(row["Priority"]).strip()
            properties["Priority"] = {"select": {"name": priority_value}}

        # Tags field
        if "Tags" in row and pd.notna(row["Tags"]) and str(row["Tags"]).strip():
            tags = [t.strip() for t in str(row["Tags"]).split(",") if t.strip()]
            properties["Tags"] = {"multi_select": [{"name": tag} for tag in tags]}

        try:
            if existing:
                notion.pages.update(page_id=existing["id"], properties=properties)
                updated += 1
            else:
                notion.pages.create(parent={"database_id": DATABASE_ID}, properties=properties)
                created += 1
        except Exception as e:
            print(f"❌ Failed to sync '{identifier}': {e}")
            skipped += 1

        # Show progress every 10 rows
        if row_count % 10 == 0 or row_count == total_rows:
            print(f"🔄 Progress: {row_count}/{total_rows} rows processed")

        time.sleep(0.4)

    # Verify that all rows were processed
    processed = created + updated + skipped
    if processed != total_rows:
        print(f"⚠️ Warning: Processed {processed} rows but expected {total_rows} rows")
        print(f"⚠️ Created: {created}, Updated: {updated}, Skipped: {skipped}")
    else:
        print(f"✅ All {total_rows} rows were processed")

    print(f"\n✅ Spreadsheet Sync Done: {created} created, {updated} updated, {skipped} skipped.")


# 🧠 Main Entry
def run_sync(choice, file_path=None):
    """
    Run the Notion sync operation based on user choice.
    
    Args:
        choice (str): The operation to perform.
                     "1" for exporting Notion to CSV.
                     "2" for importing a spreadsheet to Notion.
        file_path (str, optional): Path to the spreadsheet file for import.
                                  Required when choice is "2".
    
    Returns:
        None
    
    Example:
        >>> run_sync("1")  # Export Notion to CSV
        >>> run_sync("2", "data.csv")  # Import CSV to Notion
    """
    if choice == "1":
        notion_to_csv()
    elif choice == "2":
        if not file_path:
            print("❌ No input file specified.")
            return
        spreadsheet_to_notion(file_path)
    else:
        print("❌ Invalid option.")


def is_running_in_notebook():
    """
    Check if the code is running in a Jupyter notebook.
    
    Returns:
        bool: True if running in a notebook, False otherwise.
    
    Example:
        >>> is_running_in_notebook()
        False
    """
    try:
        from IPython import get_ipython
        return get_ipython() is not None
    except ImportError:
        return False


def launch_interface():
    """
    Launch the appropriate interface based on the environment.
    
    If running in a Jupyter notebook, launches an interactive widget UI.
    Otherwise, launches a command-line interface.
    
    Returns:
        None
    
    Example:
        >>> launch_interface()
        🔁 Notion Sync Utility
        1 - Export Notion → CSV
        2 - Import Spreadsheet → Notion
        Select an option (1 or 2):
    """
    if is_running_in_notebook():
        from ipywidgets import Dropdown, Button, VBox, Output, HBox, Text
        from IPython.display import display

        options = {
            "Export Notion → CSV": "1",
            "Import Spreadsheet → Notion": "2"
        }

        dropdown = Dropdown(
            options=options,
            description="Sync Mode:",
            style={'description_width': 'initial'},
            layout={'width': '300px'}
        )

        file_input = Text(
            value="",
            placeholder="Path to input file (.csv, .ods, .xls, .xlsx)",
            description="File:",
            style={'description_width': 'initial'},
            layout={'width': '500px'}
        )

        button = Button(
            description="Run Sync",
            button_style='success',
            tooltip="Click to begin sync",
            layout={'width': '150px'}
        )

        out = Output()

        def on_click(b):
            with out:
                out.clear_output()
                choice = dropdown.value
                file_path = file_input.value.strip() if file_input.value.strip() else None
                print(f"🔃 Running '{dropdown.label}'...\n")
                run_sync(choice, file_path)

        button.on_click(on_click)

        display(VBox([HBox([dropdown]), file_input, button, out]))

    else:
        print("🔁 Notion Sync Utility")
        print("1 - Export Notion → CSV")
        print("2 - Import Spreadsheet → Notion")
        choice = input("Select an option (1 or 2): ").strip()

        file_path = None
        if choice == "2":
            file_path = input("Enter path to input file (.csv, .ods, .xls, .xlsx): ").strip()
            if not file_path:
                print("❌ No input file specified.")
                return

        run_sync(choice, file_path)


if __name__ == "__main__" or is_running_in_notebook():
    launch_interface()