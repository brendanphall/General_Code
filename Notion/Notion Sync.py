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
    """Create a rich text block for Notion properties."""
    # Convert to string and ensure it's not None/empty
    if text is None:
        return []

    text_str = str(text).strip()
    if not text_str:
        return []

    return [{"type": "text", "text": {"content": text_str}}]


def safe_rich_text(props, field):
    try:
        return " ".join([r["plain_text"] for r in props.get(field, {}).get("rich_text", [])])
    except Exception:
        return ""


def safe_select(props, field):
    select_value = props.get(field, {}).get("select")
    return select_value.get("name") if select_value else ""


def safe_status(props, field):
    status_value = props.get(field, {}).get("status")
    return status_value.get("name") if status_value else ""


def fetch_notion_pages():
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
    print("📥 Exporting Notion → CSV...")
    pages = fetch_notion_pages()
    notion_lookup = {
        page["properties"]["Title"]["title"][0]["plain_text"]: page
        for page in pages if page["properties"]["Title"]["title"]
    }

    backup = []
    for title, page in notion_lookup.items():
        props = page.get("properties", {})

        # Get Group_ID if it exists
        group_id = ""
        if "Group_ID" in props:
            group_id_prop = props["Group_ID"]
            if group_id_prop.get("type") == "rich_text" and group_id_prop.get("rich_text"):
                group_id = " ".join([r["plain_text"] for r in group_id_prop["rich_text"]])

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
    """Load data from various spreadsheet formats."""
    print(f"📄 Loading spreadsheet from: {file_path}")
    ext = os.path.splitext(file_path)[1].lower()

    try:
        # Force string type for all columns
        if ext == '.csv':
            try:
                data = pd.read_csv(file_path, encoding="utf-8", dtype=str).fillna("")
                print(f"✅ Loaded {len(data)} rows using UTF-8.")
            except UnicodeDecodeError as e:
                print(f"⚠️ UTF-8 decode failed: {e}")
                data = pd.read_csv(file_path, encoding="ISO-8859-1", dtype=str).fillna("")
                print(f"✅ Loaded {len(data)} rows using ISO-8859-1.")
        elif ext == '.ods':
            data = pd.read_excel(file_path, engine="odf", dtype=str).fillna("")
            print(f"✅ Loaded {len(data)} rows from ODS file.")
        elif ext in ['.xls', '.xlsx']:
            data = pd.read_excel(file_path, dtype=str).fillna("")
            print(f"✅ Loaded {len(data)} rows from Excel file.")
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        # Print column names for debugging
        print(f"📊 Columns found in spreadsheet: {', '.join(data.columns)}")

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
            # Show first few values for debugging
            print(f"✅ Mapped '#' column to 'Group_ID' with values: {data['#'].head(3).tolist()}")

        # Create new dataframe in one operation to avoid fragmentation
        processed_data = pd.DataFrame(columns_dict)

        return processed_data

    except Exception as e:
        print(f"❌ Failed to load spreadsheet: {e}")
        raise


def spreadsheet_to_notion(file_path):
    print("📤 Importing Spreadsheet → Notion...")
    print(f"📂 Checking file: {file_path}")
    print(f"🧪 File exists? {os.path.isfile(file_path)}")
    print(f"📍 Working directory: {os.getcwd()}")

    if not os.path.isfile(file_path):
        print(f"❌ File `{file_path}` does not exist on disk.")
        return

    # Load spreadsheet data
    try:
        data = load_spreadsheet(file_path)
    except Exception as e:
        print(f"❌ Failed to process spreadsheet: {e}")
        return

    # Clean up data - remove empty rows
    data = data.dropna(subset=['Title'], how='all')
    print(f"✅ Removed empty rows, {len(data)} rows remaining")

    # Fetch existing Notion pages
    pages = fetch_notion_pages()
    notion_lookup = {
        page["properties"]["Title"]["title"][0]["plain_text"]: page
        for page in pages if page["properties"]["Title"]["title"]
    }

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

    # Iterate rows in spreadsheet
    for _, row in data.iterrows():
        title = row["Title"] if "Title" in row and pd.notna(row["Title"]) else None

        # Skip rows without a title
        if not title or str(title).strip() == "":
            print("⚠️ Skipping row with no title")
            skipped += 1
            continue

        existing = notion_lookup.get(title)

        print(f"🔍 Processing row: {title}")
        properties = {
            "Title": {"title": text_block(title)}
        }

        # Add Group_ID field if it exists in the data
        if "Group_ID" in row and pd.notna(row["Group_ID"]) and str(row["Group_ID"]).strip():
            group_id_value = str(row["Group_ID"]).strip()
            # For Group_ID, always use rich_text format
            properties["Group_ID"] = {"rich_text": text_block(group_id_value)}
            print(f"✅ Added Group_ID: {group_id_value}")

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
                print(
                    f"✅ Added {notion_field}: {str(row[csv_field])[:30]}{'...' if len(str(row[csv_field])) > 30 else ''}")

        # Status field - validate and preserve existing status
        if existing and "Status" in row and pd.notna(row["Status"]) and str(row["Status"]).strip():
            status_value = str(row["Status"]).strip()

            # Check if status is valid
            if valid_statuses and status_value not in valid_statuses:
                print(f"⚠️ Invalid status '{status_value}'. Valid options are: {', '.join(valid_statuses)}")

                # Get existing status if available
                existing_status = ""
                try:
                    existing_props = existing.get("properties", {})
                    if "Status" in existing_props:
                        existing_status = safe_status(existing_props, "Status")
                        if existing_status and existing_status in valid_statuses:
                            print(f"✅ Keeping existing status: {existing_status}")
                            properties["Status"] = {"status": {"name": existing_status}}
                except Exception:
                    pass

                # Fallback if no existing status
                if "Status" not in properties:
                    # Map 'Cancelled' to 'Rejected' if available
                    if status_value == "Cancelled" and "Rejected" in valid_statuses:
                        print(f"⚠️ Mapping 'Cancelled' to 'Rejected'")
                        properties["Status"] = {"status": {"name": "Rejected"}}
                    # Otherwise use New as fallback
                    elif "New" in valid_statuses:
                        print(f"⚠️ Using 'New' as fallback status")
                        properties["Status"] = {"status": {"name": "New"}}
            else:
                # Use valid status from spreadsheet
                properties["Status"] = {"status": {"name": status_value}}
                print(f"✅ Using status: {status_value}")

        # For new items, always set a status
        elif not existing and ("Status" not in properties) and valid_statuses:
            print(f"⚠️ No valid status for new item, using 'New'")
            if "New" in valid_statuses:
                properties["Status"] = {"status": {"name": "New"}}

        # Priority field
        if "Priority" in row and pd.notna(row["Priority"]) and str(row["Priority"]).strip():
            properties["Priority"] = {"select": {"name": str(row["Priority"]).strip()}}

        # Tags field
        if "Tags" in row and pd.notna(row["Tags"]) and str(row["Tags"]).strip():
            tags = [t.strip() for t in str(row["Tags"]).split(",") if t.strip()]
            properties["Tags"] = {"multi_select": [{"name": tag} for tag in tags]}

        try:
            if existing:
                notion.pages.update(page_id=existing["id"], properties=properties)
                print(f"🔄 Updated: {title}")
                updated += 1
            else:
                notion.pages.create(parent={"database_id": DATABASE_ID}, properties=properties)
                print(f"➕ Created: {title}")
                created += 1
        except Exception as e:
            print(f"❌ Failed to sync '{title}': {e}")
            skipped += 1

        time.sleep(0.4)

    print(f"\n✅ Spreadsheet Sync Done: {created} created, {updated} updated, {skipped} skipped.")


# 🧠 Main Entry
def run_sync(choice, file_path=None):
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
    try:
        from IPython import get_ipython
        return get_ipython() is not None
    except ImportError:
        return False


def launch_interface():
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