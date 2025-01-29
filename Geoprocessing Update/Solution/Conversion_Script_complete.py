import sys
import zipfile
import os
import logging
import json
from os.path import join, splitext, basename, isdir
import fiona
from fiona.transform import transform_geom
import tempfile
from shapely.geometry import shape
import warnings
from fiona.errors import FionaDeprecationWarning  # Import the specific warning type

# Configure logging to suppress repeated warnings
logging.basicConfig(level=logging.INFO, format='[py] %(message)s')
logging.captureWarnings(True)

# Suppress specific warnings and ensure they are logged only once
warnings.filterwarnings("once", category=FionaDeprecationWarning)

# -----------------------------------
# PATH VARIABLES: Define your input and output paths here
# -----------------------------------
INPUT_PATH = "Data"  # Input directory or ZIP file
OUTPUT_DIR = "Output"  # Output directory
TARGET_CRS = 'EPSG:3857'  # Target CRS for reprojection (Web Mercator)


# -----------------------------------
# Utility Functions
# -----------------------------------

def logMessage(msg):
    """
    Logs messages for debugging.
    """
    logging.info(msg)


def is_valid_file(filename):
    """
    Checks if the file is valid for processing (excludes hidden files).
    """
    return not (filename.startswith("._") or filename == ".DS_Store")


def extract_files(input_path, temp_dir):
    """
    Extracts files if the input is a ZIP archive, or lists files in a directory.
    """
    if zipfile.is_zipfile(input_path):
        logMessage(f"Extracting ZIP archive: {input_path}")
        with zipfile.ZipFile(input_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
            return [join(temp_dir, name) for name in zip_ref.namelist() if is_valid_file(name)], temp_dir
    elif isdir(input_path):
        logMessage(f"Processing directory: {input_path}")
        file_list = []
        for root, _, files in os.walk(input_path):
            for file in files:
                if is_valid_file(file):
                    file_list.append(join(root, file))
        return file_list, input_path
    else:
        raise ValueError("Input must be a valid ZIP file or directory.")


def convert_to_arcgis_json(input_path, output_path, target_crs):
    """
    Converts a shapefile to ArcGIS JSON format after reprojecting.
    """
    try:
        logMessage(f"Converting shapefile to ArcGIS JSON: {input_path}")
        features = []

        with fiona.open(input_path, 'r') as source:
            source_crs = source.crs

            for feature in source:
                if feature['geometry']:  # Ensure geometry is not missing
                    transformed_geom = transform_geom(source_crs, target_crs, feature['geometry'])
                    geom_type = transformed_geom['type']

                    if geom_type == 'Point':
                        geometry = {"x": transformed_geom['coordinates'][0], "y": transformed_geom['coordinates'][1]}
                    elif geom_type == 'LineString':
                        geometry = {"paths": [transformed_geom['coordinates']]}
                    elif geom_type == 'Polygon':
                        geometry = {"rings": transformed_geom['coordinates']}
                    else:
                        geometry = None  # Unsupported geometry types

                    if geometry:
                        geometry["spatialReference"] = {"wkid": 3857}
                        features.append({
                            "geometry": geometry,
                            "attributes": dict(feature['properties'])
                        })

        with open(output_path, 'w') as json_file:
            json.dump(features, json_file, indent=4)

        logMessage(f"Converted and saved as ArcGIS JSON: {output_path}")
    except Exception as e:
        logMessage(f"Conversion error: {e}")


# -----------------------------------
# Main Execution Block
# -----------------------------------

if __name__ == '__main__':
    logMessage("Script started")
    try:
        # Create the output directory if it doesn't exist
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR)

        # Create a temporary directory for processing if needed
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract files or list directory contents
            file_list, working_dir = extract_files(INPUT_PATH, temp_dir)

            # Look for shapefiles in the list of files
            shapefiles = [f for f in file_list if splitext(f)[1].lower() == ".shp"]

            if not shapefiles:
                logMessage("No valid shapefiles found.")
                sys.exit(1)

            # Process each shapefile
            for shapefile in shapefiles:
                output_json = join(OUTPUT_DIR, f"reprojected_{basename(shapefile)}.json")
                convert_to_arcgis_json(shapefile, output_json, TARGET_CRS)

    except Exception as e:
        logMessage(f"Unexpected error: {e}")
    logMessage("Finished")
