"""
FGDB to SQL Server Converter - FIXED VERSION
Complete conversion script for ESRI File Geodatabase to SQL Server
"""

import geopandas as gpd
import fiona
import pyodbc
from sqlalchemy import create_engine, text
import pandas as pd
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURATION - UPDATE THESE VALUES
# =============================================================================

CONFIG = {
    'server': '100.103.17.32,1433',
    'database': 'SpatialTest',
    'username': 'dbeaver',
    'password': 'dbeaver',
    'fgdb_path': r'Z:\Users\brendanhall\GitHub\General_Code\ATFS\FGDB to SQL Server Conversion\esri_ref_data.gdb\esri_ref_data.gdb',
    'chunk_size': 1000,
    'selected_layers': None  # None = all layers, or ['layer1', 'layer2'] for specific layers
}

class FGDBConverter:
    def __init__(self, config):
        self.config = config
        self.engine = None

    def log(self, message, level="INFO"):
        """Simple logging function"""
        print(f"[{level}] {message}")

    def setup_connection(self):
        """Create SQL Server connection"""
        self.log("Setting up SQL Server connection...")

        try:
            connection_string = (
                f"mssql+pyodbc://{self.config['username']}:{self.config['password']}"
                f"@{self.config['server']}/{self.config['database']}"
                f"?driver=ODBC+Driver+17+for+SQL+Server"
            )

            self.engine = create_engine(
                connection_string,
                fast_executemany=True,
                pool_pre_ping=True
            )

            # Test connection
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT @@VERSION, DB_NAME()"))
                version, db_name = result.fetchone()
                self.log(f"✅ Connected to SQL Server")
                self.log(f"   Database: {db_name}")
                self.log(f"   Version: {version[:50]}...")

            return True

        except Exception as e:
            self.log(f"❌ Connection failed: {e}", "ERROR")
            return False

    def get_fgdb_layers(self):
        """Get list of layers in FGDB"""
        self.log(f"Reading FGDB: {self.config['fgdb_path']}")

        if not os.path.exists(self.config['fgdb_path']):
            self.log(f"❌ FGDB not found: {self.config['fgdb_path']}", "ERROR")
            return []

        try:
            layers = fiona.listlayers(self.config['fgdb_path'])
            self.log(f"✅ Found {len(layers)} layers: {', '.join(layers)}")
            return layers

        except Exception as e:
            self.log(f"❌ Error reading FGDB: {e}", "ERROR")
            return []

    def clean_column_names(self, columns):
        """Clean column names for SQL Server compatibility"""
        cleaned = []
        for col in columns:
            # Replace problematic characters
            clean_col = col.replace(' ', '_').replace('-', '_').replace('.', '_')
            clean_col = clean_col.replace('(', '').replace(')', '')
            clean_col = clean_col.replace('#', 'num').replace('%', 'pct')
            clean_col = clean_col.replace('/', '_').replace('\\', '_')

            # Ensure starts with letter
            if clean_col and clean_col[0].isdigit():
                clean_col = f"col_{clean_col}"

            # Limit length
            if len(clean_col) > 50:
                clean_col = clean_col[:50]

            # Handle empty names
            if not clean_col:
                clean_col = f"col_{len(cleaned)}"

            cleaned.append(clean_col)

        return cleaned

    def convert_layer(self, layer_name):
        """FIXED: Simplified conversion that lets pandas handle data types"""
        self.log(f"\n🔄 Converting layer: {layer_name}")

        try:
            # Read the data
            gdf = gpd.read_file(self.config['fgdb_path'], layer=layer_name)

            if len(gdf) == 0:
                self.log(f"   ⚠️ Layer is empty, skipping")
                return True

            self.log(f"   📊 Processing {len(gdf)} features")

            # Show geometry info
            if 'geometry' in gdf.columns and len(gdf) > 0:
                geom_types = gdf.geometry.geom_type.value_counts()
                self.log(f"   🗺️ Geometry types: {dict(geom_types)}")

            # Clean column names
            original_columns = list(gdf.columns)
            cleaned_columns = self.clean_column_names(original_columns)
            column_mapping = dict(zip(original_columns, cleaned_columns))

            # Handle duplicate column names
            if len(set(cleaned_columns)) != len(cleaned_columns):
                self.log(f"   ⚠️ Warning: Duplicate column names after cleaning", "WARN")
                seen = set()
                unique_cleaned = []
                for col in cleaned_columns:
                    if col in seen:
                        counter = 1
                        new_col = f"{col}_{counter}"
                        while new_col in seen:
                            counter += 1
                            new_col = f"{col}_{counter}"
                        unique_cleaned.append(new_col)
                        seen.add(new_col)
                    else:
                        unique_cleaned.append(col)
                        seen.add(col)
                cleaned_columns = unique_cleaned
                column_mapping = dict(zip(original_columns, cleaned_columns))

            gdf = gdf.rename(columns=column_mapping)

            # Handle geometry
            has_geometry = False
            if 'geometry' in gdf.columns:
                self.log(f"   🔧 Converting geometry to WKT...")

                def safe_wkt(geom):
                    try:
                        if geom is None or geom.is_empty:
                            return None
                        if not geom.is_valid:
                            geom = geom.buffer(0)  # Try to fix invalid geometry
                        return geom.wkt
                    except:
                        return None

                gdf['Shape'] = gdf['geometry'].apply(safe_wkt)
                gdf = gdf.drop('geometry', axis=1)
                has_geometry = True

                valid_geoms = gdf['Shape'].notna().sum()
                self.log(f"   ✅ Converted {valid_geoms}/{len(gdf)} geometries to WKT")

            # Drop existing table
            self.log(f"   🗑️ Dropping existing table if exists...")
            with self.engine.connect() as conn:
                conn.execute(text(f"IF OBJECT_ID('{layer_name}', 'U') IS NOT NULL DROP TABLE {layer_name}"))
                conn.commit()

            # Write without specifying dtypes - let pandas decide
            self.log(f"   💾 Writing {len(gdf)} records to SQL Server...")
            gdf.to_sql(
                name=layer_name,
                con=self.engine,
                if_exists='replace',
                index=False,
                chunksize=self.config['chunk_size']
                # No dtype parameter - let pandas auto-detect
            )

            # Fix geometry column type manually if we have geometry
            if has_geometry:
                self.log(f"   🔧 Converting Shape column to GEOMETRY type...")
                try:
                    with self.engine.connect() as conn:
                        # Add a new geometry column
                        conn.execute(text(f"ALTER TABLE {layer_name} ADD Shape_Geom GEOMETRY"))

                        # Update with geometry data
                        conn.execute(text(f"""
                            UPDATE {layer_name}
                            SET Shape_Geom = geometry::STGeomFromText(Shape, 4326)
                            WHERE Shape IS NOT NULL AND Shape != ''
                        """))

                        # Drop old text column and rename
                        conn.execute(text(f"ALTER TABLE {layer_name} DROP COLUMN Shape"))
                        conn.execute(text(f"EXEC sp_rename '{layer_name}.Shape_Geom', 'Shape', 'COLUMN'"))
                        conn.commit()

                        # Create spatial index
                        self.log(f"   🗂️ Creating spatial index...")
                        spatial_index_sql = f"""
                        CREATE SPATIAL INDEX SIDX_{layer_name}_Shape
                        ON {layer_name}(Shape)
                        USING GEOMETRY_GRID
                        WITH (BOUNDING_BOX = (-180, -90, 180, 90))
                        """
                        conn.execute(text(spatial_index_sql))
                        conn.commit()
                        self.log(f"   ✅ Spatial index created")

                except Exception as e:
                    self.log(f"   ⚠️ Warning: Could not create geometry column or spatial index: {e}", "WARN")

            # Show column mapping changes
            changed_cols = [(orig, new) for orig, new in column_mapping.items()
                           if orig != new and orig != 'geometry']
            if changed_cols:
                self.log(f"   📝 Column name changes:")
                for orig, new in changed_cols[:5]:  # Show first 5
                    self.log(f"      {orig} → {new}")
                if len(changed_cols) > 5:
                    self.log(f"      ... and {len(changed_cols) - 5} more")

            self.log(f"   ✅ Successfully converted {layer_name}")
            return True

        except Exception as e:
            self.log(f"   ❌ Error converting {layer_name}: {e}", "ERROR")
            import traceback
            self.log(f"   Details: {traceback.format_exc()}", "ERROR")
            return False

    def run_conversion(self):
        """Main conversion process"""
        self.log("🚀 Starting FGDB to SQL Server conversion")
        self.log(f"📁 Source: {self.config['fgdb_path']}")
        self.log(f"🎯 Target: {self.config['server']} -> {self.config['database']}")

        # Setup connection
        if not self.setup_connection():
            return False

        # Get layers
        available_layers = self.get_fgdb_layers()
        if not available_layers:
            return False

        # Determine which layers to convert
        if self.config['selected_layers']:
            layers_to_convert = [l for l in self.config['selected_layers'] if l in available_layers]
            missing_layers = [l for l in self.config['selected_layers'] if l not in available_layers]
            if missing_layers:
                self.log(f"⚠️ Selected layers not found: {missing_layers}", "WARN")
        else:
            layers_to_convert = available_layers

        self.log(f"📋 Converting {len(layers_to_convert)} layers: {', '.join(layers_to_convert)}")

        # Convert each layer
        successful = 0
        failed = 0

        for i, layer in enumerate(layers_to_convert, 1):
            self.log(f"\n[{i}/{len(layers_to_convert)}] Processing: {layer}")

            if self.convert_layer(layer):
                successful += 1
            else:
                failed += 1

        # Final summary
        self.log(f"\n" + "="*60)
        self.log(f"📊 CONVERSION SUMMARY")
        self.log(f"="*60)
        self.log(f"✅ Successful: {successful}")
        self.log(f"❌ Failed: {failed}")
        self.log(f"📋 Total: {len(layers_to_convert)}")

        if successful > 0:
            self.log(f"\n🎉 Conversion completed!")
            self.log(f"🔍 Test your data with these SQL queries:")
            self.log(f"   SELECT COUNT(*) FROM {layers_to_convert[0]};")
            self.log(f"   SELECT TOP 5 * FROM {layers_to_convert[0]};")
            self.log(f"   SELECT TOP 5 *, Shape.STAsText() AS WKT FROM {layers_to_convert[0]};")

        return failed == 0

def main():
    """Main function"""
    print("="*60)
    print("    FGDB to SQL Server Converter - FIXED VERSION")
    print("="*60)

    # Show configuration
    print(f"📋 Configuration:")
    print(f"   Server: {CONFIG['server']}")
    print(f"   Database: {CONFIG['database']}")
    print(f"   Username: {CONFIG['username']}")
    print(f"   FGDB: {CONFIG['fgdb_path']}")
    print(f"   Chunk size: {CONFIG['chunk_size']}")
    print(f"   Selected layers: {CONFIG['selected_layers'] or 'All layers'}")
    print()

    # Validate FGDB path
    if not os.path.exists(CONFIG['fgdb_path']):
        print(f"❌ FGDB not found: {CONFIG['fgdb_path']}")
        print(f"💡 Please update CONFIG['fgdb_path'] to the correct location")
        return

    # Create converter and run
    converter = FGDBConverter(CONFIG)
    success = converter.run_conversion()

    if success:
        print(f"\n🏆 All conversions completed successfully!")
    else:
        print(f"\n⚠️ Some conversions failed. Check the log output above.")

if __name__ == "__main__":
    main()