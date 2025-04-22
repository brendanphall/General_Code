# ---------------------------------------------------------------------------
# Script to identify non-contiguous tree farms using feature class 'OR_33'
# ---------------------------------------------------------------------------
import arcpy
import os
import sys

print("Starting...")

# Set environment settings
arcpy.env.overwriteOutput = True

# Check if ArcGIS Pro is properly connected
try:
    arcpy.GetInstallInfo()
    print("ArcGIS Pro connection successful")
except:
    print("Error: Cannot connect to ArcGIS Pro. Please make sure it's installed and properly configured")
    sys.exit()

# Directly specify path to feature class
TreeFarm = r"P:\Projects\ATFS\_Projects\Lloyd\20250421_Oregon\OR_33\OR_33.shp"

# Verify TreeFarm exists
if not arcpy.Exists(TreeFarm):
    print(f"Error: Feature class {TreeFarm} not found")
    sys.exit()

print(f"Using tree farm feature class: {TreeFarm}")

# Set up workspace for temporary outputs (scratch geodatabase)
scratch_gdb = arcpy.env.scratchGDB
print(f"Using scratch workspace: {scratch_gdb}")

# Define output and temporary feature classes
TreeFarmSingle = os.path.join(scratch_gdb, "TreeFarmSingle")
TreeFarmAlbers = os.path.join(scratch_gdb, "TreeFarmAlbers")
freq = os.path.join(scratch_gdb, "Freq")
tf_buffer = os.path.join(scratch_gdb, "tf_buffer")
tf_bufferSingle = os.path.join(scratch_gdb, "tf_bufferSingle")

# Define variables
freq_view = "freq_view"
near_view = "near_view"
treefarm_layer = "treefarm_layer"
maxdist = 42  # feet
buffdist = "42 feet"

# Clean up any existing temporary data
for temp_data in [TreeFarmSingle, TreeFarmAlbers, freq, tf_buffer, tf_bufferSingle]:
    if arcpy.Exists(temp_data):
        arcpy.Delete_management(temp_data)
        print(f"Deleted existing {os.path.basename(temp_data)}")

# Convert to single part
print("Converting multipart to singlepart...")
arcpy.management.MultipartToSinglepart(
    in_features=TreeFarm,
    out_feature_class=TreeFarmSingle
)
print(f"Created {TreeFarmSingle}")

# Project to Albers
print("Projecting to Albers Equal Area...")
try:
    # Get the spatial reference for USA Contiguous Albers Equal Area Conic
    sr_albers = arcpy.SpatialReference(102003)

    # Corrected parameter names for ArcGIS Pro
    arcpy.management.Project(
        in_dataset=TreeFarmSingle,
        out_dataset=TreeFarmAlbers,
        out_coor_system=sr_albers,  # Fixed parameter name
        transform_method="",
        in_coor_system="",
        preserve_shape="NO_PRESERVE_SHAPE",
        max_deviation="",
        vertical="NO_VERTICAL"
    )
    print(f"Created {TreeFarmAlbers}")
except Exception as e:
    print(f"Error during projection: {str(e)}")
    print("Attempting alternative projection method...")
    try:
        # Alternative method: copy features and define projection
        arcpy.CopyFeatures_management(TreeFarmSingle, TreeFarmAlbers)
        arcpy.DefineProjection_management(TreeFarmAlbers, sr_albers)
        print(f"Created {TreeFarmAlbers} using alternative method")
    except Exception as e2:
        print(f"Alternative projection also failed: {str(e2)}")
        sys.exit()

# Check if the field 'treefarm_id' exists
field_names = [f.name.lower() for f in arcpy.ListFields(TreeFarmAlbers)]
if 'treefarm_id' not in field_names:
    print("Warning: 'treefarm_id' field not found in the feature class.")
    print("Available fields:", [f for f in field_names])
    tf_id_field = input("Enter the name of the tree farm ID field to use: ")
    if not tf_id_field or tf_id_field.lower() not in field_names:
        print("Error: Invalid field name or no field specified")
        sys.exit()
else:
    tf_id_field = 'treefarm_id'
    print("Using 'treefarm_id' field")

# Determine field type for proper SQL formatting
field_type = None
for field in arcpy.ListFields(TreeFarmAlbers):
    if field.name.lower() == tf_id_field.lower():
        field_type = field.type
        print(f"Field type for {tf_id_field}: {field_type}")
        break

# Create frequency table
print("Creating frequency table...")
arcpy.analysis.Frequency(
    in_table=TreeFarmAlbers,
    out_table=freq,
    frequency_fields=tf_id_field,
    summary_fields=None
)
print(f"Created frequency table: {freq}")

# Create table view of tree farms with multiple parts
print("Finding tree farms with multiple parts...")
if arcpy.Exists(freq_view):
    arcpy.Delete_management(freq_view)
arcpy.MakeTableView_management(freq, freq_view, "FREQUENCY > 1", "", "")
result = arcpy.GetCount_management(freq_view)
Count = int(result.getOutput(0))
print("Number of tree farms with multiple parts: {0}".format(Count))

# Process tree farms with multiple parts to find non-contiguous ones
noncontiguous_treefarm_ids = []
if Count > 0:
    with arcpy.da.SearchCursor(freq_view, [tf_id_field], "") as cur:
        for row in cur:
            treefarm_id = row[0]
            print(f"Processing treefarm_id: {treefarm_id}")

            # Create layer for current tree farm - Format SQL properly based on field type
            if arcpy.Exists(treefarm_layer):
                arcpy.Delete_management(treefarm_layer)

            # Properly format SQL expression based on field type
            if field_type == 'String' or field_type == 'Text':
                # For string fields, use quotes and proper string formatting
                where_clause = f"{tf_id_field} = '{treefarm_id}'"
            else:
                # For numeric fields
                where_clause = f"{tf_id_field} = {treefarm_id}"

            print(f"Using where clause: {where_clause}")

            arcpy.MakeFeatureLayer_management(
                TreeFarmAlbers,
                treefarm_layer,
                where_clause,
                "",
                ""
            )

            # Check if any features exist for this tree farm
            result = arcpy.GetCount_management(treefarm_layer)
            TFCount = int(result.getOutput(0))
            print(f"Found {TFCount} features for tree farm {treefarm_id}")

            if TFCount > 0:
                # Create buffer to test contiguity
                if arcpy.Exists(tf_buffer):
                    arcpy.Delete_management(tf_buffer)
                arcpy.analysis.Buffer(
                    treefarm_layer,
                    tf_buffer,
                    buffdist,
                    "FULL",
                    "ROUND",
                    "ALL",
                    ""
                )

                # Convert buffer to single part
                if arcpy.Exists(tf_bufferSingle):
                    arcpy.Delete_management(tf_bufferSingle)
                arcpy.management.MultipartToSinglepart(
                    in_features=tf_buffer,
                    out_feature_class=tf_bufferSingle
                )

                # Count buffer parts - if more than 1, tree farm is non-contiguous
                result = arcpy.GetCount_management(tf_bufferSingle)
                buffcount = int(result.getOutput(0))
                print(f"Buffer has {buffcount} parts")
                if buffcount > 1:
                    noncontiguous_treefarm_ids.append(treefarm_id)
                    print(f"  Tree farm {treefarm_id} is non-contiguous")

# Print results
print("\nNon-contiguous tree farm IDs:")
print(noncontiguous_treefarm_ids)
print("Total non-contiguous tree farms:", len(noncontiguous_treefarm_ids))

# Save results to a text file
results_path = os.path.dirname(os.path.abspath(__file__))  # Save in the same folder as the script
results_file = os.path.join(results_path, "noncontiguous_farms.txt")
with open(results_file, 'w') as f:
    f.write("Non-contiguous tree farm IDs:\n")
    for id in noncontiguous_treefarm_ids:
        f.write(f"{str(id)}\n")
print(f"Results saved to: {results_file}")

# Create a new feature class with the non-contiguous farms (optional)
if noncontiguous_treefarm_ids:
    # Create SQL where clause for all non-contiguous IDs
    if field_type == 'String' or field_type == 'Text':
        # For string fields, properly format with quotes
        id_list = ", ".join(f"'{id}'" for id in noncontiguous_treefarm_ids)
        where_clause = f"{tf_id_field} IN ({id_list})"
    else:
        # For numeric fields
        id_list = ", ".join(str(id) for id in noncontiguous_treefarm_ids)
        where_clause = f"{tf_id_field} IN ({id_list})"

    print(f"Final where clause: {where_clause}")

    # Create a feature class of non-contiguous tree farms
    non_contiguous_fc = os.path.join(scratch_gdb, "NonContiguousFarms")
    if arcpy.Exists(non_contiguous_fc):
        arcpy.Delete_management(non_contiguous_fc)

    arcpy.MakeFeatureLayer_management(TreeFarm, "temp_nc_layer", where_clause)
    arcpy.CopyFeatures_management("temp_nc_layer", non_contiguous_fc)
    print(f"Created feature class '{non_contiguous_fc}' with all non-contiguous tree farms")

print("Done")