import fiona
import json
import os
from fiona.transform import transform_geom

TARGET_CRS = 'EPSG:3857'


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


for file in os.listdir():
    if file.endswith('.shp'):
        convert_to_arcgis_json(file)