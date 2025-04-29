Here’s a concise `.md` file summarizing what you just did to replicate the two types of ArcGIS REST API performance queries using `curl` and Python:

---

```markdown
# ArcGIS REST Query Performance Testing

This document summarizes methods used to test and benchmark query performance against the Canfor ArcGIS REST endpoint by evaluating response time for various `report_location` values.

## ✅ Goal

To compare query performance when requesting records from the `WoodPro_NSApps_DB_Views/MapServer/3` layer, especially when including the `harvest_status` field.

---

## 1. Bash + `curl` Testing

A bash script loops through a list of `report_location` codes and:
- Measures total time to fetch 2000 records
- Separately queries the count of records returned

### Script:

```bash
#!/bin/bash

locations=("AXI" "CAM" "CON" "CRO" "DAR" "DER" "EST-L" "EST-S" "FUL" "GRA" "HER" "IRO" "JAC" "LAT" "MLT" "MOB" "THM" "URB" "WDC")

for loc in "${locations[@]}"; do
  echo -n "Testing $loc... "
  time_ms=$(curl -s -o /dev/null -w "%{time_total}" "https://maps.canfor.com/arcgis/rest/services/CSPWoodpro/WoodPro_NSApps_DB_Views/MapServer/3/query?where=report_location%3D%27${loc}%27&outFields=report_location,report_tract_no,Tract_Name,tract_status_desc,Forester,tract_type_family,SaleType,latitude_dd,longitude_dd,Wthr_grd,PurchDate,harvest_status&resultRecordCount=2000&f=json")
  
  count=$(curl -s "https://maps.canfor.com/arcgis/rest/services/CSPWoodpro/WoodPro_NSApps_DB_Views/MapServer/3/query?where=report_location%3D%27${loc}%27&returnCountOnly=true&f=json" | jq -r '.count')
  
  echo "{ \"report_location\": \"$loc\", \"count\": $count, \"time\": \"$(printf "%.0f" $(echo "$time_ms * 1000" | bc)) ms\" }"
done
```

> 🔧 Dependencies: `jq`, `bc`, `curl`

---

## 2. Python Version

A Python script performs the same function using `requests`.

### Script:

```python
import requests
import time

locations = [
    "AXI", "CAM", "CON", "CRO", "DAR", "DER", "EST-L", "EST-S", "FUL", "GRA",
    "HER", "IRO", "JAC", "LAT", "MLT", "MOB", "THM", "URB", "WDC"
]

url = "https://maps.canfor.com/arcgis/rest/services/CSPWoodpro/WoodPro_NSApps_DB_Views/MapServer/3/query"

for loc in locations:
    params = {
        "where": f"report_location='{loc}'",
        "outFields": "report_location,report_tract_no,Tract_Name,tract_status_desc,Forester,tract_type_family,SaleType,latitude_dd,longitude_dd,Wthr_grd,PurchDate,harvest_status",
        "resultRecordCount": 2000,
        "f": "json",
        "returnGeometry": "false"
    }

    count_params = {
        "where": f"report_location='{loc}'",
        "returnCountOnly": "true",
        "f": "json"
    }

    count_resp = requests.get(url, params=count_params)
    count = count_resp.json().get("count", 0)

    start = time.time()
    requests.get(url, params=params)
    elapsed = round((time.time() - start) * 1000)

    print(f'{{ "report_location": "{loc}", "count": {count}, "time": "{elapsed:,} ms" }}')
```

> 💡 Requires: `pip install requests`

---

## ✅ Output Format

Each location’s test result outputs as:

```json
{ "report_location": "CAM", "count": 875, "time": "63,446 ms" }
```

This allows easy visual inspection of slow vs fast queries and correlates count size to time.

---

## 📊 Purpose

Used to:
- Measure the effect of including `harvest_status` in large queries
- Monitor improvements based on backend view optimizations
- Identify locations approaching or exceeding timeout thresholds

---

Let me know if you want this saved as a file or posted in a wiki/Notion!
```