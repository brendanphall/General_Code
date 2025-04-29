import requests
import time
import json
import os
from datetime import datetime

# Configuration
LOCATIONS = [
    "AXI", "CAM", "CON", "CRO", "DAR", "DER", "EST-L", "EST-S", "FUL", "GRA",
    "HER", "IRO", "JAC", "LAT", "MLT", "MOB", "THM", "URB", "WDC"
]
URL = "https://maps.canfor.com/arcgis/rest/services/CSPWoodpro/WoodPro_NSApps_DB_Views/MapServer/3/query"
FIELDS = "report_location,report_tract_no,Tract_Name,tract_status_desc,Forester,tract_type_family,SaleType,latitude_dd,longitude_dd,Wthr_grd,PurchDate,harvest_status"

# Performance tuning parameters
THRESHOLD = 300  # Split queries for locations with more than this many records
TIMEOUT = 60  # Timeout in seconds
OUTPUT_DIR = "woodpro_data"


def get_count(location):
    """Get the count of records for a location"""
    count_params = {
        "where": f"report_location='{location}'",
        "returnCountOnly": "true",
        "f": "json"
    }

    try:
        response = requests.get(URL, params=count_params, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json().get("count", 0)
    except Exception as e:
        print(f"Error getting count for {location}: {e}")
        return 0


def get_tract_ranges(location):
    """Get min and max tract numbers for range-based filtering"""
    # First try to get just a single record to see the field values
    params = {
        "where": f"report_location='{location}'",
        "outFields": "report_tract_no",
        "returnDistinctValues": "true",
        "orderByFields": "report_tract_no",
        "resultRecordCount": 1,
        "f": "json"
    }

    min_tract = None
    max_tract = None

    try:
        # Try to get minimal record
        response = requests.get(URL, params=params, timeout=TIMEOUT)
        data = response.json()

        if "features" in data and len(data["features"]) > 0:
            min_tract = data["features"][0]["attributes"].get("report_tract_no")

        # Now try to get max tract number
        params["orderByFields"] = "report_tract_no DESC"
        response = requests.get(URL, params=params, timeout=TIMEOUT)
        data = response.json()

        if "features" in data and len(data["features"]) > 0:
            max_tract = data["features"][0]["attributes"].get("report_tract_no")

        if min_tract is not None and max_tract is not None:
            return min_tract, max_tract
        else:
            print(f"Could not determine tract number range for {location}")
            return None, None

    except Exception as e:
        print(f"Error determining tract ranges for {location}: {e}")
        return None, None


def split_into_ranges(min_val, max_val, num_splits):
    """Split a range into approximately equal chunks"""
    if min_val is None or max_val is None:
        return []

    range_size = (max_val - min_val) / num_splits
    ranges = []

    for i in range(num_splits):
        start = min_val + (i * range_size)
        end = min_val + ((i + 1) * range_size)

        # Ensure we use integers for the ranges
        start_val = int(start)
        end_val = int(end)

        # Make sure the last range includes the max value
        if i == num_splits - 1:
            end_val = max_val

        ranges.append((start_val, end_val))

    return ranges


def get_data_with_ranges(location, total_count):
    """Get data by splitting into multiple requests based on tract number ranges"""
    print(f"Using range-based approach for {location} ({total_count} records)...")

    # Determine the number of splits based on the record count
    num_splits = max(2, total_count // 100)

    # Get min and max tract numbers
    min_tract, max_tract = get_tract_ranges(location)

    if min_tract is None or max_tract is None:
        print(f"Cannot use range-based approach for {location}, falling back to direct query")
        return get_data_direct(location)

    print(f"Tract range for {location}: {min_tract} to {max_tract}")
    print(f"Splitting into {num_splits} ranges")

    # Split the range
    ranges = split_into_ranges(min_tract, max_tract, num_splits)

    all_features = []
    range_num = 0

    for start_val, end_val in ranges:
        range_num += 1
        print(f"Querying range {range_num}/{num_splits}: tract_no from {start_val} to {end_val}")

        # Create WHERE clause for this range
        where_clause = f"report_location='{location}' AND report_tract_no>={start_val} AND report_tract_no<={end_val}"

        params = {
            "where": where_clause,
            "outFields": FIELDS,
            "f": "json",
            "returnGeometry": "false"
        }

        try:
            response = requests.get(URL, params=params, timeout=TIMEOUT)
            data = response.json()

            if "error" in data:
                print(f"API Error in range {start_val}-{end_val}: {data['error'].get('message', 'Unknown error')}")
                continue

            features = data.get("features", [])

            if features:
                all_features.extend(features)
                print(f"Retrieved {len(features)} records from range {start_val}-{end_val}")
            else:
                print(f"No records found in range {start_val}-{end_val}")

        except Exception as e:
            print(f"Error querying range {start_val}-{end_val}: {e}")

    return all_features


def get_data_direct(location):
    """Get data with a single request for smaller datasets"""
    print(f"Using direct query for {location}...")
    params = {
        "where": f"report_location='{location}'",
        "outFields": FIELDS,
        "f": "json",
        "returnGeometry": "false"
    }

    try:
        response = requests.get(URL, params=params, timeout=TIMEOUT)
        response.raise_for_status()

        data = response.json()

        # Check for error in response
        if "error" in data:
            print(f"API Error for {location}: {data['error'].get('message', 'Unknown error')}")
            return []

        features = data.get("features", [])
        print(f"Retrieved {len(features)} records")
        return features
    except Exception as e:
        print(f"Error getting data for {location}: {e}")
        return []


def process_location(location):
    """Process a single location with appropriate strategy based on record count"""
    start_time = time.time()

    # Get the total count first
    total_count = get_count(location)

    if total_count == 0:
        elapsed = round((time.time() - start_time) * 1000)
        return {
            "report_location": location,
            "count": 0,
            "time": f"{elapsed:,} ms",
            "success": True,
            "message": "No records found"
        }

    # Choose strategy based on record count
    if total_count > THRESHOLD:
        features = get_data_with_ranges(location, total_count)
    else:
        features = get_data_direct(location)

    elapsed = round((time.time() - start_time) * 1000)

    result = {
        "report_location": location,
        "count": total_count,
        "retrieved": len(features),
        "time": f"{elapsed:,} ms",
        "success": len(features) > 0
    }

    # Save the features if any were retrieved
    if features and len(features) > 0:
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)

        with open(f"{OUTPUT_DIR}/data_{location}.json", "w") as f:
            json.dump(features, f, indent=2)
        print(f"Data saved to {OUTPUT_DIR}/data_{location}.json")

    return result


def main():
    results = []
    start_time = time.time()

    print(f"Starting queries for {len(LOCATIONS)} locations...")
    print(f"Using range-based approach for locations with more than {THRESHOLD} records")
    print(f"Output directory: {OUTPUT_DIR}")
    print()

    # Process locations one by one
    for location in LOCATIONS:
        print(f"\n--- Processing {location} ---")
        try:
            result = process_location(location)
            results.append(result)

            print(json.dumps(result, indent=2))
        except Exception as e:
            print(f"Fatal error processing {location}: {e}")
            results.append({
                "report_location": location,
                "error": str(e),
                "success": False
            })

    # Print summary
    print("\nSummary of all queries:")
    successful = 0
    total_records = 0
    total_retrieved = 0

    for result in results:
        status = "✅" if result.get("success", False) else "❌"
        retrieved = result.get("retrieved", 0)
        count = result.get("count", 0)
        time_str = result.get("time", "N/A")
        print(f"{status} {result['report_location']}: {retrieved}/{count} records in {time_str}")

        if result.get("success", False):
            successful += 1
            total_records += count
            total_retrieved += retrieved

    # Save summary
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    with open(f"{OUTPUT_DIR}/query_results.json", "w") as f:
        json.dump(results, f, indent=4)

    # Print overall stats
    total_time = round(time.time() - start_time)
    print(f"\nOverall Statistics:")
    print(f"Total time: {total_time} seconds")
    print(f"Successful locations: {successful}/{len(LOCATIONS)}")
    print(f"Total records: {total_retrieved}/{total_records}")
    print(f"\nResults saved to {OUTPUT_DIR}/query_results.json")


if __name__ == "__main__":
    main()