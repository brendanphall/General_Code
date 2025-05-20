# Import necessary libraries
import requests
import json
import datetime
from pprint import pprint


def query_rest_endpoint():
    """Query ArcGIS REST endpoint for harvest data and display results"""
    try:
        # REST endpoint URL
        rest_url = "https://maps.canfor.com/arcgis/rest/services/CSPWoodpro/WoodPro_NSApps_DB_Views/MapServer/3/query"

        # Calculate date 30 days ago for filtering
        thirty_days_ago = datetime.datetime.now() - datetime.timedelta(days=30)
        date_filter = thirty_days_ago.strftime("%Y-%m-%d")

        # Build query parameters - start simple
        params = {
            'where': "1=1",  # Get all records for testing, we'll filter later
            'outFields': '*',  # Get all fields
            'returnGeometry': 'true',
            'f': 'json',
            'resultRecordCount': 10  # Limit to 10 records for the POC
        }

        print("Querying REST endpoint...")
        print(f"URL: {rest_url}")
        print(f"Parameters: {params}")

        # Make the request
        response = requests.get(rest_url, params=params)

        # Check for HTTP errors
        if response.status_code != 200:
            print(f"Error: HTTP status code {response.status_code}")
            print(f"Response: {response.text}")
            return

        # Parse the JSON response
        data = response.json()

        # Check if we got the expected data structure
        if 'features' not in data:
            print("Warning: 'features' not found in response")
            print("Response structure:")
            pprint(data)
            return

        # Display information about the results
        print(f"\nFound {len(data['features'])} features")

        if len(data['features']) > 0:
            # Display field names from the first feature
            print("\nAvailable fields:")
            fields = list(data['features'][0]['attributes'].keys())
            for field in fields:
                print(f"- {field}")

            # Check if there's any 'days since last harvest' related field
            harvest_fields = [field for field in fields if 'harvest' in field.lower()]
            if harvest_fields:
                print("\nPotential 'days since last harvest' fields:")
                for field in harvest_fields:
                    print(f"- {field}")

            # Display sample data from the first feature
            print("\nSample data (first feature):")
            pprint(data['features'][0])

            # If geometry exists, show its structure too
            if 'geometry' in data['features'][0]:
                print("\nGeometry structure:")
                pprint(data['features'][0]['geometry'])

                # Determine geometry type
                if 'x' in data['features'][0]['geometry'] and 'y' in data['features'][0]['geometry']:
                    print("\nGeometry type: Point")
                elif 'rings' in data['features'][0]['geometry']:
                    print("\nGeometry type: Polygon")
                elif 'paths' in data['features'][0]['geometry']:
                    print("\nGeometry type: Polyline")

    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    query_rest_endpoint()
    print("\nScript execution complete")