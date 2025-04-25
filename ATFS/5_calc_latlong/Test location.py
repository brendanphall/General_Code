import os

shapefile_path = r"Z:\GitHub\General_Code\ATFS\5_calc_latlong\tmp_treefarm\dbo_treefarm.shp"

print("Path exists:", os.path.exists(shapefile_path))

# Print directory contents for debugging
print("Contents of directory:")
print(os.listdir(r"Z:\GitHub\General_Code\ATFS\5_calc_latlong\tmp_treefarm"))
