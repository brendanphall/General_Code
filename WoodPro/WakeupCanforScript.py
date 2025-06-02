"""
A utility script for querying one location to "wake" up the map service

Author: Morgan Cameron, Sewall
Date: 6/2/2025
Version: 1.2 - added authentication to call to map service
"""

import time
import datetime
from datetime import timedelta
import os, sys

# print("Starting...")
import arcpy
from arcgis.gis import GIS
from arcgis.features import FeatureLayer

# location list
locations = ["FUL"]

# locations = ["AXI", "CAM", "CON", "CRO", "CWY", "DAR", "DER", "EST-L", "EST-S", "FUL", "GRA", "HER", "IRO", "JAC", "LAT", "MLT", "MOB", "THM", "URB", "WDC"]

# gis
# print("Login...")
portal = "https://maps.canfor.com/portal"
username = "woodpro.access"
password = "lobloLLy_PL1"
gis = GIS(portal, username, password) #, verify_cert=False)

gis_server = "https://maps.canfor.com/arcgis/rest/services/CSPWoodpro"

# woodpro.csp_01_woodpro_foresters_vw (1)
# woodpro.csp_02_woodpro_forester_locations_vw (2)
# woodpro.csp_10_woodpro_tract_lookup_vw (3)
# woodpro.csp_11_woodpro_tract_header_vw (4)
# woodpro.csp_20_woodpro_tract_cruise_cut_pricing_vw (5)
# woodpro.csp_30_woodpro_tract_payments_vw (6)
# woodpro.csp_99_woodpro_cruise_vol_det_vw (7)
# woodpro.csp_99_woodpro_cut_vol_det_vw (8)
# woodpro.csp_99_woodpro_tract_pay_structure_pivot_base_vw (9)

# 3 = woodpro.csp_10_woodpro_tract_lookup_vw
url = f"{gis_server}/WoodPro_CSP_Data/MapServer/3"
layer = FeatureLayer(url, gis=gis)

fields = "report_location,report_tract_no,Tract_Name,tract_status_desc,Forester,tract_type_family,SaleType,latitude_dd,longitude_dd,Wthr_grd,PurchDate,harvest_status"

currentDateTime = datetime.datetime.now().replace(microsecond=0)

for loc in locations:

	try:
		where = f"report_location='{loc}'"

		# print("Get count")
		count = layer.query(where = where, out_fields = fields, return_count_only = True)

		# print("Actual query")
		start = time.time()
		features = layer.query(where=where, out_fields=fields, return_geometry=False).features
		elapsed = round((time.time() - start) * 1000)

		# Get features count
		features_count = len(features)

		print(f'{currentDateTime} {{ "report_location": "{loc}", "total_count": {count}, "returned_count": {features_count}, "time": "{elapsed:,} ms" }}')

	except Exception as e:
		print(f'{{ "report_location": "{loc}", "error": "{str(e)}", "time": "N/A" }}')
