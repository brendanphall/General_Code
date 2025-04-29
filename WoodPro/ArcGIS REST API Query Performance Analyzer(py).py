"""
ArcGIS REST API Query Performance Analyzer
=========================================

A utility script for testing and comparing performance of ArcGIS REST API queries
with different field selections.

This script tests response times when querying the Canfor Woodpro database,
comparing performance with and without the harvest_status field included.

Usage:
------
1. Run the script as-is to test all locations with both query scenarios
2. Modify the locations list to focus on specific regions
3. Update field lists if different fields need to be compared
4. Adjust the record limit threshold (currently 500) as needed

Requirements:
------------
- Python 3.6+
- requests library

Example Output:
--------------
--- Run with harvest_status: True ---
{ "report_location": "AXI", "total_count": 120, "returned_count": 120, "time": "1,905 ms" }
{ "report_location": "CRO", "total_count": 29, "returned_count": 29, "time": "1,325 ms" }

Summary for with harvest_status:
Total successful queries: 10
Average query time: 2,345.6 ms
Total time: 23,456.0 ms

Notes:
-----
- Large datasets (>500 records) are skipped to avoid timeouts
- "Unable to complete operation" errors usually indicate server resource limitations
- Consider implementing pagination for comprehensive analysis of large datasets

Author: brendan.hall@sewall.com
Date: 4_29_2025
Version: 1.0
"""

import requests
import time
import json

def run_query(include_harvest_status=True):
    # Use the locations that seemed to work
    locations = [
        "AXI", "CRO", "DER", "EST-S", "FUL", "GRA",
        "HER", "IRO", "JAC", "LAT", "MLT", "MOB", "THM", "URB", "WDC"
    ]

    url = "https://maps.canfor.com/arcgis/rest/services/CSPWoodpro/WoodPro_NSApps_DB_Views/MapServer/3/query"

    print(f"\n--- Run with harvest_status: {include_harvest_status} ---\n")

    results = []

    for loc in locations:
        # Determine fields to query
        if include_harvest_status:
            fields = "report_location,report_tract_no,Tract_Name,tract_status_desc,Forester,tract_type_family,SaleType,latitude_dd,longitude_dd,Wthr_grd,PurchDate,harvest_status"
        else:
            fields = "report_location,report_tract_no,Tract_Name,tract_status_desc,Forester,tract_type_family,SaleType,latitude_dd,longitude_dd,Wthr_grd,PurchDate"

        # Basic parameters
        params = {
            "where": f"report_location='{loc}'",
            "outFields": fields,
            "returnGeometry": "false",
            "f": "json"
        }

        # Count request
        count_params = {
            "where": f"report_location='{loc}'",
            "returnCountOnly": "true",
            "f": "json"
        }

        try:
            # Get count
            count_resp = requests.get(url, params=count_params)
            count_resp.raise_for_status()
            count = count_resp.json().get("count", 0)

            # Skip if more than 500 records to avoid timeouts
            if count > 500:
                print(f'{{ "report_location": "{loc}", "total_count": {count}, "status": "skipped - too many records", "time": "N/A" }}')
                continue

            # Actual query
            start = time.time()
            response = requests.get(url, params=params)
            response.raise_for_status()
            elapsed = round((time.time() - start) * 1000)

            resp_data = response.json()

            # Check for API error
            if "error" in resp_data:
                print(f'{{ "report_location": "{loc}", "error": "{resp_data["error"]["message"]}", "time": "{elapsed:,} ms" }}')
                continue

            # Get features count
            features_count = len(resp_data.get("features", []))

            # Print concise result
            result = {
                "report_location": loc,
                "total_count": count,
                "returned_count": features_count,
                "time": elapsed
            }

            results.append(result)
            print(f'{{ "report_location": "{loc}", "total_count": {count}, "returned_count": {features_count}, "time": "{elapsed:,} ms" }}')

        except Exception as e:
            print(f'{{ "report_location": "{loc}", "error": "{str(e)}", "time": "N/A" }}')

    # Print summary if we got results
    if results:
        total_time = sum(r["time"] for r in results)
        avg_time = total_time / len(results)
        print(f"\nSummary for {'with' if include_harvest_status else 'without'} harvest_status:")
        print(f"Total successful queries: {len(results)}")
        print(f"Average query time: {avg_time:,.1f} ms")
        print(f"Total time: {total_time:,.1f} ms")

# Run both scenarios
run_query(include_harvest_status=True)
run_query(include_harvest_status=False)