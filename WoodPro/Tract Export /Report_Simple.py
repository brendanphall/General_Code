"""
WoodPro Mill Activity Report Generator (Simple Version)
======================================================

A utility script for generating reports from WoodPro activity tables for each mill location.
Uses the same approach as the working analyzer script - no authentication required.

Usage:
------
1. Configure the mills list with target locations  
2. Set the activity field you want to report on
3. Run the script to get values for each mill

Requirements:
------------
- Python 3.6+
- requests library

Author: brendan.hall@sewall.com
"""

import requests
import time
import json
import csv
from datetime import datetime

def generate_mill_report(activity_field="harvest_status", output_format="console"):
    """
    Generate a report showing activity values for each mill location.
    
    Args:
        activity_field: The field from activity table to report on
        output_format: "console", "csv", or "json"
    """
    
    # Mill locations - same as working analyzer script
    mills = [
        "AXI", "CAM", "CON", "CRO", "DAR", "DER", "EST-L", "EST-S",
        "FUL", "GRA", "HER", "IRO", "JAC", "LAT", "MLT", "MOB",
        "THM", "URB", "WDC"
    ]
    
    # ArcGIS REST API endpoint - same as analyzer script
    url = "https://maps.canfor.com/arcgis/rest/services/CSPWoodpro/WoodPro_CSP_Data/MapServer/3/query"
    
    print(f"Generating mill report for field: {activity_field}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    results = []
    
    for mill in mills:
        try:
            # Query parameters - exactly like analyzer script
            params = {
                "where": f"report_location='{mill}'",
                "outFields": f"report_location,{activity_field}",
                "returnGeometry": "false",
                "f": "json"
            }
            
            # Make the request - exactly like analyzer script
            start_time = time.time()
            response = requests.get(url, params=params)
            response.raise_for_status()
            elapsed_ms = round((time.time() - start_time) * 1000)
            
            resp_data = response.json()
            
            # Check for API errors - same as analyzer script
            if "error" in resp_data:
                result = {
                    "mill": mill,
                    "status": "error",
                    "message": resp_data["error"]["message"],
                    "query_time_ms": elapsed_ms
                }
                results.append(result)
                print(f'{mill:10} | ERROR: {resp_data["error"]["message"]}')
                continue
            
            # Process features - same approach as analyzer script
            features = resp_data.get("features", [])
            
            if not features:
                result = {
                    "mill": mill,
                    "status": "no_data",
                    "count": 0,
                    "query_time_ms": elapsed_ms
                }
                results.append(result)
                print(f"{mill:10} | No data found")
                continue
            
            # Extract activity field values
            activity_values = []
            for feature in features:
                attrs = feature.get("attributes", {})
                value = attrs.get(activity_field)
                if value is not None:
                    activity_values.append(value)
            
            # Create summary
            unique_values = list(set(activity_values))
            value_counts = {val: activity_values.count(val) for val in unique_values}
            
            result = {
                "mill": mill,
                "status": "success",
                "total_records": len(features),
                "activity_values": value_counts,
                "unique_values": unique_values,
                "query_time_ms": elapsed_ms
            }
            
            results.append(result)
            
            # Console output
            if len(unique_values) == 1:
                print(f"{mill:10} | {unique_values[0]} ({len(activity_values)} records)")
            else:
                values_str = ", ".join([f"{v}({c})" for v, c in value_counts.items()])
                print(f"{mill:10} | {values_str}")
                
        except Exception as e:
            result = {
                "mill": mill,
                "status": "connection_error",
                "message": str(e),
                "query_time_ms": 0
            }
            results.append(result)
            print(f'{mill:10} | ERROR: {str(e)}')
    
    # Generate output based on format
    if output_format == "csv":
        save_to_csv(results, activity_field)
    elif output_format == "json":
        save_to_json(results, activity_field)
    
    # Print summary
    print("\n" + "-" * 60)
    successful = len([r for r in results if r["status"] == "success"])
    print(f"Summary: {successful}/{len(mills)} mills queried successfully")
    
    return results

def save_to_csv(results, activity_field):
    """Save results to CSV file"""
    filename = f"mill_report_{activity_field}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Mill', 'Status', 'Total_Records', 'Activity_Values', 'Query_Time_MS'])
        
        for result in results:
            if result['status'] == 'success':
                values_str = "; ".join([f"{k}:{v}" for k, v in result['activity_values'].items()])
                writer.writerow([
                    result['mill'],
                    result['status'], 
                    result['total_records'],
                    values_str,
                    result['query_time_ms']
                ])
            else:
                writer.writerow([
                    result['mill'],
                    result['status'],
                    0,
                    result.get('message', ''),
                    result['query_time_ms']
                ])
    
    print(f"Results saved to: {filename}")

def save_to_json(results, activity_field):
    """Save results to JSON file"""
    filename = f"mill_report_{activity_field}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    output = {
        "report_metadata": {
            "activity_field": activity_field,
            "generated_at": datetime.now().isoformat(),
            "total_mills": len(results)
        },
        "results": results
    }
    
    with open(filename, 'w') as jsonfile:
        json.dump(output, jsonfile, indent=2)
    
    print(f"Results saved to: {filename}")

if __name__ == "__main__":
    # Generate report for harvest_status field
    generate_mill_report(activity_field="harvest_status", output_format="console")
    
    # Uncomment to save to CSV or JSON
    # generate_mill_report(activity_field="harvest_status", output_format="csv")
    # generate_mill_report(activity_field="harvest_status", output_format="json")
    
    # Example for other activity fields
    # generate_mill_report(activity_field="tract_status_desc", output_format="console")
    # generate_mill_report(activity_field="SaleType", output_format="console")