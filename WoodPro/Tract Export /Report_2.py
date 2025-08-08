"""
WoodPro Harvest Report Generator - Condensed Core Version
========================================================

Streamlined utility for generating harvest reports from WoodPro activity tables.
Includes geometry export to shapefile format.
"""

import requests
import os
from datetime import datetime, date
import calendar
import json
import geopandas as gpd
from shapely.geometry import shape


def get_auth_token(username, password):
    """Get authentication token for WoodPro ArcGIS service."""
    session = requests.Session()
    
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
    
    if 'token' not in token_data:
        raise Exception(f"Authentication failed: {token_data.get('error', {}).get('message', 'Unknown error')}")
    
    return token_data['token'], session


def get_month_input():
    """Get month and year from user input."""
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    print("\nHarvest Report Month Selection")
    print("=" * 40)
    
    # Get year
    year_input = input(f"Enter year (default: {current_year}): ").strip()
    year = int(year_input) if year_input else current_year
    
    # Get month  
    month_input = input(f"Enter month (1-12, default: {current_month}): ").strip()
    month = int(month_input) if month_input else current_month
    
    month_name = calendar.month_name[month]
    print(f"Selected: {month_name} {year}")
    
    return year, month, month_name


def get_sewall_auth_token(username, password):
    """Get authentication token for Sewall's ArcGIS service."""
    session = requests.Session()
    
    # Try Sewall's portal first
    auth_url = "https://maps.sewall.com/portal2/sharing/rest/generateToken"
    auth_data = {
        'username': username,
        'password': password,
        'f': 'json',
        'referer': 'https://maps.sewall.com',
        'client': 'referer'
    }
    
    try:
        response = session.post(auth_url, data=auth_data, timeout=30)
        token_data = response.json()
        
        if 'token' in token_data:
            return token_data['token'], session
    except:
        pass
    
    # If that fails, we'll continue without Sewall access
    return None, session


def discover_spatial_services(canfor_token, canfor_session, sewall_token=None, sewall_session=None):
    """Discover available ArcGIS services that contain spatial tract data."""
    
    print("Discovering spatial services...")
    
    working_services = []
    
    # First try Sewall's service (most likely to have geometries based on the example)
    if sewall_token and sewall_session:
        print("Testing Sewall's spatial service...")
        sewall_service = "https://maps.sewall.com/server2/rest/services/canfor/SalesService/FeatureServer"
        
        try:
            # Get service info
            info_url = f"{sewall_service}?f=json"
            response = sewall_session.get(info_url, params={"token": sewall_token}, timeout=30)
            
            if response.status_code == 200:
                service_info = response.json()
                if "layers" in service_info:
                    print(f"  Found Sewall service with {len(service_info['layers'])} layers")
                    
                    # Look for "All Tracts" layer specifically
                    for layer in service_info['layers']:
                        layer_id = layer['id']
                        layer_name = layer.get('name', 'Unknown')
                        
                        if 'tracts' in layer_name.lower():
                            test_url = f"{sewall_service}/{layer_id}/query"
                            test_params = {
                                "where": "1=1",
                                "returnGeometry": "true",
                                "f": "json", 
                                "token": sewall_token,
                                "resultRecordCount": 1
                            }
                            
                            try:
                                test_response = sewall_session.get(test_url, params=test_params, timeout=15)
                                test_data = test_response.json()
                                
                                if ("features" in test_data and test_data["features"] and 
                                    test_data["features"][0].get("geometry")):
                                    print(f"    ✓ Found spatial layer: {layer_name} (Layer {layer_id})")
                                    working_services.append({
                                        "url": test_url,
                                        "service": sewall_service,
                                        "layer_id": layer_id,
                                        "layer_name": layer_name,
                                        "source": "sewall",
                                        "token": sewall_token,
                                        "session": sewall_session
                                    })
                            except Exception as e:
                                print(f"    Layer {layer_id} test failed: {str(e)}")
        except Exception as e:
            print(f"  Failed to access Sewall service: {str(e)}")
    else:
        print("No Sewall credentials available - skipping Sewall spatial service")
    
    # Also check Canfor services as backup
    canfor_services = [
        "https://maps.canfor.com/arcgis/rest/services/CSPWoodpro/WoodPro_CSP_Data/MapServer",
        "https://maps.canfor.com/arcgis/rest/services/CSPWoodpro/Tracts/MapServer", 
        "https://maps.canfor.com/arcgis/rest/services/CSPWoodpro/Spatial/MapServer"
    ]
    
    print("Testing Canfor services as backup...")
    for service_url in canfor_services:
        try:
            info_url = service_url.replace("/MapServer", "/MapServer?f=json")
            response = canfor_session.get(info_url, params={"token": canfor_token}, timeout=30)
            
            if response.status_code == 200:
                service_info = response.json()
                if "layers" in service_info:
                    for layer in service_info['layers']:
                        layer_id = layer['id']
                        layer_name = layer.get('name', 'Unknown')
                        
                        test_url = f"{service_url}/{layer_id}/query"
                        test_params = {
                            "where": "1=1",
                            "returnGeometry": "true",
                            "f": "json",
                            "token": canfor_token,
                            "resultRecordCount": 1
                        }
                        
                        try:
                            test_response = canfor_session.get(test_url, params=test_params, timeout=15)
                            test_data = test_response.json()
                            
                            if ("features" in test_data and test_data["features"] and 
                                test_data["features"][0].get("geometry")):
                                print(f"    ✓ Found Canfor spatial layer: {layer_name} (Layer {layer_id})")
                                working_services.append({
                                    "url": test_url,
                                    "service": service_url,
                                    "layer_id": layer_id,
                                    "layer_name": layer_name,
                                    "source": "canfor",
                                    "token": canfor_token,
                                    "session": canfor_session
                                })
                        except:
                            pass
        except:
            pass
    
    return working_services


def export_geometries_to_shapefile(canfor_username, canfor_password, canfor_token, canfor_session, month_info="", test_mills=None):
    """Export tract geometries to shapefile format for selected mills and month."""
    
    # Try to get Sewall credentials (from the example solution)
    sewall_username = "canfor_app" 
    sewall_password = "canfor$1234"
    
    print("Getting authentication tokens...")
    sewall_token, sewall_session = get_sewall_auth_token(sewall_username, sewall_password)
    
    # Discover spatial services from both sources
    spatial_services = discover_spatial_services(canfor_token, canfor_session, sewall_token, sewall_session)
    
    if spatial_services:
        print(f"\nFound {len(spatial_services)} spatial services!")
        selected_service = spatial_services[0]  # Use first working service
        print(f"Using: {selected_service['layer_name']} from {selected_service['source']}")
        
        # Extract service details
        geometry_url = selected_service["url"] 
        geometry_token = selected_service["token"]
        geometry_session = selected_service["session"]
    else:
        print("\nNo spatial services found. Unable to generate shapefiles without geometry data.")
        return None
    
    # Use test mills or default to first few mills for testing
    if test_mills is None:
        test_mills = ["AXI", "CAM", "CON"]  # Start with just 3 mills for testing
    
    print(f"\nExporting geometries for {len(test_mills)} mills{month_info}...")
    
    all_features = []
    
    for mill in test_mills:
        try:
            params = {
                "where": f"report_location='{mill}'",
                "outFields": "*",  # Get all fields for export
                "returnGeometry": "true",  # Important: include geometries
                "f": "json",
                "token": geometry_token,
                "resultRecordCount": 10  # Limit to 10 features per mill for testing
            }
            
            response = geometry_session.get(geometry_url, params=params, timeout=30)
            data = response.json()
            
            if "error" in data:
                print(f"  {mill}: ERROR - {data['error']['message']}")
                continue
                
            features = data.get("features", [])
            
            if not features:
                print(f"  {mill}: No features found")
                continue
                
            # Debug: Check what we're actually getting back
            if mill == "AXI":  # Only debug first mill to avoid spam
                sample_feature = features[0]
                print(f"  DEBUG - Sample feature keys: {list(sample_feature.keys())}")
                if 'geometry' in sample_feature:
                    print(f"  DEBUG - Geometry keys: {list(sample_feature['geometry'].keys()) if sample_feature['geometry'] else 'None'}")
                else:
                    print(f"  DEBUG - No 'geometry' key found")
                    
            # Add mill identifier to each feature
            for feature in features:
                feature["attributes"]["source_mill"] = mill
                
            all_features.extend(features)
            print(f"  {mill}: {len(features)} geometries collected")
            
        except Exception as e:
            print(f"  {mill}: ERROR - {str(e)}")
    
    if not all_features:
        print("No geometries found to export")
        return None
    
    # Convert to GeoDataFrame
    try:
        # Extract geometries and attributes
        geometries = []
        attributes = []
        
        print(f"Processing {len(all_features)} features...")
        
        for i, feature in enumerate(all_features):
            geom_data = feature.get("geometry")
            if geom_data:
                try:
                    # Debug geometry structure for first feature
                    if i == 0:
                        print(f"  DEBUG - Geometry structure: {geom_data}")
                    
                    # Convert ArcGIS geometry to Shapely geometry
                    # Handle ArcGIS polygon format with rings
                    if 'rings' in geom_data:
                        # ArcGIS polygon format
                        geojson_geom = {
                            "type": "Polygon",
                            "coordinates": geom_data['rings']
                        }
                        geom = shape(geojson_geom)
                    else:
                        # Try standard format
                        geom = shape(geom_data)
                    
                    if geom and not geom.is_empty:
                        geometries.append(geom)
                        attributes.append(feature["attributes"])
                    else:
                        print(f"  Feature {i+1}: Empty geometry, skipping")
                except Exception as geom_error:
                    print(f"  Feature {i+1}: Geometry conversion failed - {geom_error}")
                    # Try to see what the actual geometry data looks like
                    if i < 3:  # Only debug first few features
                        print(f"    DEBUG - Raw geometry: {geom_data}")
            else:
                print(f"  Feature {i+1}: No geometry data")
        
        print(f"Successfully processed {len(geometries)} geometries")
            
        if not geometries:
            print("No valid geometries found after processing")
            return None
            
        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame(attributes, geometry=geometries)
        
        # Set coordinate reference system (assuming Web Mercator or WGS84)
        # Try to detect from first geometry or use common default
        gdf.crs = "EPSG:4326"  # WGS84, most common for web services
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_month = month_info.replace(' ', '_').replace('-', '').strip('_') if month_info else "all_data"
        filename = f"harvest_tracts{safe_month}_{timestamp}.shp"
        
        # Export to shapefile
        gdf.to_file(filename)
        
        print(f"\nGeometry export successful!")
        print(f"File: {filename}")
        print(f"Features: {len(gdf)}")
        print(f"Columns: {', '.join(gdf.columns[:-1])}")  # Exclude geometry column
        print(f"Geometry types: {gdf.geometry.geom_type.value_counts().to_dict()}")
        
        return filename
        
    except Exception as e:
        print(f"Export failed: {str(e)}")
        print(f"Error details: {type(e).__name__}")
        return None


def generate_harvest_report(username=None, password=None, query_month=True, export_geometries=False):
    """Generate harvest report for all mills with optional geometry export."""
    
    # Get month selection
    month_info = ""
    if query_month:
        year, month, month_name = get_month_input()
        month_info = f" - {month_name} {year}"
    
    # Get credentials
    username = username or os.getenv('CANFOR_USERNAME')
    password = password or os.getenv('CANFOR_PASSWORD')
    
    if not username or not password:
        raise ValueError("Username and password required")
    
    # Get authentication
    token, session = get_auth_token(username, password)
    
    # API endpoint and mill locations
    url = "https://maps.canfor.com/arcgis/rest/services/CSPWoodpro/WoodPro_CSP_Data/MapServer/3/query"
    mills = ["AXI", "CAM", "CON", "CRO", "DAR", "DER", "EST-L", "EST-S",
             "FUL", "GRA", "HER", "IRO", "JAC", "LAT", "MLT", "MOB",
             "THM", "URB", "WDC"]
    
    # Core harvest fields 
    fields = "report_location,harvest_status,complete_status,supplier,SaleType,tract_status_desc"
    
    print(f"\nGenerating Harvest Report{month_info}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)
    
    results = []
    total_records = 0
    all_suppliers = set()
    
    for mill in mills:
        try:
            params = {
                "where": f"report_location='{mill}'",
                "outFields": fields,
                "returnGeometry": "false", 
                "f": "json",
                "token": token
            }
            
            response = session.get(url, params=params, timeout=30)
            data = response.json()
            
            if "error" in data:
                print(f"{mill:10} | ERROR: {data['error']['message']}")
                continue
                
            features = data.get("features", [])
            
            if not features:
                print(f"{mill:10} | No data found")
                continue
            
            # Process harvest data
            suppliers = set()
            harvest_statuses = {}
            
            for feature in features:
                attrs = feature.get("attributes", {})
                
                if attrs.get("supplier"):
                    suppliers.add(attrs["supplier"])
                    all_suppliers.add(attrs["supplier"])
                    
                if attrs.get("harvest_status"):
                    status = attrs["harvest_status"]
                    harvest_statuses[status] = harvest_statuses.get(status, 0) + 1
            
            results.append({
                "mill": mill,
                "total_records": len(features),
                "suppliers": list(suppliers),
                "harvest_statuses": harvest_statuses
            })
            
            total_records += len(features)
            
            # Console output
            status_info = f"{len(harvest_statuses)} statuses" if harvest_statuses else "No statuses"
            supplier_info = f"{len(suppliers)} suppliers" if suppliers else "No suppliers"
            print(f"{mill:10} | {len(features):3d} records | {status_info} | {supplier_info}")
            
        except Exception as e:
            print(f'{mill:10} | ERROR: {str(e)}')
    
    # Summary
    print("\n" + "=" * 80)
    print(f"HARVEST SUMMARY{month_info}")
    print(f"Mills processed: {len([r for r in results if r['total_records'] > 0])}/{len(mills)}")
    print(f"Total records: {total_records:,}")
    print(f"Total suppliers: {len(all_suppliers)}")
    
    # Export geometries if requested
    if export_geometries:
        export_geometries_to_shapefile(username, password, token, session, month_info)
    
    return results


if __name__ == "__main__":
    username = "woodpro.access"
    password = "lobloLLy_PL1"
    
    print("WoodPro Harvest Report Generator")
    print("===============================")
    
    # Ask user if they want to export geometries
    export_choice = input("\nExport tract geometries to shapefile? (y/n, default: n): ").strip().lower()
    export_geoms = export_choice in ['y', 'yes']
    
    if export_geoms:
        print("Note: Geometry export will include up to 10 features per mill for the first 3 mills (AXI, CAM, CON)")
    
    generate_harvest_report(
        username=username,
        password=password, 
        query_month=True,
        export_geometries=export_geoms
    )