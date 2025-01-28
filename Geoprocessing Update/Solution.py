import sys
import zipfile
import os
import logging
from os.path import isdir, join, normpath, split
from pyproj import Transformer
import fiona
from fiona.transform import transform_geom

# Configure logging
logging.basicConfig(level=logging.INFO, format='[py] %(message)s')

def logMessage(msg):
    logging.info(msg)

def unzipfiles(path, zip):
    shapefileName = ''
    if not isdir(path):
        os.makedirs(path)

    for x in zip.namelist():
        logMessage(f"Extracting {os.path.basename(x)} ...")
        fileExt = os.path.splitext(x)[1].lower()
        if fileExt == ".shp":
            shapefileName = normpath(str(x))

        if not x.endswith('/'):
            root, name = split(x)
            directory = normpath(join(path, root))
            if not isdir(directory):
                os.makedirs(directory)
            with open(join(directory, name), 'wb') as f:
                f.write(zip.read(x))

    return shapefileName

def unzip(infile, outfol):
    try:
        with zipfile.ZipFile(infile, 'r') as zip:
            shapefileName = unzipfiles(outfol, zip)
        return shapefileName
    except Exception as e:
        logMessage(f"Error: {e}")
        return None

def project(input_path, output_path, target_crs):
    try:
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
    except Exception as e:
        logMessage(f"Projection error: {e}")
        return None

if __name__ == '__main__':
    logMessage("Script started")
    try:
        infile = "Archive.zip"  # Input ZIP file
        outdir = "Output"  # Output directory
        target_crs = 'EPSG:3857'  # Web Mercator

        if not infile or not outdir:
            logMessage("Usage: script.py <input_zip_file> <output_directory>")
            sys.exit(1)

        shapefileName = unzip(infile, outdir)
        if shapefileName:
            input_path = join(outdir, shapefileName)
            output_path = join(outdir, f"_{os.path.basename(shapefileName)}")
            project(input_path, output_path, target_crs)
            logMessage(f"Shapefile processed and saved to {output_path}")
        else:
            logMessage("No shapefile found.")
    except Exception as e:
        logMessage(f"Unexpected error: {e}")
    logMessage("Finished")
