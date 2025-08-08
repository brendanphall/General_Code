"""
WoodPro Mill Activity Report Generator with Authentication
=========================================================

A utility script for generating reports from WoodPro activity tables for each mill location.
Queries the Canfor WoodPro ArcGIS REST API with authentication and extracts specific activity data values.

Usage:
------
1. Set your username and password in the script or use environment variables
2. Configure the mills list with target locations
3. Set the activity field you want to report on
4. Run the script to get values for each mill

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
import os
from datetime import datetime, date
import calendar


def get_arcgis_token(username, password, service_url):
    """
    Get a token that works for the specific ArcGIS service.
    This tries multiple approaches including session-based authentication.
    """
    session = requests.Session()

    # Extract the base server URL for token generation
    if '/rest/services/' in service_url:
        base_url = service_url.split('/rest/services/')[0]
    else:
        base_url = 'https://maps.canfor.com'

    # Method 1: Try direct session authentication (like a web browser)
    print("Method 1: Trying session-based authentication...")
    try:
        # First, get the login page to establish session
        login_url = "https://maps.canfor.com/portal/home/signin.html"
        session.get(login_url, timeout=30)

        # Try to authenticate using the web form approach
        auth_url = "https://maps.canfor.com/portal/sharing/rest/generateToken"
        auth_data = {
            'username': username,
            'password': password,
            'f': 'json',
            'referer': 'https://maps.canfor.com',
            'client': 'referer'
        }

        response = session.post(auth_url, data=auth_data, timeout=30)
        token_data = response.json()

        if 'token' in token_data:
            token = token_data['token']
            print(f"  Got session token, testing with service...")

            # Test with the service using session cookies AND token
            test_params = {
                'f': 'json',
                'token': token,
                'where': '1=1',
                'returnCountOnly': 'true'
            }

            test_response = session.get(service_url, params=test_params, timeout=30)
            test_data = test_response.json()

            if 'error' not in test_data or test_data.get('count') is not None:
                print(f"  Session authentication successful!")
                return token, token_data.get('expires', 0), session
            else:
                print(f"  Session token failed: {test_data.get('error', {}).get('message', 'Unknown error')}")

    except Exception as e:
        print(f"  Session auth failed: {str(e)}")

    # Method 2: Try getting token with different client types and parameters
    print("Method 2: Trying various token configurations...")

    token_configs = [
        {
            'endpoint': f"{base_url}/tokens/generateToken",
            'params': {
                'username': username,
                'password': password,
                'f': 'json',
                'client': 'referer',
                'referer': service_url,
                'expiration': '60'  # 60 minutes
            }
        },
        {
            'endpoint': "https://maps.canfor.com/portal/sharing/rest/generateToken",
            'params': {
                'username': username,
                'password': password,
                'f': 'json',
                'client': 'referer',
                'referer': base_url,
                'serverURL': base_url
            }
        },
        {
            'endpoint': "https://maps.canfor.com/portal/sharing/rest/generateToken",
            'params': {
                'username': username,
                'password': password,
                'f': 'json',
                'client': 'referer',
                'referer': service_url,
                'serverURL': service_url.split('/rest/services/')[0] if '/rest/services/' in service_url else base_url
            }
        }
    ]

    for config in token_configs:
        try:
            endpoint = config['endpoint']
            params = config['params']

            print(f"  Trying {endpoint} with serverURL: {params.get('serverURL', 'none')}")

            response = session.post(endpoint, data=params, timeout=30)
            response.raise_for_status()

            token_data = response.json()

            if 'error' in token_data:
                print(f"    Failed: {token_data['error']['message']}")
                continue

            token = token_data.get('token')
            if not token:
                print(f"    No token in response")
                continue

            # Test the token with different approaches
            test_approaches = [
                # Approach 1: Token in URL params
                {
                    'params': {'f': 'json', 'token': token, 'where': '1=1', 'returnCountOnly': 'true'},
                    'headers': {}
                },
                # Approach 2: Token in Authorization header
                {
                    'params': {'f': 'json', 'where': '1=1', 'returnCountOnly': 'true'},
                    'headers': {'Authorization': f'Bearer {token}'}
                },
                # Approach 3: Token in X-Esri-Authorization header
                {
                    'params': {'f': 'json', 'where': '1=1', 'returnCountOnly': 'true'},
                    'headers': {'X-Esri-Authorization': f'Bearer {token}'}
                }
            ]

            for i, approach in enumerate(test_approaches, 1):
                try:
                    test_response = session.get(service_url, params=approach['params'],
                                                headers=approach['headers'], timeout=30)
                    test_data = test_response.json()

                    if 'error' not in test_data or test_data.get('count') is not None:
                        print(f"    Token test successful with approach {i}!")
                        return token, token_data.get('expires', 0), session
                    elif i == 1:  # Only print error details for first approach
                        error = test_data.get('error', {})
                        print(f"    Token test failed: {error.get('message', 'Unknown error')}")

                except Exception as test_error:
                    if i == 1:  # Only print error for first approach
                        print(f"    Token test error: {str(test_error)}")

        except Exception as e:
            print(f"    Connection failed: {str(e)}")
            continue

    # Method 3: Try without authentication (in case service is actually public)
    print("Method 3: Testing if service is publicly accessible...")
    try:
        test_params = {
            'f': 'json',
            'where': '1=1',
            'returnCountOnly': 'true'
        }

        test_response = session.get(service_url, params=test_params, timeout=30)
        test_data = test_response.json()

        if 'error' not in test_data and test_data.get('count') is not None:
            print("  Service is publicly accessible!")
            return None, 0, session  # No token needed
        else:
            print(f"  Service requires authentication: {test_data.get('error', {}).get('message', 'Unknown error')}")

    except Exception as e:
        print(f"  Public access test failed: {str(e)}")

    raise Exception("All authentication methods failed to provide access to the service")


def get_month_input():
    """
    Interactive function to get month and year from user input.
    Returns a tuple of (year, month, start_date_str, end_date_str) for query filtering.
    """
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    print("\nHarvest Report Month Selection")
    print("=" * 40)
    
    # Get year
    while True:
        year_input = input(f"Enter year (default: {current_year}): ").strip()
        if not year_input:
            year = current_year
            break
        try:
            year = int(year_input)
            if year < 2000 or year > 2050:
                print("Please enter a reasonable year between 2000 and 2050")
                continue
            break
        except ValueError:
            print("Please enter a valid year (e.g., 2024)")
    
    # Get month
    while True:
        month_input = input(f"Enter month (1-12, default: {current_month}): ").strip()
        if not month_input:
            month = current_month
            break
        try:
            month = int(month_input)
            if month < 1 or month > 12:
                print("Please enter a month between 1 and 12")
                continue
            break
        except ValueError:
            print("Please enter a valid month number (1-12)")
    
    # Calculate date range for the month
    first_day = date(year, month, 1)
    last_day = date(year, month, calendar.monthrange(year, month)[1])
    
    # Format as strings for SQL query (assuming date format used in WoodPro)
    start_date_str = first_day.strftime('%Y-%m-%d')
    end_date_str = last_day.strftime('%Y-%m-%d')
    
    month_name = calendar.month_name[month]
    print(f"Selected: {month_name} {year} ({start_date_str} to {end_date_str})")
    
    return year, month, start_date_str, end_date_str


def generate_harvest_report(username=None, password=None, query_month=True, output_format="console"):
    """
    Generate a comprehensive harvest report for all mills with optional month filtering.
    
    Args:
        username: Canfor username (or set CANFOR_USERNAME env var)
        password: Canfor password (or set CANFOR_PASSWORD env var) 
        query_month: If True, prompts user for month to filter by
        output_format: "console", "csv", or "json"
    """
    
    # Get month filter if requested - temporarily disabled until we know what date fields exist
    date_filter = ""
    month_info = ""
    if query_month:
        year, month, start_date, end_date = get_month_input()
        month_name = calendar.month_name[month]
        month_info = f" - {month_name} {year} (Note: Date filtering disabled - showing all data)"
        # Temporarily disable date filtering since we don't know the field names yet
        # date_filter = f" AND (harvest_date >= date '{start_date}' AND harvest_date <= date '{end_date}')"
        print("Note: Month filtering temporarily disabled until we identify available date fields.")
    
    # Get credentials
    username = username or os.getenv('CANFOR_USERNAME')
    password = password or os.getenv('CANFOR_PASSWORD')

    if not username or not password:
        raise ValueError(
            "Username and password required. Set CANFOR_USERNAME and CANFOR_PASSWORD environment variables or pass them directly.")

    # ArcGIS REST API endpoint
    url = "https://maps.canfor.com/arcgis/rest/services/CSPWoodpro/WoodPro_CSP_Data/MapServer/3/query"

    # Get authentication token
    try:
        print("Authenticating with Canfor ArcGIS services...")
        token, token_expires, session = get_arcgis_token(username, password, url)
    except Exception as e:
        print(f"Authentication failed: {e}")
        return None

    # Mill locations
    mills = [
        "AXI", "CAM", "CON", "CRO", "DAR", "DER", "EST-L", "EST-S",
        "FUL", "GRA", "HER", "IRO", "JAC", "LAT", "MLT", "MOB",
        "THM", "URB", "WDC"
    ]
    
    # First, let's try with basic fields that we know work from the original script
    # We'll query all fields first to see what's available
    basic_fields = ["report_location", "harvest_status", "tract_status_desc", "SaleType"]
    
    # Test one mill to see what fields are available
    print("Testing available fields...")
    test_params = {
        "where": f"report_location='{mills[0]}'",
        "outFields": "*",  # Get all fields
        "returnGeometry": "false",
        "f": "json",
        "token": token,
        "resultRecordCount": 1  # Just get one record to test
    }
    
    try:
        test_response = session.get(url, params=test_params, timeout=30)
        test_data = test_response.json()
        
        if "features" in test_data and test_data["features"]:
            available_fields = list(test_data["features"][0].get("attributes", {}).keys())
            print(f"Available fields: {', '.join(sorted(available_fields))}")
            
            # Use fields that exist - focus on available harvest-related fields
            harvest_fields = ["report_location"]
            potential_fields = ["harvest_status", "tract_status_desc", "SaleType", 
                              "complete_status", "supplier", "procure_mgr", "Forester",
                              "begin_month", "begin_year", "end_month", "end_year", 
                              "days_since_last_load", "PurchDate", "expiredate"]
            
            for field in potential_fields:
                if field in available_fields:
                    harvest_fields.append(field)
                    
            print(f"Using fields: {', '.join(harvest_fields)}")
        else:
            print("No test data found, using basic fields")
            harvest_fields = basic_fields
            
    except Exception as e:
        print(f"Field test failed: {e}, using basic fields")
        harvest_fields = basic_fields
    
    outfields_str = ",".join(harvest_fields)

    print(f"\nGenerating Harvest Report{month_info}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Fields: {', '.join(harvest_fields[1:])}")  # Skip report_location in display
    print("-" * 80)

    results = []
    total_suppliers = set()
    total_harvest_statuses = set()
    total_records = 0

    for mill in mills:
        try:
            # Build where clause with mill filter and optional date filter
            where_clause = f"report_location='{mill}'{date_filter}"
            
            # Query parameters
            params = {
                "where": where_clause,
                "outFields": outfields_str,
                "returnGeometry": "false",
                "f": "json",
                "token": token
            }

            # Make the request
            start_time = time.time()
            response = session.get(url, params=params, timeout=30)
            response.raise_for_status()
            elapsed_ms = round((time.time() - start_time) * 1000)

            resp_data = response.json()

            # Check for API errors
            if "error" in resp_data:
                error_code = resp_data["error"].get("code", "unknown")
                error_message = resp_data["error"]["message"]

                # Handle token expiration
                if error_code == 498 or "token" in error_message.lower():
                    print(f"{mill:10} | Token expired, getting new token...")
                    try:
                        token, token_expires, session = get_arcgis_token(username, password, url)
                        params["token"] = token

                        # Retry the request
                        response = session.get(url, params=params, timeout=30)
                        resp_data = response.json()

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
                    except Exception as auth_error:
                        result = {
                            "mill": mill,
                            "status": "auth_error",
                            "message": str(auth_error),
                            "query_time_ms": elapsed_ms
                        }
                        results.append(result)
                        print(f'{mill:10} | AUTH ERROR: {str(auth_error)}')
                        continue
                else:
                    result = {
                        "mill": mill,
                        "status": "error",
                        "message": error_message,
                        "query_time_ms": elapsed_ms
                    }
                    results.append(result)
                    print(f'{mill:10} | ERROR: {error_message}')
                    continue

            # Process features
            features = resp_data.get("features", [])

            if not features:
                result = {
                    "mill": mill,
                    "status": "no_data",
                    "count": 0,
                    "query_time_ms": elapsed_ms
                }
                results.append(result)
                print(f"{mill:10} | No harvest data found")
                continue

            # Process harvest data using available fields
            harvest_statuses = []
            complete_statuses = []
            suppliers = set()
            sale_types = []
            
            for feature in features:
                attrs = feature.get("attributes", {})
                
                # Collect available harvest information
                if attrs.get("harvest_status"):
                    harvest_statuses.append(attrs["harvest_status"])
                if attrs.get("complete_status"):
                    complete_statuses.append(attrs["complete_status"])
                if attrs.get("supplier"):
                    suppliers.add(attrs["supplier"])
                if attrs.get("SaleType"):
                    sale_types.append(attrs["SaleType"])

            # Calculate summary statistics
            harvest_status_counts = {}
            for status in harvest_statuses:
                harvest_status_counts[status] = harvest_status_counts.get(status, 0) + 1
                
            complete_status_counts = {}
            for status in complete_statuses:
                complete_status_counts[status] = complete_status_counts.get(status, 0) + 1
            
            sale_type_counts = {}
            for sale_type in sale_types:
                sale_type_counts[sale_type] = sale_type_counts.get(sale_type, 0) + 1

            result = {
                "mill": mill,
                "status": "success",
                "total_records": len(features),
                "harvest_statuses": harvest_status_counts,
                "complete_statuses": complete_status_counts,
                "sale_types": sale_type_counts,
                "suppliers": list(suppliers),
                "supplier_count": len(suppliers),
                "query_time_ms": elapsed_ms
            }

            results.append(result)

            # Console output - show meaningful harvest info
            status_summary = f"H:{len(harvest_status_counts)} C:{len(complete_status_counts)} S:{len(sale_type_counts)}" if harvest_status_counts or complete_status_counts or sale_type_counts else "No status data"
            supplier_info = f"{len(suppliers)} suppliers" if suppliers else "No suppliers"
            print(f"{mill:10} | {len(features):3d} records | {status_summary} | {supplier_info}")

        except Exception as e:
            result = {
                "mill": mill,
                "status": "connection_error",
                "message": str(e),
                "query_time_ms": 0
            }
            results.append(result)
            print(f'{mill:10} | ERROR: {str(e)}')

    # Print summary statistics
    print("\n" + "=" * 80)
    successful = len([r for r in results if r["status"] == "success"])
    total_suppliers = len(set().union(*[r.get("suppliers", []) for r in results if r["status"] == "success"]))
    total_harvest_statuses = len(set().union(*[r.get("harvest_statuses", {}).keys() for r in results if r["status"] == "success"]))
    total_records = sum(r.get("total_records", 0) for r in results if r["status"] == "success")
    print(f"HARVEST SUMMARY{month_info}")
    print(f"Mills processed: {successful}/{len(mills)}")
    print(f"Total records: {total_records:,}")
    print(f"Total suppliers: {total_suppliers}")
    print(f"Unique harvest statuses: {total_harvest_statuses}")
    
    # Generate output based on format
    if output_format == "csv":
        save_harvest_to_csv(results, month_info)
    elif output_format == "json":
        save_harvest_to_json(results, month_info)

    return results


def generate_mill_report(username=None, password=None, activity_field="harvest_status", output_format="console"):
    """
    Generate a report showing activity values for each mill location.

    Args:
        username: Canfor username (or set CANFOR_USERNAME env var)
        password: Canfor password (or set CANFOR_PASSWORD env var)
        activity_field: The field from activity table to report on
        output_format: "console", "csv", or "json"
    """

    # Get credentials
    username = username or os.getenv('CANFOR_USERNAME')
    password = password or os.getenv('CANFOR_PASSWORD')

    if not username or not password:
        raise ValueError(
            "Username and password required. Set CANFOR_USERNAME and CANFOR_PASSWORD environment variables or pass them directly.")

    # ArcGIS REST API endpoint
    url = "https://maps.canfor.com/arcgis/rest/services/CSPWoodpro/WoodPro_CSP_Data/MapServer/3/query"

    # Get authentication token
    try:
        print("Authenticating with Canfor ArcGIS services...")
        token, token_expires, session = get_arcgis_token(username, password, url)
    except Exception as e:
        print(f"Authentication failed: {e}")
        return None

    # Mill locations - using the same subset as the working analyzer script
    mills = [
        "AXI", "CAM", "CON", "CRO", "DAR", "DER", "EST-L", "EST-S",
        "FUL", "GRA", "HER", "IRO", "JAC", "LAT", "MLT", "MOB",
        "THM", "URB", "WDC"
    ]

    print(f"\nGenerating mill report for field: {activity_field}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)

    results = []

    for mill in mills:
        try:
            # Query parameters
            params = {
                "where": f"report_location='{mill}'",
                "outFields": f"report_location,{activity_field}",
                "returnGeometry": "false",
                "f": "json",
                "token": token
            }

            # Make the request
            start_time = time.time()
            response = session.get(url, params=params, timeout=30)
            response.raise_for_status()
            elapsed_ms = round((time.time() - start_time) * 1000)

            resp_data = response.json()

            # Check for API errors
            if "error" in resp_data:
                error_code = resp_data["error"].get("code", "unknown")
                error_message = resp_data["error"]["message"]

                # Handle token expiration
                if error_code == 498 or "token" in error_message.lower():
                    print(f"{mill:10} | Token expired, getting new token...")
                    try:
                        token, token_expires, session = get_arcgis_token(username, password, url)
                        params["token"] = token

                        # Retry the request
                        response = session.get(url, params=params, timeout=30)
                        resp_data = response.json()

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
                    except Exception as auth_error:
                        result = {
                            "mill": mill,
                            "status": "auth_error",
                            "message": str(auth_error),
                            "query_time_ms": elapsed_ms
                        }
                        results.append(result)
                        print(f'{mill:10} | AUTH ERROR: {str(auth_error)}')
                        continue
                else:
                    result = {
                        "mill": mill,
                        "status": "error",
                        "message": error_message,
                        "query_time_ms": elapsed_ms
                    }
                    results.append(result)
                    print(f'{mill:10} | ERROR: {error_message}')
                    continue

            # Process features
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


def save_harvest_to_csv(results, month_info):
    """Save harvest results to CSV file"""
    safe_month = month_info.replace(' ', '_').replace('-', '').strip('_') if month_info else "all_months"
    filename = f"harvest_report{safe_month}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            'Mill', 'Status', 'Total_Records', 'Volume_m3', 'Area_ha', 
            'Contractors', 'Harvest_Statuses', 'Activity_Types', 'Query_Time_MS'
        ])

        for result in results:
            if result['status'] == 'success':
                statuses_str = "; ".join([f"{k}:{v}" for k, v in result.get('harvest_statuses', {}).items()])
                activities_str = "; ".join([f"{k}:{v}" for k, v in result.get('activity_types', {}).items()])
                contractors_str = "; ".join(result.get('contractors', []))
                
                writer.writerow([
                    result['mill'],
                    result['status'],
                    result['total_records'],
                    result.get('volume_m3', 0),
                    result.get('area_ha', 0),
                    contractors_str,
                    statuses_str,
                    activities_str,
                    result['query_time_ms']
                ])
            else:
                writer.writerow([
                    result['mill'],
                    result['status'],
                    0, 0, 0, '',
                    result.get('message', ''),
                    '',
                    result['query_time_ms']
                ])

    print(f"Harvest results saved to: {filename}")


def save_harvest_to_json(results, month_info):
    """Save harvest results to JSON file"""
    safe_month = month_info.replace(' ', '_').replace('-', '').strip('_') if month_info else "all_months"
    filename = f"harvest_report{safe_month}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    # Calculate totals for metadata
    total_volume = sum(r.get('volume_m3', 0) for r in results if r['status'] == 'success')
    total_area = sum(r.get('area_ha', 0) for r in results if r['status'] == 'success')
    successful_mills = len([r for r in results if r['status'] == 'success'])

    output = {
        "report_metadata": {
            "report_type": "harvest_report",
            "month_filter": month_info.strip() if month_info else "all_months",
            "generated_at": datetime.now().isoformat(),
            "total_mills": len(results),
            "successful_mills": successful_mills,
            "total_volume_m3": total_volume,
            "total_area_ha": total_area
        },
        "results": results
    }

    with open(filename, 'w') as jsonfile:
        json.dump(output, jsonfile, indent=2)

    print(f"Harvest results saved to: {filename}")


if __name__ == "__main__":
    # WoodPro Harvest Report Generator
    # ================================
    # 
    # This script provides two main reporting functions:
    # 1. generate_harvest_report() - Comprehensive harvest reports with month filtering and volume/area metrics
    # 2. generate_mill_report() - Simple activity field reports for backward compatibility
    
    # Option 1: Set credentials as environment variables (recommended)
    # export CANFOR_USERNAME="your_username"
    # export CANFOR_PASSWORD="your_password"
    
    # Option 2: Pass credentials directly (less secure)
    username = "woodpro.access"
    password = "lobloLLy_PL1"

    print("WoodPro Harvest Report Generator")
    print("===============================")
    print("This script will generate a comprehensive harvest report for all mills.")
    print("You will be prompted to select a month and year to filter the data.")
    print()
    
    # Generate comprehensive harvest report with month selection
    generate_harvest_report(
        username=username,
        password=password,
        query_month=True,  # This will prompt user for month selection
        output_format="console"
    )
    
    # Uncomment to generate additional report formats
    # generate_harvest_report(username=username, password=password, query_month=True, output_format="csv")
    # generate_harvest_report(username=username, password=password, query_month=True, output_format="json")
    
    # Uncomment to generate report for all data (no month filter)
    # generate_harvest_report(username=username, password=password, query_month=False, output_format="console")
    
    # =====================================
    # Legacy simple reports (for reference)
    # =====================================
    
    # Uncomment to run legacy simple field reports
    # generate_mill_report(username=username, password=password, activity_field="harvest_status", output_format="console")
    # generate_mill_report(username=username, password=password, activity_field="tract_status_desc", output_format="console")
    # generate_mill_report(username=username, password=password, activity_field="SaleType", output_format="console")