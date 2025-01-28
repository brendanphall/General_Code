import zipfile
import os
import logging
from os.path import join, splitext, basename, isfile, isdir
import fiona
from fiona.transform import transform_geom
from pyproj import Transformer
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO, format='[py] %(message)s')

# -----------------------------------
# PATH VARIABLES: Define your input and output paths here
# -----------------------------------
INPUT_PATH = "TMBPoints_QGis_reprojected"           # Input directory or ZIP file
OUTPUT_DIR = "TMBPoints_QGis_reprojectedoutput"     # Output directory
TARGET_CRS = 'EPSG:3857'                            # Target CRS for reprojection (Web Mercator)

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

    Args:
        input_path (str): Path to the input (ZIP file or directory).
        temp_dir (str): Temporary directory for extraction (if ZIP file).

    Returns:
        list: List of valid files.
        str: Path to the working directory containing files.
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

def project(input_path, output_path, target_crs):
    """
    Reprojects a shapefile to the target CRS.

    Args:
        input_path (str): Path to the input shapefile.
        output_path (str): Path to save the reprojected shapefile.
        target_crs (str): Target CRS for reprojection.
    """
    try:
        logMessage(f"Reprojecting shapefile: {input_path}")
        with fiona.open(input_path, 'r') as source:
            source_crs = source.crs
            schema = source.schema

            with fiona.open(
                output_path, 'w',
                driver=source.driver,
                crs=target_crs,
                schema=schema
            ) as target:
                transformer = Transformer.from_crs(source_crs, target_crs, always_xy=True)
                for feature in source:
                    transformed_geom = transform_geom(
                        source_crs, target_crs, feature['geometry'], transformer=transformer
                    )
                    feature['geometry'] = transformed_geom
                    target.write(feature)
        logMessage(f"Reprojected shapefile saved to: {output_path}")
    except Exception as e:
        logMessage(f"Projection error: {e}")

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
                output_shapefile = join(OUTPUT_DIR, f"reprojected_{basename(shapefile)}")
                project(shapefile, output_shapefile, TARGET_CRS)

    except Exception as e:
        logMessage(f"Unexpected error: {e}")
    logMessage("Finished")
