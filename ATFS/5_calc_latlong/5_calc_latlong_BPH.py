# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
import os,sys
print("Starting...")
# Import arcpy module
import arcpy

gdb = os.path.abspath(r'oregon.gdb')
print(gdb)
tmp_treefarm = os.path.join(gdb, 'tmp_treefarm')

with arcpy.EnvManager(geographicTransformations="WGS_1984_(ITRF00)_To_NAD_1983"):
	print("calc dlong/dlat/totalacres")
	arcpy.management.CalculateGeometryAttributes(
		in_features=tmp_treefarm,
		geometry_property="dlongitude INSIDE_X;dlatitude INSIDE_Y;totalacres AREA",
		length_unit="",
		area_unit="ACRES_US",
		coordinate_system='PROJCS["USA_Contiguous_Albers_Equal_Area_Conic",GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Albers"],PARAMETER["False_Easting",0.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",-96.0],PARAMETER["Standard_Parallel_1",29.5],PARAMETER["Standard_Parallel_2",45.5],PARAMETER["Latitude_Of_Origin",37.5],UNIT["Meter",1.0]]',
		coordinate_format="DD"
	)

print("calc long/lat")
arcpy.management.CalculateField(
	in_table=tmp_treefarm,
	field="longitude",
	expression='"%.6f" % !dlongitude!',
	expression_type="PYTHON3",
	code_block="",
	field_type="TEXT",
	enforce_domains="NO_ENFORCE_DOMAINS"
)
arcpy.management.CalculateField(
	in_table=tmp_treefarm,
	field="latitude",
	expression='"%.6f" % !dlatitude!',
	expression_type="PYTHON3",
	code_block="",
	field_type="TEXT",
	enforce_domains="NO_ENFORCE_DOMAINS"
)

print("create 7_update_treefarm.sql")
outfile_location = os.path.abspath('.\\')
sqlfile = os.path.join(outfile_location, "7_update_treefarm.sql")
if os.path.isfile(sqlfile):
	os.remove(sqlfile)
f_sql = open(sqlfile, "w")
f_sql.write("use atfs\n")
f_sql.write("go\n")

with arcpy.da.SearchCursor(tmp_treefarm, ['treefarm_id', 'totalforestedacres', 'longitude', 'latitude', 'totalacres']) as cursor:
	for row in cursor:
		treefarm_id = row[0]
		totalforestedacres = round(row[1], 2)
		longitude = row[2]
		latitude = row[3]
		totalacres = round(row[4], 2)
		if totalforestedacres > totalacres or abs(totalforestedacres - totalacres) < 0.1:
			totalforestedacres = totalacres

		sql1 = "update treefarm set totalacres = {0}, totalforestedacres = {1} where treefarm_id = {2}".format(totalacres, totalforestedacres, treefarm_id)
		sql2 = "update treefarmlocation set acres = {0}, longitude = '{1}', latitude = '{2}', forestedacres = {3} where treefarm_id = {4}".format(totalacres, longitude, latitude, totalforestedacres, treefarm_id)

		f_sql.write(sql1+"\n")
		f_sql.write(sql2+"\n")

f_sql.close()

