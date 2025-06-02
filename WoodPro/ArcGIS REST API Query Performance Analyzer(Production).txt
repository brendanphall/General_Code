"""
ArcGIS REST API Query Performance Analyzer
=========================================

A utility script for testing and comparing performance of ArcGIS REST API queries
with different field selections on the Canfor Woodpro CSP Data MapServer.

This script tests response times when querying Layer 3 (woodpro.csp_10_woodpro_tract_lookup_vw),
comparing performance with and without the harvest_status field included.

Target Layer: woodpro.csp_10_woodpro_tract_lookup_vw (ID: 3)
Max Records: 2000 per query
Endpoint: https://maps.canfor.com/arcgis/rest/services/CSPWoodpro/WoodPro_CSP_Data/MapServer/3

Usage:
------
1. Run the script as-is to test all locations with both query scenarios
2. Modify the locations list to focus on specific regions
3. Update field lists if different fields need to be compared
4. Adjust the record limit threshold (currently 1500) as needed

Requirements:
------------
- Python 3.6+
- requests library

Example Output:
--------------
--- Performance Test: WITH harvest_status field ---
{ "report_location": "AXI", "total_count": 120, "returned_count": 120, "time": "1,905 ms" }
{ "report_location": "CRO", "total_count": 29, "returned_count": 29, "time": "1,325 ms" }

Summary for WITH harvest_status:
Total successful queries: 10
Average query time: 2,345.6 ms
Total time: 23,456.0 ms

Notes:
-----
- Layer supports max 2000 records per query
- Large datasets (>1500 records) are skipped to avoid timeouts
- "Unable to complete operation" errors usually indicate server resource limitations
- Layer supports advanced queries, statistics, and pagination

Author: brendan.hall@sewall.com
Date: 5_21_2025
Version: 2.0 - Updated for Layer 3 (woodpro.csp_10_woodpro_tract_lookup_vw)
"""

import requests
import time
import json
from typing import List, Dict, Tuple, Optional

# Configuration Constants
BASE_URL = "https://maps.canfor.com/arcgis/rest/services/CSPWoodpro/WoodPro_CSP_Data/MapServer"
LAYER_ID = "3"  # woodpro.csp_10_woodpro_tract_lookup_vw
QUERY_URL = f"{BASE_URL}/{LAYER_ID}/query"
RECORD_LIMIT = 1500  # Conservative limit (MapServer max is 2000)
REQUEST_TIMEOUT = 90  # Seconds


def get_layer_info() -> None:
    """
    Fetch and display layer information from the MapServer
    """
    try:
        layer_url = f"{BASE_URL}/{LAYER_ID}?f=json"
        response = requests.get(layer_url, timeout=30)
        response.raise_for_status()
        data = response.json()

        print("Layer Information:")
        print("-" * 60)
        print(f"Name: {data.get('name', 'Unknown')}")
        print(f"Display Field: {data.get('displayField', 'Unknown')}")
        print(f"Type: {data.get('type', 'Unknown')}")
        print(f"Max Record Count: {data.get('maxRecordCount', 'Unknown')}")
        print(f"Supports Advanced Queries: {data.get('supportsAdvancedQueries', 'Unknown')}")
        print(f"Supports Statistics: {data.get('supportsStatistics', 'Unknown')}")
        print("-" * 60)

    except Exception as e:
        print(f"Error fetching layer info: {e}")


def run_performance_test(include_harvest_status: bool = True) -> List[Dict]:
    """
    Run performance test queries with or without harvest_status field

    Args:
        include_harvest_status (bool): Whether to include harvest_status in query

    Returns:
        List[Dict]: Results from successful queries
    """

    # Test locations based on the original script
    locations = [
        "AXI", "CAM", "CON", "CRO", "DAR", "DER", "EST-L", "EST-S",
        "FUL", "GRA", "HER", "IRO", "JAC", "LAT", "MLT", "MOB",
        "THM", "URB", "WDC"
    ]

    # Define field sets based on layer schema
    base_fields = [
        "Location", "report_location", "report_tract_no", "Tract_Name",
        "tract_status_desc", "Forester", "tract_type_family", "SaleType",
        "latitude_dd", "longitude_dd", "Wthr_grd", "PurchDate",
        "complete_status", "expire_status", "days_to_expire"
    ]

    # Add harvest_status if requested
    if include_harvest_status:
        query_fields = base_fields + ["harvest_status", "days_since_last_load"]
    else:
        query_fields = base_fields.copy()

    fields_string = ",".join(query_fields)

    print(f"\n--- Performance Test: {'WITH' if include_harvest_status else 'WITHOUT'} harvest_status field ---")
    print(f"Target Layer: {LAYER_ID} (woodpro.csp_10_woodpro_tract_lookup_vw)")
    print(f"Query URL: {QUERY_URL}")
    print(f"Fields Count: {len(query_fields)}")
    print(f"Record Limit: {RECORD_LIMIT}\n")

    results = []
    skipped_locations = []
    failed_locations = []

    for loc in locations:
        try:
            # First, get the count to check if we should proceed
            count_result = get_record_count(loc)
            if count_result is None:
                failed_locations.append((loc, "Count query failed"))
                continue

            total_count = count_result

            # Skip if too many records (to avoid timeouts)
            if total_count > RECORD_LIMIT:
                skipped_locations.append((loc, total_count))
                print(
                    f'{{ "report_location": "{loc}", "status": "skipped", "total_count": {total_count:,}, "reason": "exceeds limit of {RECORD_LIMIT:,}" }}')
                continue

            # Skip if no records
            if total_count == 0:
                print(f'{{ "report_location": "{loc}", "status": "no_data", "total_count": 0, "time": "N/A" }}')
                continue

            # Execute the performance query
            query_result = execute_query(loc, fields_string)
            if query_result is None:
                failed_locations.append((loc, "Query execution failed"))
                continue

            returned_count, elapsed_ms = query_result

            # Store successful result
            result = {
                "report_location": loc,
                "total_count": total_count,
                "returned_count": returned_count,
                "time": elapsed_ms,
                "fields_count": len(query_fields)
            }

            results.append(result)
            print(
                f'{{ "report_location": "{loc}", "total_count": {total_count:,}, "returned_count": {returned_count:,}, "time": "{elapsed_ms:,} ms" }}')

        except Exception as e:
            failed_locations.append((loc, f"Unexpected error: {str(e)}"))
            print(f'{{ "report_location": "{loc}", "error": "Unexpected error: {str(e)}", "time": "N/A" }}')

    # Print comprehensive summary
    print_detailed_summary(results, skipped_locations, failed_locations, include_harvest_status)
    return results


def get_record_count(location: str) -> Optional[int]:
    """Get record count for a specific location"""
    count_params = {
        "where": f"report_location='{location}'",
        "returnCountOnly": "true",
        "f": "json"
    }

    try:
        response = requests.get(QUERY_URL, params=count_params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            print(f'{{ "report_location": "{location}", "error": "Count failed: {data["error"]["message"]}" }}')
            return None

        return data.get("count", 0)

    except requests.exceptions.RequestException as e:
        print(f'{{ "report_location": "{location}", "error": "Count request failed: {str(e)}" }}')
        return None


def execute_query(location: str, fields: str) -> Optional[Tuple[int, int]]:
    """Execute the main query and return (returned_count, elapsed_ms)"""
    query_params = {
        "where": f"report_location='{location}'",
        "outFields": fields,
        "returnGeometry": "false",
        "f": "json"
    }

    try:
        start_time = time.time()
        response = requests.get(QUERY_URL, params=query_params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        elapsed_ms = round((time.time() - start_time) * 1000)

        data = response.json()

        if "error" in data:
            print(
                f'{{ "report_location": "{location}", "error": "{data["error"]["message"]}", "time": "{elapsed_ms:,} ms" }}')
            return None

        features = data.get("features", [])
        return len(features), elapsed_ms

    except requests.exceptions.RequestException as e:
        print(f'{{ "report_location": "{location}", "error": "Query request failed: {str(e)}" }}')
        return None


def print_detailed_summary(results: List[Dict], skipped: List[Tuple], failed: List[Tuple],
                           include_harvest_status: bool) -> None:
    """Print comprehensive summary statistics"""

    status_text = 'WITH' if include_harvest_status else 'WITHOUT'

    print(f"\n{'=' * 60}")
    print(f"SUMMARY FOR {status_text} harvest_status field")
    print(f"{'=' * 60}")

    if results:
        # Calculate statistics
        total_time = sum(r["time"] for r in results)
        avg_time = total_time / len(results)
        total_records = sum(r["returned_count"] for r in results)

        fastest = min(results, key=lambda x: x["time"])
        slowest = max(results, key=lambda x: x["time"])

        print(f"Successful queries: {len(results)}")
        print(f"Total records returned: {total_records:,}")
        print(f"Average query time: {avg_time:,.1f} ms")
        print(f"Total query time: {total_time:,.1f} ms")
        print(f"Fastest query: {fastest['report_location']} ({fastest['time']:,} ms)")
        print(f"Slowest query: {slowest['report_location']} ({slowest['time']:,} ms)")

        # Performance metrics
        avg_records_per_query = total_records / len(results) if results else 0
        avg_ms_per_record = avg_time / avg_records_per_query if avg_records_per_query > 0 else 0

        print(f"Average records per query: {avg_records_per_query:.1f}")
        print(f"Average ms per record: {avg_ms_per_record:.2f}")

    else:
        print("No successful queries completed")

    if skipped:
        print(f"\nSkipped locations (>{RECORD_LIMIT:,} records):")
        for loc, count in skipped:
            print(f"  {loc}: {count:,} records")

    if failed:
        print(f"\nFailed locations:")
        for loc, reason in failed:
            print(f"  {loc}: {reason}")


def compare_performance_results(with_harvest: List[Dict], without_harvest: List[Dict]) -> None:
    """Compare results between the two test scenarios"""

    print(f"\n{'=' * 60}")
    print("PERFORMANCE COMPARISON")
    print(f"{'=' * 60}")

    # Find common locations
    with_locations = {r["report_location"] for r in with_harvest}
    without_locations = {r["report_location"] for r in without_harvest}
    common_locations = with_locations.intersection(without_locations)

    if not common_locations:
        print("No common locations found for comparison")
        return

    print(f"Comparing {len(common_locations)} common locations:")

    # Create lookup dictionaries
    with_lookup = {r["report_location"]: r for r in with_harvest}
    without_lookup = {r["report_location"]: r for r in without_harvest}

    total_with_time = 0
    total_without_time = 0
    faster_with_harvest = 0
    faster_without_harvest = 0

    print(f"\n{'Location':<12} {'With (ms)':<10} {'Without (ms)':<12} {'Difference':<12} {'Faster'}")
    print("-" * 60)

    for loc in sorted(common_locations):
        with_time = with_lookup[loc]["time"]
        without_time = without_lookup[loc]["time"]

        total_with_time += with_time
        total_without_time += without_time

        difference = with_time - without_time
        faster = "WITH" if difference > 0 else "WITHOUT" if difference < 0 else "SAME"

        if difference > 0:
            faster_without_harvest += 1
        elif difference < 0:
            faster_with_harvest += 1

        print(f"{loc:<12} {with_time:<10,} {without_time:<12,} {difference:>+8,} ms   {faster}")

    # Summary
    avg_with = total_with_time / len(common_locations)
    avg_without = total_without_time / len(common_locations)
    avg_difference = avg_with - avg_without

    print("-" * 60)
    print(f"{'AVERAGE':<12} {avg_with:<10,.0f} {avg_without:<12,.0f} {avg_difference:>+8,.0f} ms")
    print(f"\nFaster WITH harvest_status: {faster_with_harvest} locations")
    print(f"Faster WITHOUT harvest_status: {faster_without_harvest} locations")

    improvement_pct = (abs(avg_difference) / max(avg_with, avg_without)) * 100
    faster_scenario = "WITHOUT" if avg_difference > 0 else "WITH"
    print(f"\nOverall: {faster_scenario} harvest_status is {improvement_pct:.1f}% faster on average")


def main():
    """Main execution function"""
    print("ArcGIS REST API Query Performance Analyzer")
    print("Canfor Woodpro CSP Data - Layer 3 Analysis")
    print("=" * 60)

    # Display layer information
    get_layer_info()

    # Run both test scenarios
    print("\nStarting performance analysis...")
    results_with_harvest = run_performance_test(include_harvest_status=True)
    results_without_harvest = run_performance_test(include_harvest_status=False)

    # Compare results
    if results_with_harvest and results_without_harvest:
        compare_performance_results(results_with_harvest, results_without_harvest)

    print(f"\nAnalysis complete!")
    print(f"Layer: {LAYER_ID} (woodpro.csp_10_woodpro_tract_lookup_vw)")
    print(f"Record limit: {RECORD_LIMIT:,}")
    print(f"Request timeout: {REQUEST_TIMEOUT}s")


if __name__ == "__main__":
    main()