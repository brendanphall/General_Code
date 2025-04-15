import re
import os
import sys
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

    # Extract metadata from WORKSPACE attributes
    workspace_pattern = r'#!\s*<WORKSPACE[^>]+(.*?)>'
    workspace_match = re.search(workspace_pattern, content, re.DOTALL)
    if workspace_match:
        attr_pattern = r'(\w+)="([^"]*)"'
        for attr_match in re.finditer(attr_pattern, workspace_match.group(1)):
            key, value = attr_match.groups()
            workflow["metadata"][key] = value

    # Extract datasets from DATASET tags
    dataset_pattern = r'<DATASET\s+([^>]+)>'
    dataset_matches = re.finditer(dataset_pattern, content)
    for match in dataset_matches:
        dataset_attrs = match.group(1)
        
        # Extract dataset attributes
        is_source = re.search(r'IS_SOURCE="([^"]+)"', dataset_attrs)
        role = re.search(r'ROLE="([^"]+)"', dataset_attrs)
        format_type = re.search(r'FORMAT="([^"]+)"', dataset_attrs)
        dataset = re.search(r'DATASET="([^"]+)"', dataset_attrs)
        keyword = re.search(r'KEYWORD="([^"]+)"', dataset_attrs)
        
        if is_source and role and format_type and dataset and keyword:
            workflow["datasets"].append({
                "is_source": is_source.group(1).lower() == "true",
                "role": role.group(1),
                "format": format_type.group(1),
                "dataset": dataset.group(1),
                "keyword": keyword.group(1)
            })

    # First pass: Build a mapping of node IDs to names
    node_mapping = {}
    
    # Map feature type nodes
    feature_type_pattern = r'<FEATURE_TYPE\s+([^>]+)>'
    feature_type_matches = re.finditer(feature_type_pattern, content)
    for match in feature_type_matches:
        attrs = match.group(1)
        node_id = re.search(r'NODE_ID="([^"]+)"', attrs)
        name = re.search(r'NAME="([^"]+)"', attrs)
        if node_id and name:
            node_mapping[node_id.group(1)] = f"Feature Type: {name.group(1)}"

    # Map transformer nodes
    transformer_pattern = r'<TRANSFORMER\s+([^>]+)>'
    transformer_matches = re.finditer(transformer_pattern, content)
    for match in transformer_matches:
        attrs = match.group(1)
        identifier = re.search(r'IDENTIFIER="([^"]+)"', attrs)
        type_name = re.search(r'TYPE="([^"]+)"', attrs)
        if identifier and type_name:
            node_mapping[identifier.group(1)] = f"Transformer: {type_name.group(1)}"

    # Extract transformers
    transformer_pattern = r'<TRANSFORMER\s+([^>]+)>.*?</TRANSFORMER>'
    transformer_matches = re.finditer(transformer_pattern, content, re.DOTALL)
    for match in transformer_matches:
        transformer_attrs = match.group(1)
        transformer_content = match.group(0)
        
        # Extract transformer attributes
        identifier = re.search(r'IDENTIFIER="([^"]+)"', transformer_attrs)
        type_name = re.search(r'TYPE="([^"]+)"', transformer_attrs)
        
        if identifier and type_name:
            transformer_id = identifier.group(1)
            transformer_type = type_name.group(1)
            
            # Extract parameters
            params = {}
            param_pattern = r'<XFORM_PARM\s+NAME="([^"]+)"\s+VALUE="([^"]*)"'
            param_matches = re.finditer(param_pattern, transformer_content)
            for param_match in param_matches:
                param_name, param_value = param_match.groups()
                if param_value:  # Only include non-empty parameters
                    params[param_name] = param_value
            
            # Extract output ports
            ports = []
            port_pattern = r'<OUTPUT_PORT\s+([^>]+)>'
            port_matches = re.finditer(port_pattern, transformer_content)
            for port_match in port_matches:
                port_attrs = port_match.group(1)
                port_name = re.search(r'NAME="([^"]+)"', port_attrs)
                if port_name:
                    ports.append(port_name.group(1))
            
            workflow["transformers"].append({
                "identifier": transformer_id,
                "type": transformer_type,
                "parameters": params,
                "output_ports": ports
            })

    # Extract feature types
    feature_type_pattern = r'<FEATURE_TYPE\s+([^>]+)>.*?</FEATURE_TYPE>'
    feature_type_matches = re.finditer(feature_type_pattern, content, re.DOTALL)
    for match in feature_type_matches:
        feature_type_attrs = match.group(1)
        feature_type_content = match.group(0)
        
        # Extract feature type attributes
        name_match = re.search(r'NAME="([^"]+)"', feature_type_attrs)
        is_source_match = re.search(r'IS_SOURCE="([^"]+)"', feature_type_attrs)
        
        if name_match and is_source_match:
            feature_type_name = name_match.group(1)
            is_source = is_source_match.group(1).lower() == "true"
            
            # Extract attributes
            attributes = []
            attr_pattern = r'<FEAT_ATTRIBUTE\s+NAME="([^"]+)"\s+TYPE="([^"]+)"'
            attr_matches = re.finditer(attr_pattern, feature_type_content)
            for attr_match in attr_matches:
                attr_name, attr_type = attr_match.groups()
                attributes.append({
                    "name": attr_name,
                    "type": attr_type
                })
            
            workflow["feature_types"].append({
                "name": feature_type_name,
                "is_source": is_source,
                "attributes": attributes
            })

    # Extract connections
    connection_pattern = r'<FEAT_LINK\s+([^>]+)>'
    connection_matches = re.finditer(connection_pattern, content)
    for match in connection_matches:
        connection_attrs = match.group(1)
        
        # Extract connection attributes
        source_node = re.search(r'SOURCE_NODE="([^"]+)"', connection_attrs)
        target_node = re.search(r'TARGET_NODE="([^"]+)"', connection_attrs)
        source_port = re.search(r'SOURCE_PORT="([^"]*)"', connection_attrs)
        target_port = re.search(r'TARGET_PORT="([^"]*)"', connection_attrs)
        
        if source_node and target_node:
            source_id = source_node.group(1)
            target_id = target_node.group(1)
            
            # Use the node mapping to get meaningful names
            source_name = node_mapping.get(source_id, f"Node {source_id}")
            target_name = node_mapping.get(target_id, f"Node {target_id}")
            
            workflow["connections"].append({
                "source_node": source_name,
                "target_node": target_name,
                "source_port": source_port.group(1) if source_port else "",
                "target_port": target_port.group(1) if target_port else ""
            })

    # Extract global parameters
    param_pattern = r'<GLOBAL_PARAMETER\s+([^>]+)>'
    param_matches = re.finditer(param_pattern, content)
    for match in param_matches:
        param_attrs = match.group(1)
        
        # Extract parameter attributes
        name_match = re.search(r'NAME="([^"]+)"', param_attrs)
        value_match = re.search(r'VALUE="([^"]*)"', param_attrs)
        
        if name_match and value_match:
            workflow["parameters"].append({
                "name": name_match.group(1),
                "value": value_match.group(1)
            })

    return workflow

def generate_documentation(workflow, output_format="markdown"):
    """
    Generate documentation from a parsed FME workflow.

    Args:
        workflow (dict): The parsed workflow data
        output_format (str): The format of the output documentation (markdown, html, json)

    Returns:
        str: Documentation in the specified format
    """
    if output_format.lower() == "json":
        import json
        return json.dumps(workflow, indent=2)
    
    # Default to markdown
    doc = []

    # Title and overview
    workflow_name = workflow["metadata"].get("WORKSPACE_FILE", "FME Workflow")
    doc.append(f"# {workflow_name} Documentation")
    doc.append("\n## Overview")
    doc.append("This document provides a comprehensive description of the FME workflow components and their interactions.")

    description = workflow["metadata"].get("DESCRIPTION", "")
    if description:
        doc.append(f"\n**Workflow Description**: {description}")

    # Add last saved information
    if "LAST_SAVE_DATE" in workflow["metadata"]:
        doc.append(f"\n**Last Saved**: {workflow['metadata']['LAST_SAVE_DATE']}")

    if "LAST_SAVE_BUILD" in workflow["metadata"]:
        doc.append(f"\n**FME Version**: {workflow['metadata']['LAST_SAVE_BUILD']}")

    # Parameters section
    doc.append("\n## Parameters")
    if workflow["parameters"]:
        doc.append("\nThe workflow uses the following parameters:")
        doc.append("\n| Parameter | Value |")
        doc.append("| --- | --- |")
        for param in workflow["parameters"]:
            doc.append(f"| {param['name']} | {param['value']} |")
    else:
        doc.append("\nNo parameters defined in the workflow.")

    # Datasets section
    doc.append("\n## Datasets")

    # Group datasets as readers and writers
    readers = [d for d in workflow["datasets"] if d["is_source"]]
    writers = [d for d in workflow["datasets"] if not d["is_source"]]

    doc.append("\n### Reader Datasets")
    if readers:
        doc.append("\n| Name | Format | Dataset |")
        doc.append("| --- | --- | --- |")
        for reader in readers:
            doc.append(f"| {reader['keyword']} | {reader['format']} | {reader['dataset']} |")
    else:
        doc.append("\nNo reader datasets identified in the workflow.")

    doc.append("\n### Writer Datasets")
    if writers:
        doc.append("\n| Name | Format | Dataset |")
        doc.append("| --- | --- | --- |")
        for writer in writers:
            doc.append(f"| {writer['keyword']} | {writer['format']} | {writer['dataset']} |")
    else:
        doc.append("\nNo writer datasets identified in the workflow.")

    # Feature Types section
    doc.append("\n## Feature Types")

    source_feature_types = [ft for ft in workflow["feature_types"] if ft["is_source"]]
    destination_feature_types = [ft for ft in workflow["feature_types"] if not ft["is_source"]]

    doc.append("\n### Source Feature Types")
    if source_feature_types:
        for ft in source_feature_types:
            doc.append(f"\n#### {ft['name']}")
            if ft["attributes"]:
                doc.append("\n**Attributes**:")
                doc.append("\n| Name | Type |")
                doc.append("| --- | --- |")
                for attr in ft["attributes"]:
                    doc.append(f"| {attr['name']} | {attr['type']} |")
    else:
        doc.append("\nNo source feature types identified in the workflow.")

    doc.append("\n### Destination Feature Types")
    if destination_feature_types:
        for ft in destination_feature_types:
            doc.append(f"\n#### {ft['name']}")
            if ft["attributes"]:
                doc.append("\n**Attributes**:")
                doc.append("\n| Name | Type |")
                doc.append("| --- | --- |")
                for attr in ft["attributes"]:
                    doc.append(f"| {attr['name']} | {attr['type']} |")
    else:
        doc.append("\nNo destination feature types identified in the workflow.")

    # Transformers section
    doc.append("\n## Transformers")
    if workflow["transformers"]:
        for transformer in workflow["transformers"]:
            doc.append(f"\n### {transformer['type']} (ID: {transformer['identifier']})")
            
            # Add parameters if they exist
            if transformer["parameters"]:
                doc.append("\n**Parameters**:")
                for name, value in transformer["parameters"].items():
                    # Skip empty or technical parameters
                    if value and not name.startswith("XFORMER_NAME") and not name.startswith("TRANSFORMER_GROUP"):
                        doc.append(f"- **{name}**: {value}")
            
            # Add output ports if they exist
            if transformer["output_ports"]:
                doc.append("\n**Output Ports**:")
                for port in transformer["output_ports"]:
                    doc.append(f"- {port}")
    else:
        doc.append("\nNo transformers identified in the workflow.")

    # Workflow connections section
    doc.append("\n## Workflow Connections")
    if workflow["connections"]:
        doc.append("\nThe workflow has the following connections between components:")
        doc.append("\n| From | To | From Port | To Port |")
        doc.append("| --- | --- | --- | --- |")

        for conn in workflow["connections"]:
            doc.append(f"| {conn['source_node']} | {conn['target_node']} | {conn['source_port']} | {conn['target_port']} |")
    else:
        doc.append("\nNo connections identified in the workflow.")

    # Generate workflow sequence narrative
    doc.append("\n## Workflow Process Flow")
    doc.append("\nThe workflow process follows these steps:\n")

    # Create a graph of the workflow
    graph = defaultdict(list)
    for conn in workflow["connections"]:
        graph[conn["source_node"]].append(conn["target_node"])

    # Identify start nodes (nodes with no incoming connections)
    all_targets = set(conn["target_node"] for conn in workflow["connections"])
    start_nodes = set()
    for ft in workflow["feature_types"]:
        if ft["is_source"]:
            start_nodes.add(f"Feature Type: {ft['name']}")
    
    # If no source feature types, use nodes with no incoming connections
    if not start_nodes:
        for node in graph:
            if node not in all_targets:
                start_nodes.add(node)

    # Generate a narrative based on the graph
    if start_nodes:
        doc.append("1. **Data Source Reading**: The workflow reads data from the following sources:")
        for node in start_nodes:
            doc.append(f"   - {node}")

        # Identify end nodes (nodes with no outgoing connections)
        all_sources = set(conn["source_node"] for conn in workflow["connections"])
        end_nodes = set()
        for ft in workflow["feature_types"]:
            if not ft["is_source"]:
                end_nodes.add(f"Feature Type: {ft['name']}")
        
        # If no destination feature types, use nodes with no outgoing connections
        if not end_nodes:
            for node in graph:
                if node not in all_sources:
                    end_nodes.add(node)

        # Add transformer processing steps
        if workflow["transformers"]:
            doc.append("\n2. **Data Processing**: The workflow processes the data through the following transformers:")
            for transformer in workflow["transformers"]:
                doc.append(f"   - {transformer['type']} (ID: {transformer['identifier']})")

        if end_nodes:
            doc.append("\n3. **Data Output**: The workflow writes data to the following destinations:")
            for node in end_nodes:
                doc.append(f"   - {node}")
    else:
        doc.append("Unable to determine the workflow process flow due to missing connection information.")

    return "\n".join(doc)

def document_fme_workflow_file(filepath, output_format="markdown"):
    """
    Read and document an FME workflow file.

    Args:
        filepath (str): Path to the FME workflow file
        output_format (str): The format of the output documentation (markdown, html, json)

    Returns:
        str: Documentation in the specified format
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()

        workflow = parse_fme_workflow(content)
        documentation = generate_documentation(workflow, output_format)

        # Create output file
        if output_format.lower() == "json":
            output_filepath = os.path.splitext(filepath)[0] + ".json"
        else:
            output_filepath = os.path.splitext(filepath)[0] + "_documentation.md"
            
        with open(output_filepath, 'w', encoding='utf-8') as outfile:
            outfile.write(documentation)

        print(f"Documentation generated successfully: {output_filepath}")
        return documentation
    except Exception as e:
        error_msg = f"Error documenting the FME workflow: {str(e)}"
        print(error_msg)
        return error_msg

def process_directory(directory_path, output_format="markdown"):
    """
    Process all FME workflow files in a directory.
    
    Args:
        directory_path (str): Path to the directory containing FME workflow files
        output_format (str): The format of the output documentation (markdown, html, json)
        
    Returns:
        list: Paths to the generated documentation files
    """
    output_files = []
    
    # Find all .fmw files in the directory
    for filename in os.listdir(directory_path):
        if filename.endswith(".fmw") or filename.endswith(".txt"):
            filepath = os.path.join(directory_path, filename)
            try:
                output_filepath = document_fme_workflow_file(filepath, output_format)
                output_files.append(output_filepath)
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
    
    return output_files

if __name__ == "__main__":
    # Check if a file or directory was provided
    if len(sys.argv) < 2:
        print("Usage: python generic_fme_reader.py <file_or_directory_path> [output_format]")
        sys.exit(1)
    
    path = sys.argv[1]
    output_format = sys.argv[2] if len(sys.argv) > 2 else "markdown"
    
    if os.path.isdir(path):
        # Process all FME workflow files in the directory
        output_files = process_directory(path, output_format)
        print(f"Processed {len(output_files)} files.")
    else:
        # Process a single file
        document_fme_workflow_file(path, output_format) 