"""
A utility script for exporting tract geometries with days_since_last_load <= N
where N is the number of days in the previous month.

Author: Morgan Cameron, Sewall
Date: 6/5/2025

6/9/2025 Changed to set start/end values for days_since_last_load relative to current date
  e.g., if script is run on June 9, the number of days in May is 31 and days_since_last_load
  would be 9 to 39 (days_since_last_load = 0 == "today")

7/15/2025
	Changed to use csp_11_woodpro_tract_header_vw view
	Changed fields returned
	Changed output to separate shapefile for each "primary_loc"

"""

import time
import datetime
from datetime import timedelta
import os, sys
import calendar
import json

print("===============================================")
currentDateTime = datetime.datetime.now().replace(microsecond=0)
print(currentDateTime)
cd_mm = currentDateTime.strftime("%m")   # this returns a leading 0 on months < 10
cd_mmm = currentDateTime.strftime("%b")  # Month name, short version
cd_dd = currentDateTime.day
cd_yyyy = currentDateTime.year

# get tracts for last month
tddays = datetime.timedelta(days=cd_dd)
yesterday = currentDateTime - tddays
mm = yesterday.strftime("%m")   # this returns a leading 0 on months < 10
mmm = yesterday.strftime("%b")  # Month name, short version
dd = yesterday.day
yyyy = yesterday.year

numdays = calendar.monthrange(yyyy, int(mm))[1]

start = cd_dd
end = numdays + cd_dd - 1

print("{0} {1} {2} {3} {4} days".format(start, end, mmm, yyyy, numdays))

sys.stdout.flush()

import arcpy
from arcgis.gis import GIS
from arcgis.features import FeatureLayerCollection, FeatureLayer, Feature

# report_loc list
report_locations = ['AXI', 'CAM', 'CON', 'CRO', 'DAR', 'DER', 'EST-L', 'EST-S', 'FUL', 'GRA', 'HER', 'IRO', 'JAC', 'MLT', 'MOB', 'THM', 'URB']

# primary_loc list
primary_locs = ['Axis', 'Camden', 'Conway', 'Crosby', 'Darlington', 'DeRidder', 'Estill_Large_Mill', 'Estill_Small_Mill', 'Fulton', 'Graham', 'Hermanville', 'Iron_Mountain', 'Jackson', 'Moultrie', 'Mobile', 'Thomasville', 'Urbana']

primary_loc_dict = dict(zip(report_locations, primary_locs))

# gis
# print("Login WoodPro...")
woodpro_username = 'canfor_app'
woodpro_password = 'canfor$1234'
woodpro_portal = "https://maps.sewall.com/portal2"
woodpro_gis = GIS(woodpro_portal, woodpro_username, woodpro_password) #, verify_cert=False)
woodpro_gis_server_url = "https://maps.sewall.com/server2/rest/services/canfor/SalesService/FeatureServer"

layers = FeatureLayerCollection(woodpro_gis_server_url, woodpro_gis)

url = ""

# All Tracts
for lyr in layers.layers:
	if lyr.properties.name == "All Tracts":
		name = lyr.properties.name
		url = lyr.url
		layerId_tracts = str(lyr.properties.id)
		break

if url == "":
	print("ERROR: Unable to locate layer All Tracts")
	sys.exit()

woodpro_all_tracts = url  #woodpro_gis_server_url + "/10"

# print("Login Canfor...")
canfor_username = "woodpro.access"
canfor_password = "lobloLLy_PL1"
canfor_portal = "https://maps.canfor.com/portal"
canfor_gis = GIS(canfor_portal, canfor_username, canfor_password) #, verify_cert=False)

canfor_gis_server_url = "https://maps.canfor.com/arcgis/rest/services/CSPWoodpro/WoodPro_CSP_Data/MapServer"

# woodpro.csp_01_woodpro_foresters_vw (1)
# woodpro.csp_02_woodpro_forester_locations_vw (2)
# woodpro.csp_10_woodpro_tract_lookup_vw (3)
# woodpro.csp_11_woodpro_tract_header_vw (4)
# woodpro.csp_20_woodpro_tract_cruise_cut_pricing_vw (5)
# woodpro.csp_30_woodpro_tract_payments_vw (6)
# woodpro.csp_99_woodpro_cruise_vol_det_vw (7)
# woodpro.csp_99_woodpro_cut_vol_det_vw (8)
# woodpro.csp_99_woodpro_tract_pay_structure_pivot_base_vw (9)
# woodpro.csp_99_woodpro_company_loggers_vw (10)
# woodpro.csp_30_woodpro_company_loggers_vw (11)

layers = FeatureLayerCollection(canfor_gis_server_url, canfor_gis)

url = ""
# woodpro.csp_10_woodpro_tract_lookup_vw
for tbl in layers.tables:
	if tbl.properties.name == "woodpro.csp_10_woodpro_tract_lookup_vw":
		name = tbl.properties.name
		url = tbl.url
		layerId_view = str(tbl.properties.id)
		break

if url == "":
	print("ERROR: Unable to locate view woodpro.csp_10_woodpro_tract_lookup_vw")
	sys.exit()

canfor_View = url
canfor_Layer = FeatureLayer(canfor_View, gis=canfor_gis)

canfor_fields = "latitude_dd,longitude_dd,primary_loc,report_tract_no,begin_month,begin_year,end_month,end_year"

wp_fields = "report_location,report_tract_no,tract_name,tract_status_desc,forester,tract_type_family,harvest_status"

# Using geb to store all of the tract geometries locally and project from web mercator to albers
here = os.path.abspath(".\\")
export_gdb = os.path.join(here, "Tracts_Export.gdb")
shapefiles_fldr = os.path.join(here, "Shapefiles")
temp_Layer = "temp_Layer"

if arcpy.Exists(export_gdb):
	arcpy.Delete_management(export_gdb)

arcpy.CreateFileGDB_management(os.path.dirname(export_gdb), os.path.basename(export_gdb))

print("Get All Tracts...")
tracts_Layer = FeatureLayer(woodpro_all_tracts, gis=woodpro_gis)

tracts_Layer.query().save(export_gdb, "All_Tracts_wm")

all_tracts_wm = os.path.join(export_gdb, "All_Tracts_wm")
all_tracts = os.path.join(export_gdb, "All_Tracts")

print("Project...")
arcpy.management.Project(all_tracts_wm, all_tracts, 'PROJCS["USA_Contiguous_Albers_Equal_Area_Conic",GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Albers"],PARAMETER["False_Easting",0.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",-96.0],PARAMETER["Standard_Parallel_1",29.5],PARAMETER["Standard_Parallel_2",45.5],PARAMETER["Latitude_Of_Origin",37.5],UNIT["Meter",1.0]]', "WGS_1984_(ITRF00)_To_NAD_1983", 'PROJCS["WGS_1984_Web_Mercator_Auxiliary_Sphere",GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Mercator_Auxiliary_Sphere"],PARAMETER["False_Easting",0.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",0.0],PARAMETER["Standard_Parallel_1",0.0],PARAMETER["Auxiliary_Sphere_Type",0.0],UNIT["Meter",1.0]]', "NO_PRESERVE_SHAPE", None, "NO_VERTICAL")

if arcpy.Exists(all_tracts_wm):
	arcpy.Delete_management(all_tracts_wm)

# Add delivery month/year and supplier fields
supplier = "'Canfor'"
arcpy.management.AddField(all_tracts, "del_month", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.management.AddField(all_tracts, "del_year", "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.management.AddField(all_tracts, "supplier", "TEXT", "", "", "16", "", "NULLABLE", "NON_REQUIRED", "")
arcpy.management.CalculateFields(all_tracts, "PYTHON3", [["del_month", int(mm)], ["del_year", int(yyyy)], ["supplier", supplier]])

# Get all of the tracts with days_since_last_load in the target range
where = f"days_since_last_load >= {start} and days_since_last_load <= {end} and report_location in ({str(report_locations).replace('[','').replace(']','')})"

print("Get report_location list")
fs = canfor_Layer.query(where=where, out_fields="report_location", return_count_only=False, return_geometry=False, return_distinct_values=True, f="json")

results = str(fs)

# Make unique list of report_location values
loc_dict = json.loads(results)
features = loc_dict['features']
locations = []
for i in features:
	loc = i['attributes']['report_location']
	locations.append(loc.replace(" ","_"))
# print(locations)

numLocations = len(locations)
if numLocations > 0:
	for loc in locations:
		print(loc)

		# Create feature layer of the tract geometries for the given location
		if arcpy.Exists(temp_Layer):
			arcpy.Delete_management(temp_Layer)
		arcpy.management.MakeFeatureLayer(in_features=all_tracts, out_layer=temp_Layer, where_clause=f"report_location='{loc}'", workspace="", field_info="")

		# Only need to proceed if there are any tract geometries for the given location
		if int(arcpy.GetCount_management(temp_Layer)[0]) > 0:
			# 0 days == today, null would indicate no loads

			where = f"report_location='{loc}' and days_since_last_load >= {start} and days_since_last_load <= {end}"

			if "-" in loc:
				tblname = loc.replace("-", "_")
			else:
				tblname = loc
			tblname = tblname+"_att"

			outtbl = os.path.join(export_gdb, tblname)
			if arcpy.Exists(outtbl):
				arcpy.Delete_management(outtbl)

			results = canfor_Layer.query(where = where, out_fields = canfor_fields, return_geometry = False)

			for index, item in enumerate(results.fields):
				# print(f"Index: {index}, Item: {item}")
				if item['name'] == "ESRI_OID":
					results.fields[index]['type']='esriFieldTypeInteger'
					results.fields[index]['name']='OBJECTID_1'
					results.fields[index]['alias']='OBJECTID_1'
				if item['name'] == "OBJECTID":
					results.fields[index]['type']='esriFieldTypeInteger'
					results.fields[index]['name']='OBJECTID_2'
					results.fields[index]['alias']='OBJECTID_2'

			results.save(export_gdb, tblname)

			arcpy.management.DeleteField(outtbl, ["OBJECTID_1", "OBJECTID_2"])

			arcpy.management.AddJoin(temp_Layer, "report_tract_no", outtbl, "report_tract_no", "KEEP_COMMON")
			count = int(arcpy.GetCount_management(temp_Layer)[0])
			if count > 0:
				print(".. {0} : {1}".format(loc, count))
				fcname = primary_loc_dict[loc]
				outfc = os.path.join(export_gdb, fcname)

				arcpy.conversion.ExportFeatures(in_features=temp_Layer, out_features=outfc, field_mapping="")

				arcpy.management.DeleteField(outfc, ["report_tract_no_1", "OBJECTID_1", "report_location", "tract_type_family", "tract_status_desc", "harvest_status", "forester", "tract_name"])

				outshp = os.path.join(shapefiles_fldr, fcname+".shp")

				if arcpy.Exists(outshp):
					arcpy.Delete_management(outshp)

				# arcpy.conversion.ExportFeatures(
					# in_features=outfc,
					# out_features=outshp,
					# where_clause="",
					# use_field_alias_as_name="NOT_USE_ALIAS",
					# field_mapping="",
					# sort_field=None
				# )

				arcpy.conversion.ExportFeatures(in_features=outfc, out_features=outshp, field_mapping="latitude \"latitude\" true true false 8 Double 0 0,First,#,{0},latitude_dd,-1,-1;longitude \"longitude\" true true false 8 Double 0 0,First,#,{0},longitude_dd,-1,-1;del_month \"del_month\" true true false 4 Long 0 0,First,#,{0},del_month,-1,-1;del_year \"del_year\" true true false 4 Long 0 0,First,#,{0},del_year,-1,-1;pri_mill \"pri_mill\" true true false 50 Text 0 0,First,#,{0},primary_loc,0,49;tract_name \"tract_name\" true true false 4 Long 0 0,First,#,{0},report_tract_no,-1,-1;supplier \"supplier\" true true false 16 Text 0 0,First,#,{0},supplier,0,15;startmonth \"startmonth\" true true false 4 Long 0 0,First,#,{0},begin_month,-1,-1;startyear \"startyear\" true true false 4 Long 0 0,First,#,{0},begin_year,-1,-1;endmonth \"endmonth\" true true false 4 Long 0 0,First,#,{0},end_month,-1,-1;endyear \"endyear\" true true false 4 Long 0 0,First,#,{0},end_year,-1,-1;Shape_Length \"Shape_Length\" false true true 8 Double 0 0,First,#,{0},Shape_Length,-1,-1;Shape_Area \"Shape_Area\" false true true 8 Double 0 0,First,#,{0},Shape_Area,-1,-1".format(outfc))

			if arcpy.Exists(outtbl):
				arcpy.Delete_management(outtbl)

			sys.stdout.flush()

arcpy.Delete_management(all_tracts)

print("Done")
