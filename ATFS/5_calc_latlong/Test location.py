import os
import arcpy

shapefile_path = r"Z:\GitHub\General_Code\ATFS\5_calc_latlong\tmp_treefarm\dbo_treefarm.shp"

print("Path exists:", os.path.exists(shapefile_path))

# Print directory contents for debugging
print("Contents of directory:")
print(os.listdir(r"Z:\GitHub\General_Code\ATFS\5_calc_latlong\tmp_treefarm"))

# Print fields in the shapefile
if os.path.exists(shapefile_path):
    print("Fields in the shapefile:")
    fields = arcpy.ListFields(shapefile_path)
    for field in fields:
        print(f"- {field.name} ({field.type})")
else:
    print("Shapefile does not exist, cannot list fields.")

