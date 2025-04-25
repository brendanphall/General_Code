import arcpy
import os

# Input shapefile path
input_shapefile = r"Z:\GitHub\General_Code\ATFS\5_calc_latlong\test_oregon_shape.shp"

# Output GDB path
base_name = os.path.splitext(os.path.basename(input_shapefile))[0]  # "oregon"
output_folder = os.path.dirname(input_shapefile)
gdb_name = f"{base_name}.gdb"
output_gdb = os.path.join(output_folder, gdb_name)

# Create FileGDB
if not arcpy.Exists(output_gdb):
    arcpy.CreateFileGDB_management(out_folder_path=output_folder, out_name=gdb_name)
    print(f"Created GDB: {output_gdb}")
else:
    print(f"GDB already exists: {output_gdb}")

# Import shapefile into the GDB
arcpy.FeatureClassToFeatureClass_conversion(input_shapefile, output_gdb, base_name)
print(f"✅ Imported shapefile '{base_name}' into geodatabase.")
