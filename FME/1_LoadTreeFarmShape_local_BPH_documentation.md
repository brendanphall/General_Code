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
| MSSQL_SPATIAL_1 | MSSQL_SPATIAL | $(SourceDataset_MSSQL_SPATIAL) |
| SHAPEFILE_2 | SHAPEFILE | $(SourceDataset_SHAPEFILE) |

### Writer Datasets

| Name | Format | Dataset |
| --- | --- | --- |
| MDB_ADO_1 | MDB_ADO | $(DestDataset_MDB_ADO) |

## Feature Types

### Source Feature Types

#### treefarm

#### TREEFARM

#### MD_TreeFarm_ForUpload

### Destination Feature Types

#### NotFound

#### treefarm

#### duplicate

#### geomexists

#### tmp_treefarm

## Transformers

### FeatureMerger (ID: 5)

### AttributeCreator (ID: 6)

### AttributeCreator (ID: 11)

### DuplicateFilter (ID: 20)

### Sorter (ID: 21)

### AttributeCreator (ID: 29)

### FeatureJoiner (ID: 39)

## Workflow Connections

The workflow has the following connections between components:

| From | To | From Port | To Port |
| --- | --- | --- | --- |
| Node 4 | Transformer: AttributeCreator |  |  |
| Node 33 | Transformer: FeatureJoiner |  |  |
| Node 45 | Transformer: AttributeCreator |  |  |
| Transformer: FeatureMerger | Transformer: Sorter |  |  |
| Transformer: AttributeCreator | Transformer: FeatureMerger |  |  |
| Transformer: AttributeCreator | Node 36 |  |  |
| Transformer: DuplicateFilter | Transformer: FeatureJoiner |  |  |
| Transformer: Sorter | Transformer: DuplicateFilter |  |  |
| Transformer: AttributeCreator | Transformer: FeatureMerger |  |  |
| Transformer: FeatureJoiner | Node 43 |  |  |
| Transformer: FeatureMerger | Node 19 |  |  |
| Transformer: DuplicateFilter | Node 28 |  |  |
| Transformer: FeatureJoiner | Transformer: AttributeCreator |  |  |
| Transformer: FeatureMerger | Node 26 |  |  |

## Workflow Process Flow

The workflow process follows these steps:

1. **Data Source Reading**: The workflow reads data from the following sources:
   - Feature Type: TREEFARM
   - Feature Type: treefarm
   - Feature Type: MD_TreeFarm_ForUpload

2. **Data Processing**: The workflow processes the data through the following transformers:
   - FeatureMerger (ID: 5)
   - AttributeCreator (ID: 6)
   - AttributeCreator (ID: 11)
   - DuplicateFilter (ID: 20)
   - Sorter (ID: 21)
   - AttributeCreator (ID: 29)
   - FeatureJoiner (ID: 39)

3. **Data Output**: The workflow writes data to the following destinations:
   - Feature Type: tmp_treefarm
   - Feature Type: treefarm
   - Feature Type: duplicate
   - Feature Type: geomexists
   - Feature Type: NotFound