### 🔄 Unified Notion ↔ Spreadsheet Sync with Smart Matching and UI

> **Note:**  
> • Supports CSV, Excel (`.xls`, `.xlsx`), and ODS files  
> • Uses `Group_ID` as primary sync key when present (falls back to `Title`)  
> • Validates status values and preserves previous ones when missing or invalid  
> • Cleans up unnamed columns and fully empty rows  
> • Interactive UI in notebooks, CLI fallback outside

<details>
<summary>🛠️ Features & Behavior (click to expand)</summary>

- 🔁 **Bidirectional sync**: Export Notion to CSV, or import spreadsheet to Notion  
- 🔑 **Primary key logic**: Uses `Group_ID` for row matching; falls back to `Title` for legacy support  
- ✅ **Validates and normalizes**:
  - Rich text, select, status, and multi-select fields
  - Tag field handling via comma-separated values
- 🧼 **Spreadsheet hygiene**:
  - Handles encoding issues (UTF-8, ISO-8859-1, latin1)
  - Removes unnamed columns and fully blank rows
  - Warns on missing or duplicate `Title` entries
- 🧠 **Smart fallback for status mismatches**:
  - Preserves existing status when input is invalid
  - Maps `"Cancelled"` to `"Rejected"` if defined
  - Defaults new rows to `"New"` when available
- 🧪 **Rate-limited sync** with 0.4s delay per operation
- 🧑‍💻 **Runs as script or notebook widget UI** using `ipywidgets`

</details>