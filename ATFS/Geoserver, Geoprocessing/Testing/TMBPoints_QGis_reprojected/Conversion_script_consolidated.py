import zipfile
import fiona
import json
import os
import tempfile
from fiona.transform import transform_geom

TARGET_CRS = 'EPSG:3857'

def extract_shapefiles(zip_path, temp_dir):
    """
    Extracts shapefiles from a ZIP archive.
    """
    extracted_files = []
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
        for name in zip_ref.namelist():
            extracted_path = os.path.join(temp_dir, name)
            if name.endswith('.shp'):
                extracted_files.append(extracted_path)
    return extracted_files

def convert_to_arcgis_json(input_shp):
    output_json = f"reprojected_{os.path.splitext(os.path.basename(input_shp))[0]}.json"
    features = []

    with fiona.open(input_shp, 'r') as source:
        source_crs = source.crs
        for feature in source:
            if feature['geometry']:
                transformed_geom = transform_geom(source_crs, TARGET_CRS, feature['geometry'])
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

    with open(output_json, 'w') as json_file:
        json.dump(features, json_file, indent=4)

    print(f"Saved: {output_json}")

# Process shapefiles or ZIP archives
for file in os.listdir():
    file_path = os.path.join(os.getcwd(), file)
    if file.endswith('.zip'):
        with tempfile.TemporaryDirectory() as temp_dir:
            shapefiles = extract_shapefiles(file_path, temp_dir)
            if not shapefiles:
                print(f"No shapefiles found in {file}")
            for shp in shapefiles:
                convert_to_arcgis_json(shp)
    elif file.endswith('.shp'):
        convert_to_arcgis_json(file_path)
