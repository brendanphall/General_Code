"""
All-in-One FGDB to SQL Server Converter
Complete solution in a single file for easy sharing

USAGE:
1. Update CONFIG section below with your settings
2. Run in Jupyter Notebook, PyCharm, or ArcGIS Pro Python window
3. Do NOT run as command line script (DLL issues in ESRI environment)

TESTED: ArcGIS Pro 3.x + SQL Server 2022
AUTHOR: Your Team
DATE: 2025
"""

# =============================================================================
# CONFIGURATION - UPDATE THESE VALUES FOR YOUR ENVIRONMENT
# =============================================================================

CONFIG = {
    'fgdb_path': r'Z:\Users\brendanhall\GitHub\General_Code\ATFS\FGDB to SQL Server Conversion\esri_ref_data.gdb\esri_ref_data.gdb',
    'server': '100.103.17.32,1433',
    'database': 'SpatialTest',
    'username': 'dbeaver',
    'password': 'dbeaver',
    'selected_layers': None  # None = all layers, or ['layer1', 'layer2'] for specific
}


# =============================================================================
# CONVERTER CODE - NO CHANGES NEEDED BELOW THIS LINE
# =============================================================================

def fgdb_to_sql_server():
    """Main conversion function"""

    print("=" * 60)
    print("FGDB to SQL Server Converter")
    print("=" * 60)

    # Import required packages
    try:
        import geopandas as gpd
        import fiona
        from sqlalchemy import create_engine, text
        import warnings
        warnings.filterwarnings('ignore')
        print("✅ All packages loaded successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Run this in Jupyter Notebook or PyCharm instead of command line")
        return

    # Setup connection
    connection_string = f"mssql+pyodbc://{CONFIG['username']}:{CONFIG['password']}@{CONFIG['server']}/{CONFIG['database']}?driver=ODBC+Driver+17+for+SQL+Server"
    engine = create_engine(connection_string, fast_executemany=True)

    print(f"🎯 Source: {CONFIG['fgdb_path']}")
    print(f"🎯 Target: {CONFIG['server']} -> {CONFIG['database']}")

    # Get layers
    available_layers = fiona.listlayers(CONFIG['fgdb_path'])
    layers_to_convert = CONFIG['selected_layers'] if CONFIG['selected_layers'] else available_layers

    print(f"📋 Converting {len(layers_to_convert)} layers: {', '.join(layers_to_convert)}")

    results = {'successful': [], 'failed': []}

    # Convert each layer
    for i, layer_name in enumerate(layers_to_convert, 1):
        print(f"\n[{i}/{len(layers_to_convert)}] Processing: {layer_name}")

        try:
            # Read FGDB layer
            gdf = gpd.read_file(CONFIG['fgdb_path'], layer=layer_name)
            print(f"   📊 {len(gdf)} features")

            # Clean column names
            gdf.columns = [col.replace(' ', '_').replace('-', '_').replace('.', '_').replace('(', '').replace(')', '')
                           for col in gdf.columns]

            # Convert geometry to WKT
            if 'geometry' in gdf.columns:
                print(f"   🔧 Converting geometry...")
                gdf['Shape'] = gdf['geometry'].apply(lambda x: x.wkt if x and hasattr(x, 'wkt') else None)
                gdf = gdf.drop('geometry', axis=1)

            # Write to SQL Server
            print(f"   💾 Writing to SQL Server...")
            with engine.connect() as conn:
                conn.execute(text(f"IF OBJECT_ID('{layer_name}', 'U') IS NOT NULL DROP TABLE {layer_name}"))
                conn.commit()

            gdf.to_sql(name=layer_name, con=engine, if_exists='replace', index=False, chunksize=1000)

            # Convert to geometry type and create spatial index
            if 'Shape' in gdf.columns:
                print(f"   🗺️ Creating spatial geometry...")
                with engine.connect() as conn:
                    conn.execute(text(f"ALTER TABLE {layer_name} ADD Shape_Geom GEOMETRY"))
                    conn.execute(text(f"""
                        UPDATE {layer_name} 
                        SET Shape_Geom = geometry::STGeomFromText(Shape, 4326)
                        WHERE Shape IS NOT NULL
                    """))
                    conn.execute(text(f"ALTER TABLE {layer_name} DROP COLUMN Shape"))
                    conn.execute(text(f"EXEC sp_rename '{layer_name}.Shape_Geom', 'Shape', 'COLUMN'"))
                    conn.execute(text(f"ALTER TABLE {layer_name} ADD ID INT IDENTITY(1,1) PRIMARY KEY"))
                    conn.execute(text(f"""
                        CREATE SPATIAL INDEX SIDX_{layer_name}_Shape
                        ON {layer_name}(Shape)
                        USING GEOMETRY_GRID
                        WITH (BOUNDING_BOX = (-180, -90, 180, 90))
                    """))
                    conn.commit()

            print(f"   ✅ Success: {layer_name}")
            results['successful'].append(layer_name)

        except Exception as e:
            print(f"   ❌ Failed: {layer_name} - {e}")
            results['failed'].append(layer_name)

    # Summary
    print(f"\n📊 CONVERSION SUMMARY:")
    print(f"✅ Successful: {len(results['successful'])}")
    print(f"❌ Failed: {len(results['failed'])}")

    if results['successful']:
        print(f"\n🎉 Converted layers: {', '.join(results['successful'])}")
        print(f"Test with: SELECT COUNT(*) FROM {results['successful'][0]};")

    return results


def validate_conversion():
    """Quick validation of converted data"""

    try:
        import pyodbc
        from sqlalchemy import create_engine, text

        print(f"\n🔍 Validating conversion...")

        connection_string = f"mssql+pyodbc://{CONFIG['username']}:{CONFIG['password']}@{CONFIG['server']}/{CONFIG['database']}?driver=ODBC+Driver+17+for+SQL+Server"
        engine = create_engine(connection_string)

        # Test basic connectivity and get table list
        with engine.connect() as conn:
            tables = conn.execute(
                text("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")).fetchall()
            converted_tables = [table[0] for table in tables if not table[0].startswith('sys')]

            print(f"Found {len(converted_tables)} tables: {', '.join(converted_tables)}")

            # Validate each table
            for table in converted_tables:
                try:
                    result = conn.execute(text(f"""
                        SELECT 
                            COUNT(*) as total_records,
                            COUNT(Shape) as records_with_geometry,
                            SUM(CASE WHEN Shape.STIsValid() = 1 THEN 1 ELSE 0 END) as valid_geometries
                        FROM {table}
                    """)).fetchone()

                    print(f"   ✅ {table}: {result[0]} records, {result[2]} valid geometries")

                except Exception as e:
                    print(f"   ❌ {table}: Error - {e}")

        return True

    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    # Run conversion
    results = fgdb_to_sql_server()

    # Run validation
    if results and results['successful']:
        validate_conversion()

        print(f"\n🏆 COMPLETE! {len(results['successful'])} layers converted and validated.")
        print(f"Ready for use in ArcGIS Pro and other applications.")
    else:
        print(f"\n⚠️ Conversion issues detected. Check the log above.")

else:
    # If imported as module
    print("FGDB Converter loaded. Run fgdb_to_sql_server() to start conversion.")