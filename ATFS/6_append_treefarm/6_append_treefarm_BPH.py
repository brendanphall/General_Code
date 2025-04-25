# -*- coding: utf-8 -*-
#
# This script is run on AGS server
#
import os,sys
print("Starting...")
import arcpy

# To allow overwriting outputs change overwriteOutput option to True.
arcpy.env.overwriteOutput = False

gdb = os.path.abspath(r'.\atfs_update.gdb')
print(gdb)
tmp_treefarm = os.path.join(gdb, 'tmp_treefarm')

atfs_dbo_treefarm = "F:\\sde_connections\\atfs_atfsdb_aws.sde\\atfs.dbo.treefarm"
atfs_gdb_DBO_TreeFarm = "F:\\sde_connections\\atfs_gdb_atfsdb_aws.sde\\atfs_gdb.DBO.TreeFarm"
treefarm_view = "treefarm_view"

print("Count records in tmp_treefarm")
num_tmp = int(arcpy.management.GetCount(tmp_treefarm).getOutput(0))

arcpy.management.MakeTableView(in_table=atfs_dbo_treefarm, out_view=treefarm_view)

print("Add join between tmp_treefarm and atfs.dbo.treefarm on treefarm_id")
atfs_dbo_treefarm_join = arcpy.management.AddJoin(in_layer_or_view=tmp_treefarm, in_field="treefarm_id", join_table=atfs_dbo_treefarm, join_field="treefarm_id", join_type="KEEP_COMMON", index_join_fields="NO_INDEX_JOIN_FIELDS")[0]

print("Get count after join")
num_join = int(arcpy.management.GetCount(atfs_dbo_treefarm_join).getOutput(0))

print ("Tree Farm counts after join: {0} --> {1}".format(num_tmp, num_join))

# If counts are not equal, then stop and determine which tree farms are not in ATFS database
if num_tmp != num_join:
	print ("Tree Farm counts after join not equal: {0} --> {1}".format(num_tmp, num_join))
	sys.exit()

# Remove all joins
arcpy.management.RemoveJoin(in_layer_or_view=atfs_dbo_treefarm_join, join_name="")

if arcpy.Exists(treefarm_view):
	arcpy.management.Delete(treefarm_view)
	
print("Check to see if there are any geometries already present in atfs_gdb for the incoming tree farms")
arcpy.management.MakeTableView(in_table=atfs_gdb_DBO_TreeFarm, out_view=treefarm_view)

print("Add join between tmp_treefarm and atfs_gdb.dbo.treefarm on treefarm_id")
atfs_gdb_dbo_treefarm_join = arcpy.management.AddJoin(in_layer_or_view=tmp_treefarm, in_field="treefarm_id", join_table=atfs_gdb_DBO_TreeFarm, join_field="treefarm_id", join_type="KEEP_COMMON", index_join_fields="NO_INDEX_JOIN_FIELDS")[0]

print("Get count after join")
num_join = int(arcpy.management.GetCount(atfs_gdb_dbo_treefarm_join).getOutput(0))

print ("Tree Farm counts after join: {0} --> {1}".format(num_tmp, num_join))

# If count > 0 then there are existing tree farm geometries
# Either have to delete the geometries in atfs_gdb or delete them from the incoming dataset
if num_join > 0:
	print ("Existing Tree Farm geometries found: {0}".format(num_join))
	print ("Either have to delete the geometries in atfs_gdb or delete them from the incoming dataset")
	sys.exit()

# Remove all joins
arcpy.management.RemoveJoin(in_layer_or_view=atfs_gdb_dbo_treefarm_join, join_name="")

print("Append records from tmp_treefarm to atfs_gdb.dbo.treefarm")
arcpy.management.Append(inputs=tmp_treefarm, target=atfs_gdb_DBO_TreeFarm, schema_type="NO_TEST", field_mapping=r'treefarm_id "treefarm_id" true true false 4 Long 0 10,First,#,{0},treefarm_id,-1,-1;parcelnumber "parcelnumber" true true false 2 Short 0 5,First,#,{0},parcelnumber,-1,-1'.format(tmp_treefarm), subtype="", expression="")

