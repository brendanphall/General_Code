import requests
import time
import json

# Configuration
LOCATIONS = [
    "AXI", "CAM", "CON", "CRO", "DAR", "DER", "EST-L", "EST-S", "FUL", "GRA",
    "HER", "IRO", "JAC", "LAT", "MLT", "MOB", "THM", "URB", "WDC"
]
URL = "https://maps.canfor.com/arcgis/rest/services/CSPWoodpro/WoodPro_NSApps_DB_Views/MapServer/3/query"
FIELDS = "report_location,report_tract_no,Tract_Name,tract_status_desc,Forester,tract_type_family,SaleType,latitude_dd,longitude_dd,Wthr_grd,PurchDate,harvest_status"
TIMEOUT = 60  # Seconds


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


def test_query_variants(location):
    """Try different query variants to find what works"""
    variants = [
        {
            "name": "Basic query with FIELDS",
            "params": {
                "where": f"report_location='{location}'",
                "outFields": FIELDS,
                "f": "json",
                "returnGeometry": "false"
            }
        },
        {
            "name": "Basic query with *",
            "params": {
                "where": f"report_location='{location}'",
                "outFields": "*",
                "f": "json",
                "returnGeometry": "false"
            }
        },
        {
            "name": "Query with objectIds",
            "params": {
                "objectIds": "1,2,3,4,5",
                "outFields": "*",
                "f": "json",
                "returnGeometry": "false"
            }
        },
        {
            "name": "Query with 1=1",
            "params": {
                "where": "1=1",
                "outFields": FIELDS,
                "f": "json",
                "returnGeometry": "false",
                "resultRecordCount": "5"
            }
        },
        {
            "name": "Query with single quotes escaped",
            "params": {
                "where": f"report_location=''{location}''",
                "outFields": FIELDS,
                "f": "json",
                "returnGeometry": "false"
            }
        },
        {
            "name": "Query without quotes",
            "params": {
                "where": f"report_location={location}",
                "outFields": FIELDS,
                "f": "json",
                "returnGeometry": "false"
            }
        },
        {
            "name": "Query with LIKE operator",
            "params": {
                "where": f"report_location LIKE '{location}%'",
                "outFields": FIELDS,
                "f": "json",
                "returnGeometry": "false"
            }
        }
    ]

    results = []

    for variant in variants:
        print(f"\nTesting variant: {variant['name']}")
        try:
            response = requests.get(URL, params=variant['params'], timeout=TIMEOUT)
            print(f"Status Code: {response.status_code}")

            try:
                data = response.json()

                if "error" in data:
                    print(f"API Error: {data['error'].get('message', 'Unknown error')}")
                    success = False
                    features_count = 0
                else:
                    features = data.get("features", [])
                    features_count = len(features)
                    success = features_count > 0
                    print(f"Features returned: {features_count}")

                    if success and features_count > 0:
                        print(f"First feature attributes: {json.dumps(features[0].get('attributes', {}), indent=2)}")

                results.append({
                    "variant": variant['name'],
                    "success": success,
                    "features_count": features_count,
                    "params": variant['params']
                })

            except ValueError as e:
                print(f"JSON parsing error: {e}")
                print(f"Response content: {response.text[:500]}...")
                results.append({
                    "variant": variant['name'],
                    "success": False,
                    "error": str(e),
                    "params": variant['params']
                })

        except Exception as e:
            print(f"Request error: {e}")
            results.append({
                "variant": variant['name'],
                "success": False,
                "error": str(e),
                "params": variant['params']
            })

    return results


def main():
    # Start with one location to test with
    test_location = "AXI"  # This is a smaller location

    print(f"Testing query variants for location: {test_location}")
    count = get_count(test_location)
    print(f"Record count for {test_location}: {count}")

    results = test_query_variants(test_location)

    # Find successful variants
    successful = [r for r in results if r.get("success", False)]

    print("\n=== RESULTS SUMMARY ===")
    if successful:
        print(f"Found {len(successful)} working query variants:")
        for s in successful:
            print(f"✅ {s['variant']}: {s['features_count']} features")

        # Use the first successful variant to query all locations
        best_variant = successful[0]
        print(f"\nUsing variant '{best_variant['variant']}' to query all locations")

        all_results = []
        for location in LOCATIONS:
            print(f"\nQuerying {location}...")
            start_time = time.time()

            # Adapt the successful params for this location
            params = best_variant['params'].copy()
            for key, value in params.items():
                if isinstance(value, str) and test_location in value:
                    params[key] = value.replace(test_location, location)

            try:
                response = requests.get(URL, params=params, timeout=TIMEOUT)
                data = response.json()

                if "error" in data:
                    print(f"API Error: {data['error'].get('message', 'Unknown error')}")
                    features_count = 0
                    success = False
                else:
                    features = data.get("features", [])
                    features_count = len(features)
                    success = features_count > 0

                elapsed = round((time.time() - start_time) * 1000)

                result = {
                    "report_location": location,
                    "count": get_count(location),
                    "retrieved": features_count,
                    "time": f"{elapsed:,} ms",
                    "success": success
                }

                print(json.dumps(result, indent=2))
                all_results.append(result)

                # Save the data if successful
                if success and features:
                    with open(f"data_{location}.json", "w") as f:
                        json.dump(features, f, indent=4)
                    print(f"Data saved to data_{location}.json")

            except Exception as e:
                print(f"Error: {e}")
                all_results.append({
                    "report_location": location,
                    "error": str(e),
                    "success": False
                })

        # Save summary results
        with open("query_results.json", "w") as f:
            json.dump(all_results, f, indent=4)
        print("\nAll results saved to query_results.json")

    else:
        print("❌ No successful query variants found. Try these troubleshooting steps:")
        print("1. Verify the API endpoint URL is correct")
        print("2. Check if authentication is required")
        print("3. Try accessing the service through a web browser")
        print("4. Check the field names in your query")
        print("5. Try with a simpler query structure")


if __name__ == "__main__":
    main()