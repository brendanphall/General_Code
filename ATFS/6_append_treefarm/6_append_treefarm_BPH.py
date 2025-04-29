# -*- coding: utf-8 -*-
#
# This script is run on AGS server
# It appends validated shapefile features to the SDE target
#
import os
import sys
import arcpy

print("Starting...")

# To allow overwriting outputs change overwriteOutput option to True.
arcpy.env.overwriteOutput = False

# 📂 Path to shapefile in folder
shp_folder = os.path.abspath(r'./tmp_treefarm')
tmp_treefarm = os.path.join(shp_folder, 'dbo_treefarm.shp')
print("Using shapefile:", tmp_treefarm)

# 🚫 Ensure shapefile exists
if not os.path.exists(tmp_treefarm):
    print(f"ERROR: Shapefile not found: {tmp_treefarm}")
    sys.exit(1)

# ✅ Ensure required fields are present
expected_fields = ['treefarm_i', 'parcelnumb']
existing_fields = [f.name.lower() for f in arcpy.ListFields(tmp_treefarm)]
missing_fields = [f for f in expected_fields if f.lower() not in existing_fields]
if missing_fields:
    print(f"ERROR: Required field(s) missing in shapefile: {missing_fields}")
    sys.exit(1)

# 🎯 SDE paths
atfs_dbo_treefarm = r"F:\sde_connections\atfs_atfsdb_aws.sde\atfs.dbo.treefarm"
atfs_gdb_DBO_TreeFarm = r"F:\sde_connections\atfs_gdb_atfsdb_aws.sde\atfs_gdb.DBO.TreeFarm"
treefarm_view = "treefarm_view"

# ✅ Count records in shapefile
print("Count records in tmp_treefarm")
num_tmp = int(arcpy.management.GetCount(tmp_treefarm).getOutput(0))

# ✅ Create view on reference table
arcpy.management.MakeTableView(in_table=atfs_dbo_treefarm, out_view=treefarm_view)


# 🔗 Join shapefile to atfs.dbo.treefarm by treefarm_id
print("Add join between tmp_treefarm and atfs.dbo.treefarm on treefarm_id")
atfs_dbo_treefarm_join = arcpy.management.AddJoin(
    in_layer_or_view=tmp_treefarm,
    in_field="treefarm_i",
    join_table=atfs_dbo_treefarm,
    join_field="treefarm_i",
    join_type="KEEP_COMMON",
    index_join_fields="NO_INDEX_JOIN_FIELDS"
)[0]


# 🔢 Count after join
print("Get count after join")
num_join = int(arcpy.management.GetCount(atfs_dbo_treefarm_join).getOutput(0))
print("Tree Farm counts after join: {0} --> {1}".format(num_tmp, num_join))

# If counts are not equal, then stop and determine which tree farms are not in ATFS database
if num_tmp != num_join:
	print ("Tree Farm counts after join not equal: {0} --> {1}".format(num_tmp, num_join))
	sys.exit()


# Remove all joins with error handling
if arcpy.Exists(atfs_dbo_treefarm_join):
    arcpy.management.RemoveJoin(in_layer_or_view=atfs_dbo_treefarm_join, join_name="")
else:
    print("Warning: Join layer no longer exists")

if arcpy.Exists(treefarm_view):
    arcpy.management.Delete(treefarm_view)


# 🔎 Check for existing geometries
print("Check to see if there are any geometries already present in atfs_gdb for the incoming tree farms")
arcpy.management.MakeTableView(in_table=atfs_gdb_DBO_TreeFarm, out_view=treefarm_view)

print("Add join between tmp_treefarm and atfs_gdb.dbo.treefarm on treefarm_id")
atfs_gdb_dbo_treefarm_join = arcpy.management.AddJoin(
    in_layer_or_view=tmp_treefarm,
    in_field="treefarm_i",
    join_table=atfs_gdb_DBO_TreeFarm,
    join_field="treefarm_i",
    join_type="KEEP_COMMON",
    index_join_fields="NO_INDEX_JOIN_FIELDS"
)[0]

print("Get count after join")
num_join = int(arcpy.management.GetCount(atfs_gdb_dbo_treefarm_join).getOutput(0))
print("Tree Farm counts after geometry check join: {0} --> {1}".format(num_tmp, num_join))


# ❌ Abort if any geometries already exist in the target
# If count > 0 then there are existing tree farm geometries
# Either have to delete the geometries in atfs_gdb or delete them from the incoming dataset
if num_join > 0:
    print("Existing Tree Farm geometries found: {0}".format(num_join))
    print("Either delete geometries from atfs_gdb or skip those from the shapefile.")
    sys.exit(1)

# Remove all joins with error handling
if arcpy.Exists(atfs_gdb_dbo_treefarm_join):
    arcpy.management.RemoveJoin(in_layer_or_view=atfs_gdb_dbo_treefarm_join, join_name="")
else:
    print("Warning: Join layer no longer exists")

print("Append records from tmp_treefarm to atfs_gdb.dbo.treefarm")

try:
    arcpy.management.Append(
        inputs=tmp_treefarm,
        target=atfs_gdb_DBO_TreeFarm,
        schema_type="NO_TEST",
        field_mapping=r'treefarm_i "treefarm_id" true true false 8 Double 0 0,First,#,{0},treefarm_i,-1,-1;parcelnumb "parcelnumber" true true false 8 Double 0 0,First,#,{0},parcelnumb,-1,-1'.format(tmp_treefarm),
        subtype="",
        expression=""
    )
    print(f"Append complete ✅ {num_tmp} features added.")
except Exception as e:
    print(f"Error during append operation: {e}")
    sys.exit(1)


