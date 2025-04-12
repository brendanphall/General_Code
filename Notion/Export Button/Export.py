"""
Notion Database to Excel Export Script

This script:
1. Connects to the Notion API
2. Retrieves data from a specified database
3. Processes the data into a pandas DataFrame
4. Formats and exports the data to an Excel file
5. Returns a download link or sends the file via email
"""

import os
import requests
import pandas as pd
from datetime import datetime
from flask import Flask, request, jsonify, send_file
import json
import tempfile
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# Create Flask app for webhook endpoint
app = Flask(__name__)

# Notion API configuration
NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

class NotionClient:
    def __init__(self, token):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
    
    def query_database(self, database_id, filter_params=None):
        """Query a Notion database and return all results"""
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        
        payload = {}
        if filter_params:
            payload.update(filter_params)
        
        all_results = []
        has_more = True
        next_cursor = None
        
        while has_more:
            if next_cursor:
                payload["start_cursor"] = next_cursor
                
            response = requests.post(url, json=payload, headers=self.headers)
            data = response.json()
            
            if response.status_code != 200:
                raise Exception(f"Error querying database: {data}")
                
            all_results.extend(data.get("results", []))
            has_more = data.get("has_more", False)
            next_cursor = data.get("next_cursor")
            
        return all_results
    
    def get_database_metadata(self, database_id):
        """Get database metadata including property schemas"""
        url = f"https://api.notion.com/v1/databases/{database_id}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            raise Exception(f"Error getting database metadata: {response.json()}")
            
        return response.json()

class PandasConverter:
    """Convert Notion data to pandas-friendly format"""
    
    @staticmethod
    def extract_property_value(prop_value, prop_type):
        """Extract the actual value from a Notion property based on its type"""
        if prop_value is None:
            return None
            
        if prop_type == "title":
            if len(prop_value["title"]) > 0:
                return prop_value["title"][0]["plain_text"]
            return ""
            
        elif prop_type == "rich_text":
            if len(prop_value["rich_text"]) > 0:
                return prop_value["rich_text"][0]["plain_text"]
            return ""
            
        elif prop_type == "number":
            return prop_value["number"]
            
        elif prop_type == "select":
            if prop_value["select"]:
                return prop_value["select"]["name"]
            return None
            
        elif prop_type == "multi_select":
            if prop_value["multi_select"]:
                return [item["name"] for item in prop_value["multi_select"]]
            return []
            
        elif prop_type == "date":
            if prop_value["date"]:
                return prop_value["date"]["start"]
            return None
            
        elif prop_type == "checkbox":
            return prop_value["checkbox"]
            
        elif prop_type == "url":
            return prop_value["url"]
            
        elif prop_type == "email":
            return prop_value["email"]
            
        elif prop_type == "phone_number":
            return prop_value["phone_number"]
            
        elif prop_type == "created_time":
            return prop_value["created_time"]
            
        elif prop_type == "created_by":
            return prop_value["created_by"]["name"]
            
        elif prop_type == "last_edited_time":
            return prop_value["last_edited_time"]
            
        elif prop_type == "last_edited_by":
            return prop_value["last_edited_by"]["name"]
            
        elif prop_type == "formula":
            formula_type = prop_value["formula"]["type"]
            return prop_value["formula"][formula_type]
            
        elif prop_type == "relation":
            return [item["id"] for item in prop_value["relation"]]
            
        elif prop_type == "people":
            return [person["name"] for person in prop_value["people"]]
            
        else:
            # Return a default for any other type
            return str(prop_value)

class ExcelFormatter:
    """Format and style Excel files"""
    
    @staticmethod
    def format_excel(df, excel_path, sheet_name="Notion Data"):
        """Format the Excel file with styling"""
        # Write basic DataFrame to Excel
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # Access the workbook and sheet
            workbook = writer.book
            worksheet = writer.sheets[sheet_name]
            
            # Define styles
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="2F75B5", end_color="2F75B5", fill_type="solid")
            border = Border(
                left=Side(style="thin"), 
                right=Side(style="thin"), 
                top=Side(style="thin"), 
                bottom=Side(style="thin")
            )
            
            # Format headers
            for col in range(1, len(df.columns) + 1):
                cell = worksheet.cell(row=1, column=col)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = border
                
                # Adjust column width
                worksheet.column_dimensions[openpyxl.utils.get_column_letter(col)].width = max(
                    15, min(30, len(str(df.columns[col-1])) + 4)
                )
            
            # Format data cells
            for row in range(2, len(df) + 2):
                for col in range(1, len(df.columns) + 1):
                    cell = worksheet.cell(row=row, column=col)
                    cell.border = border
                    
                    # Alternate row coloring
                    if row % 2 == 0:
                        cell.fill = PatternFill(start_color="EBF1F8", end_color="EBF1F8", fill_type="solid")
            
            # Freeze top row
            worksheet.freeze_panes = "A2"
        
        return excel_path

class NotionToExcel:
    """Main class to handle Notion to Excel conversion"""
    
    def __init__(self, notion_token):
        self.notion_client = NotionClient(notion_token)
        self.pandas_converter = PandasConverter()
        self.excel_formatter = ExcelFormatter()
    
    def convert_to_dataframe(self, database_id):
        """Convert Notion database to pandas DataFrame"""
        # Get database data and schema
        pages = self.notion_client.query_database(database_id)
        db_metadata = self.notion_client.get_database_metadata(database_id)
        properties_schema = db_metadata["properties"]
        
        # Extract property types
        property_types = {
            prop_name: prop_schema["type"] 
            for prop_name, prop_schema in properties_schema.items()
        }
        
        # Build records for DataFrame
        records = []
        for page in pages:
            record = {}
            for prop_name, prop_schema in properties_schema.items():
                prop_type = property_types[prop_name]
                if prop_name in page["properties"]:
                    value = self.pandas_converter.extract_property_value(
                        page["properties"][prop_name], prop_type
                    )
                    record[prop_name] = value
                else:
                    record[prop_name] = None
            records.append(record)
        
        # Create DataFrame
        df = pd.DataFrame(records)
        return df
    
    def export_to_excel(self, database_id, file_path=None):
        """Export Notion database to formatted Excel file"""
        df = self.convert_to_dataframe(database_id)
        
        # Generate file path if not provided
        if file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"notion_export_{timestamp}.xlsx"
        
        # Format and save Excel file
        self.excel_formatter.format_excel(df, file_path)
        return file_path

# Flask webhook endpoint
@app.route('/export-notion-to-excel', methods=['POST'])
def export_notion_to_excel():
    try:
        data = request.json
        database_id = data.get('database_id')
        
        if not database_id:
            return jsonify({"error": "Database ID is required"}), 400
        
        # Create temp file
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        temp_file_path = temp_file.name
        temp_file.close()
        
        # Export to Excel
        exporter = NotionToExcel(NOTION_TOKEN)
        excel_file = exporter.export_to_excel(database_id, temp_file_path)
        
        # You could implement different return methods here:
        # 1. Return file for download
        # 2. Save to cloud storage and return link
        # 3. Email the file as attachment
        
        # For now, we'll just return the file directly
        return send_file(
            excel_file,
            as_attachment=True,
            download_name=f"notion_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)