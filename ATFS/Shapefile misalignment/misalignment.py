import os
import fiona
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom

def inspect_shapefiles(root_dir):
    results = []

    for dirpath, _, filenames in os.walk(root_dir):
        for file in filenames:
            if file.lower().endswith(".shp"):
                filepath = os.path.join(dirpath, file)
                print(f"Inspecting: {filepath}")
                try:
                    with fiona.open(filepath, 'r') as src:
                        crs_wkt = src.crs_wkt or ""

                        # Check for legacy projection indicators in the WKT string
                        legacy_terms = ["Mercator_1SP", "Popular_Visualisation", "spherical"]
                        suspicious = any(term in crs_wkt for term in legacy_terms)

                        info = {
                            "path": filepath,
                            "crs": dict(src.crs) if src.crs else "Unknown",
                            "crs_wkt": crs_wkt[:300],
                            "geometry_type": src.schema["geometry"],
                            "properties": list(src.schema["properties"].keys()),
                            "feature_count": len(src),
                            "bounding_box": src.bounds,
                            "crs_suspicious": suspicious  # ✅ flag for reprojection issues
                        }

                        results.append(info)
                except Exception as e:
                    results.append({
                        "path": filepath,
                        "error": str(e)
                    })
    return results

def write_json(output_path, data):
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"✅ JSON written to {output_path}")

def write_pretty_xml(output_path, data):
    root = ET.Element("Shapefiles")

    for item in data:
        shp = ET.SubElement(root, "Shapefile")
        for key, value in item.items():
            child = ET.SubElement(shp, key)
            child.text = str(value)

    # Pretty print XML
    xml_str = ET.tostring(root, encoding='utf-8')
    parsed = minidom.parseString(xml_str)
    with open(output_path, "w", encoding='utf-8') as f:
        f.write(parsed.toprettyxml(indent="  "))
    print(f"✅ XML written to {output_path}")

# --- Entry point ---
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python inspect_shapefiles.py /path/to/folder output.{json|xml}")
    else:
        data = inspect_shapefiles(sys.argv[1])
        out_path = sys.argv[2]

        if out_path.endswith(".json"):
            write_json(out_path, data)
        elif out_path.endswith(".xml"):
            write_pretty_xml(out_path, data)
        else:
            print("❌ Unsupported output format. Please use .json or .xml.")
