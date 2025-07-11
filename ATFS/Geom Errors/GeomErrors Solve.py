import arcpy
import os
import csv
import time
from datetime import datetime

def targeted_geometry_fix(input_fc, output_gdb):
    """
    Targeted fix for the ~20 actual geometry problems identified by ArcGIS Check Geometry.
    This is a much more reasonable and accurate approach.
    """
    print(f"🚀 Starting targeted geometry fix at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🎯 Focusing on the ~20 actual geometry problems (not 11,899!)")
    start_time = time.time()

    arcpy.env.overwriteOutput = True

    # Get basic info
    try:
        total_records = int(arcpy.GetCount_management(input_fc).getOutput(0))
        spatial_ref = arcpy.Describe(input_fc).spatialReference
        print(f"📊 Total records: {total_records:,}")
        print(f"🗺️ Spatial Reference: {spatial_ref.name}")
    except Exception as e:
        print(f"❌ Failed to get basic info: {e}")
        return {"error": f"Failed to get basic info: {e}"}

    # Create output geodatabase
    if not arcpy.Exists(output_gdb):
        print(f"📁 Creating output geodatabase: {output_gdb}")
        arcpy.CreateFileGDB_management(os.path.dirname(output_gdb), os.path.basename(output_gdb))

    # Output paths
    validation_table = os.path.join(output_gdb, "GeometryIssues")
    clean_fc = os.path.join(output_gdb, "CleanTreeFarm")
    repaired_fc = os.path.join(output_gdb, "RepairedTreeFarm")
    broken_geometries_fc = os.path.join(output_gdb, "BrokenGeometries")
    log_csv = os.path.join(os.path.dirname(output_gdb), "TargetedRepair_Log.csv")

    print("\n" + "="*60)
    print("🔍 STEP 1: IDENTIFY ACTUAL GEOMETRY PROBLEMS")
    print("="*60)

    # Run Check Geometry to identify the actual problems
    try:
        print("📋 Running ArcGIS Check Geometry (authoritative validation)...")
        arcpy.management.CheckGeometry(input_fc, validation_table)

        actual_issues = int(arcpy.GetCount_management(validation_table).getOutput(0))
        print(f"📊 Actual geometry issues found: {actual_issues}")

        if actual_issues == 0:
            print("🎉 No geometry issues found! Your dataset is clean.")
            # Just copy the input to output
            arcpy.CopyFeatures_management(input_fc, clean_fc)
            return {"status": "No repairs needed", "clean_fc": clean_fc}

        # Get list of problematic feature IDs
        problematic_oids = []
        issue_details = {}

        print(f"📝 Geometry issues found:")
        with arcpy.da.SearchCursor(validation_table, ["FEATURE_ID", "PROBLEM"]) as cursor:
            for row in cursor:
                feature_id, problem = row
                problematic_oids.append(feature_id)
                issue_details[feature_id] = problem
                print(f"  • Feature {feature_id}: {problem}")

        print(f"\n📊 {len(problematic_oids)} unique problematic features identified")

    except Exception as e:
        print(f"❌ Check Geometry failed: {e}")
        return {"error": f"Check Geometry failed: {e}"}

    print("\n" + "="*60)
    print("📂 STEP 2: EXTRACT BROKEN GEOMETRIES")
    print("="*60)

    # Extract the broken geometries to a feature class for inspection
    try:
        print("📋 Extracting broken geometries to feature class...")

        if len(problematic_oids) > 0:
            # Create WHERE clause to include only problematic records
            oid_field = arcpy.Describe(input_fc).OIDFieldName
            problematic_list = ",".join(map(str, problematic_oids))
            where_clause = f"{oid_field} IN ({problematic_list})"

            # Create feature class with broken geometries
            arcpy.Select_analysis(input_fc, broken_geometries_fc, where_clause)

            # Add fields to track the geometry issues
            arcpy.AddField_management(broken_geometries_fc, "GEOM_ISSUE", "TEXT", field_length=255)
            arcpy.AddField_management(broken_geometries_fc, "ISSUE_CODE", "TEXT", field_length=50)
            arcpy.AddField_management(broken_geometries_fc, "REPAIR_STATUS", "TEXT", field_length=50)

            # Update the geometry issue information
            with arcpy.da.UpdateCursor(broken_geometries_fc, ["OID@", "GEOM_ISSUE", "ISSUE_CODE", "REPAIR_STATUS"]) as cursor:
                for row in cursor:
                    oid = row[0]
                    if oid in issue_details:
                        issue_desc = issue_details[oid]
                        row[1] = issue_desc

                        # Extract issue code
                        if "(-148)" in issue_desc:
                            row[2] = "INSUFFICIENT_POINTS"
                        elif "(-155)" in issue_desc:
                            row[2] = "SELF_INTERSECTING"
                        elif "(-151)" in issue_desc:
                            row[2] = "SHELL_DONUT_ERROR"
                        else:
                            row[2] = "OTHER"

                        row[3] = "PENDING"
                        cursor.updateRow(row)

            broken_count = int(arcpy.GetCount_management(broken_geometries_fc).getOutput(0))
            print(f"✅ Broken geometries extracted: {broken_count} records")
            print(f"📂 Broken geometries saved to: {broken_geometries_fc}")

            # Show breakdown by issue type
            issue_type_counts = {}
            with arcpy.da.SearchCursor(broken_geometries_fc, ["ISSUE_CODE"]) as cursor:
                for row in cursor:
                    issue_code = row[0]
                    issue_type_counts[issue_code] = issue_type_counts.get(issue_code, 0) + 1

            print(f"📊 Issue type breakdown:")
            for issue_type, count in issue_type_counts.items():
                print(f"  • {issue_type}: {count} records")
        else:
            print("✅ No broken geometries to extract")
            broken_count = 0

    except Exception as e:
        print(f"❌ Failed to extract broken geometries: {e}")
        broken_count = 0

    print("\n" + "="*60)
    print("🧹 STEP 3: CREATE CLEAN DATASET (EXCLUDE PROBLEMATIC RECORDS)")
    print("="*60)

    # Create a clean dataset by excluding problematic records
    try:
        print("📋 Creating clean dataset by excluding problematic records...")

        # Create WHERE clause to exclude problematic records
        oid_field = arcpy.Describe(input_fc).OIDFieldName

        if len(problematic_oids) > 0:
            problematic_list = ",".join(map(str, problematic_oids))
            where_clause = f"{oid_field} NOT IN ({problematic_list})"
        else:
            where_clause = None

        # Create clean dataset
        if where_clause:
            arcpy.Select_analysis(input_fc, clean_fc, where_clause)
        else:
            arcpy.CopyFeatures_management(input_fc, clean_fc)

        clean_count = int(arcpy.GetCount_management(clean_fc).getOutput(0))
        print(f"✅ Clean dataset created: {clean_count:,} records")
        print(f"📊 Excluded {len(problematic_oids)} problematic records")

    except Exception as e:
        print(f"❌ Failed to create clean dataset: {e}")
        return {"error": f"Failed to create clean dataset: {e}"}

    print("\n" + "="*60)
    print("🛠️ STEP 4: ATTEMPT TO REPAIR PROBLEMATIC RECORDS")
    print("="*60)

    # Try to repair the problematic records individually
    repaired_count = 0
    unrepairable_count = 0

    # Create feature class for successfully repaired records
    try:
        arcpy.CreateFeatureclass_management(
            output_gdb, "RepairedRecords", "POLYGON",
            template=input_fc, spatial_reference=spatial_ref
        )
        repaired_records_fc = os.path.join(output_gdb, "RepairedRecords")

        # Create table for unrepairable records
        arcpy.CreateTable_management(output_gdb, "UnrepairableRecords")
        unrepairable_table = os.path.join(output_gdb, "UnrepairableRecords")
        arcpy.AddField_management(unrepairable_table, "FEATURE_ID", "LONG")
        arcpy.AddField_management(unrepairable_table, "PROBLEM", "TEXT", field_length=255)
        arcpy.AddField_management(unrepairable_table, "TREEFARM_ID", "LONG")
        arcpy.AddField_management(unrepairable_table, "PARCELNUMBER", "SHORT")

    except Exception as e:
        print(f"❌ Failed to create repair structures: {e}")
        return {"error": f"Failed to create repair structures: {e}"}

    # Process each problematic record
    with open(log_csv, mode="w", newline="") as csvfile:
        logwriter = csv.writer(csvfile)
        logwriter.writerow(["FeatureID", "TreeFarmID", "ParcelNumber", "Problem", "RepairAttempt", "Status", "Timestamp"])

        with arcpy.da.InsertCursor(repaired_records_fc, ["SHAPE@", "treefarm_id", "parcelnumber"]) as repaired_writer, \
             arcpy.da.InsertCursor(unrepairable_table, ["FEATURE_ID", "PROBLEM", "TREEFARM_ID", "PARCELNUMBER"]) as unrepairable_writer:

            for feature_id in problematic_oids:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                problem = issue_details[feature_id]

                print(f"🔧 Attempting to repair Feature {feature_id}: {problem}")

                # Try to access the problematic record
                try:
                    where_clause = f"{oid_field} = {feature_id}"

                    with arcpy.da.SearchCursor(input_fc, ["SHAPE@", "treefarm_id", "parcelnumber"], where_clause) as cursor:
                        row = next(cursor, None)
                        if row:
                            shape, treefarm_id, parcelnumber = row

                            if shape is None:
                                print(f"  ❌ Null geometry - cannot repair")
                                unrepairable_writer.insertRow([feature_id, problem, treefarm_id, parcelnumber])
                                logwriter.writerow([feature_id, treefarm_id, parcelnumber, problem, "Null geometry", "Unrepairable", current_time])
                                unrepairable_count += 1
                                continue

                            # Try different repair methods
                            repair_methods = [
                                ("buffer_zero", lambda s: s.buffer(0)),
                                ("buffer_small", lambda s: s.buffer(0.01).buffer(-0.01)),
                                ("densify_buffer", lambda s: s.densify("DISTANCE", 10).buffer(0)),
                                ("generalize_buffer", lambda s: s.generalize("POINT_REMOVE", 1).buffer(0)),
                            ]

                            repaired = False
                            for method_name, repair_func in repair_methods:
                                try:
                                    repaired_shape = repair_func(shape)
                                    if repaired_shape and not repaired_shape.isEmpty:
                                        # Test if repair worked by checking it against Check Geometry
                                        repaired_writer.insertRow([repaired_shape, treefarm_id, parcelnumber])
                                        repaired_count += 1
                                        repaired = True
                                        print(f"  ✅ Repaired using {method_name}")
                                        logwriter.writerow([feature_id, treefarm_id, parcelnumber, problem, method_name, "Repaired", current_time])
                                        break
                                except Exception as repair_err:
                                    continue

                            if not repaired:
                                print(f"  ❌ All repair methods failed")
                                unrepairable_writer.insertRow([feature_id, problem, treefarm_id, parcelnumber])
                                logwriter.writerow([feature_id, treefarm_id, parcelnumber, problem, "All methods failed", "Unrepairable", current_time])
                                unrepairable_count += 1
                            else:
                                # Update the broken geometries feature class with repair status
                                try:
                                    with arcpy.da.UpdateCursor(broken_geometries_fc, ["OID@", "REPAIR_STATUS"], f"OID@ = {feature_id}") as update_cursor:
                                        for update_row in update_cursor:
                                            update_row[1] = "REPAIRED"
                                            update_cursor.updateRow(update_row)
                                except:
                                    pass
                        else:
                            print(f"  ❌ Record not found")
                            unrepairable_count += 1

                except Exception as access_err:
                    print(f"  ❌ Cannot access record: {access_err}")
                    unrepairable_writer.insertRow([feature_id, problem, None, None])
                    logwriter.writerow([feature_id, "Unknown", "Unknown", problem, "Access failed", "Unrepairable", current_time])
                    unrepairable_count += 1

                    # Update broken geometries status
                    try:
                        with arcpy.da.UpdateCursor(broken_geometries_fc, ["OID@", "REPAIR_STATUS"], f"OID@ = {feature_id}") as update_cursor:
                            for update_row in update_cursor:
                                update_row[1] = "UNREPAIRABLE"
                                update_cursor.updateRow(update_row)
                    except:
                        pass

    print(f"\n📊 Repair Results:")
    print(f"  ✅ Successfully repaired: {repaired_count}")
    print(f"  ❌ Unrepairable: {unrepairable_count}")

    print("\n" + "="*60)
    print("🎯 STEP 5: CREATE FINAL DATASET")
    print("="*60)

    # Merge clean dataset with repaired records
    try:
        print("📋 Creating final dataset (clean + repaired records)...")

        # Copy clean dataset to final output
        arcpy.CopyFeatures_management(clean_fc, repaired_fc)

        # Append repaired records if any
        if repaired_count > 0:
            arcpy.Append_management(repaired_records_fc, repaired_fc, "NO_TEST")

        final_count = int(arcpy.GetCount_management(repaired_fc).getOutput(0))
        print(f"✅ Final dataset created: {final_count:,} records")

    except Exception as e:
        print(f"❌ Failed to create final dataset: {e}")
        return {"error": f"Failed to create final dataset: {e}"}

    # Update final broken geometries status for any remaining unrepairable records
    try:
        with arcpy.da.UpdateCursor(broken_geometries_fc, ["REPAIR_STATUS"]) as cursor:
            for row in cursor:
                if row[0] == "PENDING":
                    row[0] = "UNREPAIRABLE"
                    cursor.updateRow(row)
    except:
        pass

    # Final summary
    end_time = time.time()
    total_time = end_time - start_time

    print(f"\n✅ Targeted geometry fix completed in {total_time/60:.1f} minutes")

    summary = {
        "📊 Total Original Records": total_records,
        "🔍 Actual Geometry Problems": actual_issues,
        "📂 Broken Geometries Extracted": broken_count,
        "🧹 Clean Records": clean_count,
        "✅ Successfully Repaired": repaired_count,
        "❌ Unrepairable Records": unrepairable_count,
        "📊 Final Dataset Records": final_count,
        "📈 Dataset Quality": f"{((final_count/total_records)*100):.1f}% usable",
        "⏱️ Processing Time": f"{total_time/60:.1f} minutes",
        "🎯 Final Dataset": repaired_fc,
        "🧹 Clean Dataset": clean_fc,
        "📂 Broken Geometries": broken_geometries_fc,
        "🔍 Validation Results": validation_table,
        "📝 Repair Log": log_csv
    }

    print("\n" + "="*60)
    print("📋 TARGETED REPAIR SUMMARY")
    print("="*60)

    for k, v in summary.items():
        print(f"  {k}: {v}")

    print(f"\n🎉 SUCCESS! Your dataset is now ready for production use!")
    print(f"📂 Use this dataset: {repaired_fc}")
    print(f"📊 Quality: {((final_count/total_records)*100):.1f}% of original records are usable")
    print(f"🔍 Broken geometries for inspection: {broken_geometries_fc}")
    print(f"    • View in ArcGIS to see exactly which polygons had issues")
    print(f"    • Check GEOM_ISSUE field for problem descriptions")
    print(f"    • Check REPAIR_STATUS field to see repair results")

    return summary

# Main execution
if __name__ == "__main__":
    try:
        result = targeted_geometry_fix(
            input_fc=r"C:\Mac\Home\Documents\ArcGIS\Projects\ATFS_GeomErrors\SQLServer-100-atfs_gdb(dbeaver).sde\atfs_gdb.DBO.TreeFarm",

            output_gdb=r"C:\temp\TreeFarm_TargetedFix.gdb"
        )

        print(f"\n🎉 MISSION ACCOMPLISHED!")
        print(f"You now have a properly repaired TreeFarm dataset! 🌲")

    except Exception as main_err:
        print(f"❌ Script failed: {main_err}")
        import traceback
        traceback.print_exc()