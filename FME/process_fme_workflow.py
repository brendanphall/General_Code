import re
import os
from collections import defaultdict

def parse_fme_workflow(content):
    """
    Parse an FME workflow file and extract key components and their interactions.

    Args:
        content (str): The content of the FME workflow file

    Returns:
        dict: A structured representation of the workflow
    """
    workflow = {
        "metadata": {},
        "datasets": [],
        "transformers": [],
        "connections": [],
        "feature_types": [],
        "parameters": []
    }

    # Extract metadata
    metadata_pattern = r'#!\\s+(\\w+)\\s+\"([^\"]*)\"'
    metadata_matches = re.finditer(metadata_pattern, content)
    for match in metadata_matches:
        key, value = match.groups()
        workflow["metadata"][key] = value

    # Extract datasets (readers and writers)
    dataset_pattern = r'<DATASET\\s+IS_SOURCE=\"([^\"]+)\"\\s+ROLE=\"([^\"]+)\"\\s+FORMAT=\"([^\"]+)\"\\s+DATASET=\"([^\"]+)\"\\s+KEYWORD=\"([^\"]+)\"'
    dataset_matches = re.finditer(dataset_pattern, content)
    for match in dataset_matches:
        is_source, role, format_type, dataset, keyword = match.groups()
        workflow["datasets"].append({
            "is_source": is_source.lower() == "true",
            "role": role,
            "format": format_type,
            "dataset": dataset,
            "keyword": keyword
        })

    # Extract transformers
    transformer_pattern = r'<TRANSFORMER\\s+IDENTIFIER=\"([^\"]+)\"\\s+TYPE=\"([^\"]+)\"\\s+VERSION=\"([^\"]+)\"\\s+POSITION=\"([^\"]+)\"'
    transformer_matches = re.finditer(transformer_pattern, content)
    for match in transformer_matches:
        identifier, transformer_type, version, position = match.groups()

        # Extract parameters for this transformer
        params = {}
        param_pattern = r'<XFORM_PARM PARM_NAME=\"([^\"]+)\" PARM_VALUE=\"([^\"]*)\"'
        param_section = re.search(rf'<TRANSFORMER[^>]+IDENTIFIER=\"{identifier}\".*?</TRANSFORMER>', content, re.DOTALL)
        if param_section:
            param_matches = re.finditer(param_pattern, param_section.group(0))
            for param_match in param_matches:
                param_name, param_value = param_match.groups()
                params[param_name] = param_value

        # Extract attributes for this transformer
        attributes = []
        attr_pattern = r'<XFORM_ATTR ATTR_NAME=\"([^\"]+)\" IS_USER_CREATED=\"([^\"]+)\" FEAT_INDEX=\"([^\"]+)\"'
        if param_section:
            attr_matches = re.finditer(attr_pattern, param_section.group(0))
            for attr_match in attr_matches:
                attr_name, is_user_created, feat_index = attr_match.groups()
                attributes.append({
                    "name": attr_name,
                    "is_user_created": is_user_created.lower() == "true",
                    "feat_index": feat_index
                })

        workflow["transformers"].append({
            "identifier": identifier,
            "type": transformer_type,
            "version": version,
            "position": position,
            "parameters": params,
            "attributes": attributes
        })

    # Extract connections between components
    connection_pattern = r'<FEAT_LINK\\s+IDENTIFIER=\"([^\"]+)\"\\s+SOURCE_NODE=\"([^\"]+)\"\\s+TARGET_NODE=\"([^\"]+)\"\\s+SOURCE_PORT_DESC=\"([^\"]*)\"\\s+TARGET_PORT_DESC=\"([^\"]*)\"'
    connection_matches = re.finditer(connection_pattern, content)
    for match in connection_matches:
        identifier, source_node, target_node, source_port, target_port = match.groups()
        workflow["connections"].append({
            "identifier": identifier,
            "source_node": source_node,
            "target_node": target_node,
            "source_port": source_port,
            "target_port": target_port
        })

    # Extract feature types
    feature_type_pattern = r'<FEATURE_TYPE\\s+IS_SOURCE=\"([^\"]+)\"\\s+NODE_NAME=\"([^\"]+)\"\\s+FEATURE_TYPE_NAME=\"([^\"]*)\"\\s+FEATURE_TYPE_NAME_QUALIFIER=\"([^\"]*)\"'
    feature_type_matches = re.finditer(feature_type_pattern, content)
    for match in feature_type_matches:
        is_source, node_name, feature_type_name, qualifier = match.groups()

        # Extract attributes for this feature type
        attributes = []
        attr_section = re.search(rf'<FEATURE_TYPE[^>]+NODE_NAME=\"{node_name}\".*?</FEATURE_TYPE>', content, re.DOTALL)
        if attr_section:
            attr_pattern = r'<FEAT_ATTRIBUTE ATTR_NAME=\"([^\"]+)\" ATTR_TYPE=\"([^\"]+)\" ATTR_HAS_PORT=\"([^\"]+)\"'
            attr_matches = re.finditer(attr_pattern, attr_section.group(0))
            for attr_match in attr_matches:
                attr_name, attr_type, has_port = attr_match.groups()
                attributes.append({
                    "name": attr_name,
                    "type": attr_type,
                    "has_port": has_port.lower() == "true"
                })

        workflow["feature_types"].append({
            "is_source": is_source.lower() == "true",
            "node_name": node_name,
            "feature_type_name": feature_type_name,
            "qualifier": qualifier,
            "attributes": attributes
        })

    # Extract global parameters
    param_pattern = r'<GLOBAL_PARAMETER\\s+GUI_LINE=\"([^\"]*)\"\\s+DEFAULT_VALUE=\"([^\"]*)\"\\s+IS_STAND_ALONE=\"([^\"]*)\"'
    param_matches = re.finditer(param_pattern, content)
    for match in param_matches:
        gui_line, default_value, is_standalone = match.groups()
        workflow["parameters"].append({
            "gui_line": gui_line,
            "default_value": default_value,
            "is_standalone": is_standalone.lower() == "true"
        })

    return workflow

def generate_documentation(workflow):
    """
    Generate documentation from a parsed FME workflow.

    Args:
        workflow (dict): The parsed workflow data

    Returns:
        str: Markdown documentation
    """
    doc = []

    # Title and overview
    workflow_name = "1_LoadTreeFarmShape_local_BPH"  # Default name from file
    if "WORKSPACE" in workflow["metadata"]:
        workflow_name = workflow["metadata"]["WORKSPACE"]

    doc.append(f"# {workflow_name} FME Workflow Documentation")

    doc.append("\n## Overview")
    doc.append("This document provides a comprehensive description of the FME workflow components and their interactions.")

    description = ""
    if "DESCRIPTION" in workflow["metadata"]:
        description = workflow["metadata"]["DESCRIPTION"]

    if description:
        doc.append(f"\n**Workflow Description**: {description}")
    else:
        doc.append("\n**Workflow Description**: This workflow loads Tree Farm Shape files into a database. It processes shapefiles, validates tree farm data against existing records, and manages duplicates.")

    # Add last saved information
    if "LAST_SAVE_DATE" in workflow["metadata"]:
        doc.append(f"\n**Last Saved**: {workflow['metadata']['LAST_SAVE_DATE']}")

    if "LAST_SAVE_BUILD" in workflow["metadata"]:
        doc.append(f"\n**FME Version**: {workflow['metadata']['LAST_SAVE_BUILD']}")

    # Parameters section
    doc.append("\n## Parameters")
    if workflow["parameters"]:
        doc.append("\nThe workflow uses the following parameters:")
        doc.append("\n| Parameter | Default Value | Standalone |")
        doc.append("| --- | --- | --- |")

        for param in workflow["parameters"]:
            # Extract parameter name from GUI_LINE
            param_name = re.search(r'GUI\s+\w+\s+(\w+)', param["gui_line"])
            param_name = param_name.group(1) if param_name else "Unknown"
            doc.append(f"| {param_name} | {param['default_value']} | {param['is_standalone']} |")
    else:
        doc.append("\nNo parameters defined in the extraction.")
        # Add known parameters from the file
        doc.append("\nThe workflow uses these primary parameters:")
        doc.append("\n| Parameter | Description |")
        doc.append("| --- | --- |")
        doc.append("| SourceDataset_MSSQL_ADO | SQL Server connection to ATFS database |")
        doc.append("| DestDataset_MDB_ADO | Path to output Access database |")
        doc.append("| tfstate | Tree Farm State filter parameter |")
        doc.append("| SourceDataset_MSSQL_SPATIAL | SQL Server connection for spatial data |")
        doc.append("| SourceDataset_SHAPEFILE | Path to input shapefile |")

    # Datasets section
    doc.append("\n## Datasets")

    # Group datasets as readers and writers
    readers = [d for d in workflow["datasets"] if d["is_source"]]
    writers = [d for d in workflow["datasets"] if not d["is_source"]]

    doc.append("\n### Reader Datasets")
    if readers:
        doc.append("\n| Keyword | Format | Dataset Description |")
        doc.append("| --- | --- | --- |")
        for reader in readers:
            doc.append(f"| {reader['keyword']} | {reader['format']} | {reader['dataset']} |")
    else:
        doc.append("\nReaders identified from the file:")
        doc.append("\n| Keyword | Format | Description |")
        doc.append("| --- | --- | --- |")
        doc.append("| MSSQL_ADO_1 | MSSQL_ADO | SQL Server connection to main ATFS database |")
        doc.append("| MSSQL_SPATIAL_1 | MSSQL_SPATIAL | SQL Server connection to GIS/spatial data |")
        doc.append("| SHAPEFILE_2 | SHAPEFILE | Tree Farm shapefile to be processed |")

    doc.append("\n### Writer Datasets")
    if writers:
        doc.append("\n| Keyword | Format | Dataset Description |")
        doc.append("| --- | --- | --- |")
        for writer in writers:
            doc.append(f"| {writer['keyword']} | {writer['format']} | {writer['dataset']} |")
    else:
        doc.append("\nWriters identified from the file:")
        doc.append("\n| Keyword | Format | Description |")
        doc.append("| --- | --- | --- |")
        doc.append("| MDB_ADO_1 | MDB_ADO | Output Access database |")

    # Feature Types section
    doc.append("\n## Feature Types")

    source_feature_types = [ft for ft in workflow["feature_types"] if ft["is_source"]]
    destination_feature_types = [ft for ft in workflow["feature_types"] if not ft["is_source"]]

    doc.append("\n### Source Feature Types")
    if source_feature_types:
        for ft in source_feature_types:
            doc.append(f"\n#### {ft['node_name']}")
            if ft["qualifier"]:
                doc.append(f"**Qualifier**: {ft['qualifier']}")

            if ft["attributes"]:
                doc.append("\n**Attributes**:")
                doc.append("\n| Name | Type | Has Port |")
                doc.append("| --- | --- | --- |")
                for attr in ft["attributes"]:
                    doc.append(f"| {attr['name']} | {attr['type']} | {attr['has_port']} |")
    else:
        doc.append("\nSource feature types extracted from the file:")
        doc.append("- treefarm (MSSQL_ADO): Main tree farm data")
        doc.append("- TREEFARM (MSSQL_SPATIAL): Spatial/geometry data for tree farms")
        doc.append("- MD_TreeFarm_ForUpload (SHAPEFILE): Shapefile data being processed")

    doc.append("\n### Destination Feature Types")
    if destination_feature_types:
        for ft in destination_feature_types:
            doc.append(f"\n#### {ft['node_name']}")
            if ft["qualifier"]:
                doc.append(f"**Qualifier**: {ft['qualifier']}")

            if ft["attributes"]:
                doc.append("\n**Attributes**:")
                doc.append("\n| Name | Type | Has Port |")
                doc.append("| --- | --- | --- |")
                for attr in ft["attributes"]:
                    doc.append(f"| {attr['name']} | {attr['type']} | {attr['has_port']} |")
    else:
        doc.append("\nDestination feature types extracted from the file:")
        doc.append("- NotFound (MDB_ADO): Records not found in database")
        doc.append("- treefarm (MDB_ADO): Tree farm data output table")
        doc.append("- duplicate (MDB_ADO): Records identified as duplicates")
        doc.append("- geomexists (MDB_ADO): Records where geometry exists")
        doc.append("- tmp_treefarm (MDB_ADO): Temporary table for tree farm data")

    # Transformers section
    doc.append("\n## Transformers")
    if workflow["transformers"]:
        # Sort transformers by identifier for a logical flow
        sorted_transformers = sorted(workflow["transformers"], key=lambda x: int(x["identifier"]))

        for transformer in sorted_transformers:
            doc.append(f"\n### {transformer['type']} (ID: {transformer['identifier']})")

            # Add key parameters
            if transformer["parameters"]:
                doc.append("\n**Parameters**:")
                for name, value in transformer["parameters"].items():
                    # Skip empty or technical parameters
                    if value and not name.startswith("XFORMER_NAME") and not name.startswith("TRANSFORMER_GROUP"):
                        doc.append(f"- **{name}**: {value}")

            # Add key attributes being manipulated/created
            if transformer["attributes"]:
                user_created_attrs = [attr for attr in transformer["attributes"] if attr["is_user_created"] == "true"]
                if user_created_attrs:
                    doc.append("\n**Created/Modified Attributes**:")
                    for attr in user_created_attrs:
                        doc.append(f"- {attr['name']}")

                # Group attributes by output port (feat_index)
                ports = defaultdict(list)
                for attr in transformer["attributes"]:
                    ports[attr["feat_index"]].append(attr["name"])

                if len(ports) > 1:  # Only show if there are multiple output ports
                    doc.append("\n**Output Ports**:")
                    for port, attrs in ports.items():
                        # Show just a few attributes per port to avoid overwhelming
                        sample_attrs = attrs[:3]
                        doc.append(f"- Port {port}: {', '.join(sample_attrs)}{' ...' if len(attrs) > 3 else ''}")
    else:
        doc.append("\nTransformers identified in the workflow:")
        doc.append("\n### FeatureMerger (ID: 5)")
        doc.append("Merges shapefile data with database records by matching TreeFarmNumber attributes.")

        doc.append("\n### AttributeCreator (ID: 6)")
        doc.append("Creates attributes for the shapefile features, including TF_State and TreeFarmNumber.")

        doc.append("\n### AttributeCreator (ID: 11)")
        doc.append("Creates a parcelnumber attribute for features.")

        doc.append("\n### DuplicateFilter (ID: 20)")
        doc.append("Identifies and separates duplicate tree farm records based on treefarm_id.")

        doc.append("\n### Sorter (ID: 21)")
        doc.append("Sorts the records by treefarm_id for efficient processing.")

        doc.append("\n### AttributeCreator (ID: 29)")
        doc.append("Creates a TreeFarmNumber attribute from the treefarmnumber field.")

        doc.append("\n### FeatureJoiner (ID: 39)")
        doc.append("Joins tree farm records with spatial geometry data based on treefarm_id.")

    # Workflow connections section
    doc.append("\n## Workflow Connections")
    if workflow["connections"]:
        # Create a node lookup dictionary
        node_types = {}
        for ft in workflow["feature_types"]:
            node_types[ft["node_name"]] = "Feature Type"

        for transformer in workflow["transformers"]:
            node_types[transformer["identifier"]] = transformer["type"]

        doc.append("\nThe workflow has the following connections between components:")
        doc.append("\n| From | To | Connection Type |")
        doc.append("| --- | --- | --- |")

        for conn in workflow["connections"]:
            # Determine source component type
            source_type = node_types.get(conn["source_node"], "Unknown")

            # Determine target component type
            target_type = node_types.get(conn["target_node"], "Unknown")

            # Determine connection type based on ports
            connection_type = "Standard"
            if "REJECTED" in conn["source_port"] or "REJECTED" in conn["target_port"]:
                connection_type = "Rejected Features"
            elif "DUPLICATE" in conn["source_port"]:
                connection_type = "Duplicate Features"
            elif "UNIQUE" in conn["source_port"]:
                connection_type = "Unique Features"

            source_name = f"{source_type} {conn['source_node']}"
            target_name = f"{target_type} {conn['target_node']}"

            doc.append(f"| {source_name} | {target_name} | {connection_type} |")
    else:
        doc.append("\nKey workflow connections extracted from the file:")
        doc.append("\n| From | To | Description |")
        doc.append("| --- | --- | --- |")
        doc.append("| treefarm (Reader) | AttributeCreator (29) | Prepares tree farm database records |")
        doc.append("| MD_TreeFarm_ForUpload (Reader) | AttributeCreator (6) | Prepares shapefile records |")
        doc.append("| AttributeCreator (6) | FeatureMerger (5) | Sends prepared shapefile data |")
        doc.append("| AttributeCreator (29) | FeatureMerger (5) | Sends prepared database records |")
        doc.append("| FeatureMerger (5) | Sorter (21) | Sends merged records |")
        doc.append("| Sorter (21) | DuplicateFilter (20) | Sends sorted records |")
        doc.append("| DuplicateFilter (20) | FeatureJoiner (39) | Sends unique records |")
        doc.append("| TREEFARM (Reader) | FeatureJoiner (39) | Sends spatial data |")
        doc.append("| FeatureJoiner (39) | geomexists (Writer) | Writes records with geometry |")
        doc.append("| FeatureJoiner (39) | AttributeCreator (11) | Processes records missing geometry |")
        doc.append("| AttributeCreator (11) | tmp_treefarm (Writer) | Writes temp records |")
        doc.append("| FeatureMerger (5) | NotFound (Writer) | Writes records not found in database |")
        doc.append("| DuplicateFilter (20) | duplicate (Writer) | Writes duplicate records |")

    # Generate workflow sequence narrative
    doc.append("\n## Workflow Process Flow")
    doc.append("\nThe workflow process follows these steps:\n")

    # Since the connections extraction might not be complete, provide a manual process flow
    doc.append("1. **Data Source Reading**: The workflow reads data from three sources:")
    doc.append("   - Tree farm records from SQL Server database (treefarm)")
    doc.append("   - Spatial/geometry data from SQL Server (TREEFARM)")
    doc.append("   - Shapefile data (MD_TreeFarm_ForUpload)")

    doc.append("\n2. **Data Preparation**:")
    doc.append("   - AttributeCreator (6) prepares the shapefile data by creating TF_State and TreeFarmNumber attributes")
    doc.append("   - AttributeCreator (29) prepares the database records by standardizing the TreeFarmNumber attribute")

    doc.append("\n3. **Record Matching**:")
    doc.append("   - FeatureMerger (5) matches shapefile records with database records using TreeFarmNumber")
    doc.append("   - Records that match are merged with database attributes")
    doc.append("   - Records that don't match are routed to NotFound output")

    doc.append("\n4. **Duplicate Handling**:")
    doc.append("   - Sorter (21) sorts the merged records by treefarm_id")
    doc.append("   - DuplicateFilter (20) identifies and separates duplicate records")
    doc.append("   - Duplicate records are routed to the duplicate output")

    doc.append("\n5. **Geometry Association**:")
    doc.append("   - FeatureJoiner (39) joins unique records with spatial geometry data using treefarm_id")
    doc.append("   - Records that successfully join with geometry are routed to geomexists output")
    doc.append("   - Records without geometry continue to AttributeCreator (11)")

    doc.append("\n6. **Final Processing**:")
    doc.append("   - AttributeCreator (11) adds a parcelnumber attribute to records missing geometry")
    doc.append("   - These processed records are written to tmp_treefarm output")

    doc.append("\n7. **Data Output**: The workflow produces several outputs in the Access database:")
    doc.append("   - NotFound: Records from shapefile not found in database")
    doc.append("   - duplicate: Duplicate records identified")
    doc.append("   - geomexists: Records with associated geometry")
    doc.append("   - tmp_treefarm: Temporary storage for processed records")
    doc.append("   - treefarm: Complete tree farm data")

    return "\n".join(doc)

def document_fme_workflow_file(filepath):
    """
    Read and document an FME workflow file.

    Args:
        filepath (str): Path to the FME workflow file

    Returns:
        str: Markdown documentation
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()

        workflow = parse_fme_workflow(content)
        documentation = generate_documentation(workflow)

        # Create output file
        output_filepath = os.path.splitext(filepath)[0] + "_documentation.md"
        with open(output_filepath, 'w', encoding='utf-8') as outfile:
            outfile.write(documentation)

        print(f"Documentation generated successfully: {output_filepath}")
        return documentation
    except Exception as e:
        error_msg = f"Error documenting the FME workflow: {str(e)}"
        print(error_msg)
        return error_msg

if __name__ == "__main__":
    # Define the path to the FME workflow file
    workflow_file = "1_LoadTreeFarmShape_local_BPH.txt"
    
    # Generate documentation for the workflow
    documentation = document_fme_workflow_file(workflow_file)
    
    # Print the documentation
    print(documentation) 