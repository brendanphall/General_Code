# FME Workflow Documentation

## Overview
This document provides a comprehensive description of the FME workflow components and their interactions.

## Parameters

No parameters defined in the workflow.

## Datasets

### Reader Datasets

| Name | Format | Dataset |
| --- | --- | --- |
| MSSQL_ADO_1 | MSSQL_ADO | $(SourceDataset_MSSQL_ADO) |
| SHAPEFILE_1 | SHAPEFILE | $(SourceDataset_SHAPEFILE_3) |

### Writer Datasets

| Name | Format | Dataset |
| --- | --- | --- |
| GEODATABASE_FILE_1 | GEODATABASE_FILE | $(DestDataset_GEODATABASE_FILE) |

## Feature Types

### Source Feature Types

#### treefarm

#### To_AFF_3-19-25_partial

### Destination Feature Types

#### tmp_treefarm

## Transformers

### FeatureMerger (ID: 5)

### AttributeCreator (ID: 11)

### DuplicateFilter (ID: 20)

### Sorter (ID: 21)

### AttributeCreator (ID: 29)

### EsriReprojector (ID: 37)

### AttributeCreator (ID: 28)

### Tester (ID: 26)

## Workflow Connections

The workflow has the following connections between components:

| From | To | From Port | To Port |
| --- | --- | --- | --- |
| Node 4 | Transformer: AttributeCreator |  |  |
| Node 27 | Transformer: Tester |  |  |
| Transformer: FeatureMerger | Transformer: Sorter |  |  |
| Transformer: AttributeCreator | Node 3 |  |  |
| Transformer: DuplicateFilter | Transformer: EsriReprojector |  |  |
| Transformer: Sorter | Transformer: DuplicateFilter |  |  |
| Transformer: Tester | Transformer: AttributeCreator |  |  |
| Transformer: AttributeCreator | Transformer: FeatureMerger |  |  |
| Transformer: AttributeCreator | Transformer: FeatureMerger |  |  |
| Transformer: EsriReprojector | Transformer: AttributeCreator |  |  |

## Workflow Process Flow

The workflow process follows these steps:

1. **Data Source Reading**: The workflow reads data from the following sources:
   - Feature Type: treefarm
   - Feature Type: To_AFF_3-19-25_partial

2. **Data Processing**: The workflow processes the data through the following transformers:
   - FeatureMerger (ID: 5)
   - AttributeCreator (ID: 11)
   - DuplicateFilter (ID: 20)
   - Sorter (ID: 21)
   - AttributeCreator (ID: 29)
   - EsriReprojector (ID: 37)
   - AttributeCreator (ID: 28)
   - Tester (ID: 26)

3. **Data Output**: The workflow writes data to the following destinations:
   - Feature Type: tmp_treefarm