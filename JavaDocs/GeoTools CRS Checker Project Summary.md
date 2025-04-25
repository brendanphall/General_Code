# GeoTools CRS Checker Project Summary

## Overview
We created a Java application using GeoTools to analyze the Coordinate Reference System (CRS) information in shapefiles. The application can process individual shapefiles or scan directories recursively to find all shapefiles and extract their CRS information.

## Steps Completed

1. **Set up the Maven project**:
   - Created a POM file with GeoTools dependencies
   - Configured repositories to access GeoTools artifacts
   - Resolved dependency issues related to GeoTools 30.1

2. **Created the Java application**:
   - Implemented code to read shapefiles and extract CRS information
   - Fixed package import issues (e.g., `SimpleFeatureSource` moved to `org.geotools.api.data`)
   - Added functionality to recursively search directories for shapefiles

3. **Enhanced the application to output XML**:
   - Added XML generation to output CRS information for multiple shapefiles
   - Included file paths, CRS names, WKT representations, and detected EPSG codes

4. **Discovered CRS discrepancies**:
   - Found that `CRS.lookupIdentifier(crs, true)` with the "lenient" parameter set to true sometimes returns different EPSG codes than what's declared in the shapefile
   - All test shapefiles declared EPSG:3857 (Web Mercator) but were detected as EPSG:3395 (World Mercator)

## Key Code Components

### Main Application (GeotoolsTest.java)
```java
import org.geotools.api.data.FileDataStore;
import org.geotools.api.data.FileDataStoreFinder;
import org.geotools.api.data.SimpleFeatureSource;
import org.geotools.api.referencing.crs.CoordinateReferenceSystem;
import org.geotools.referencing.CRS;

// ... other imports

public class GeotoolsTest {
    public static void main(String[] args) throws Exception {
        // Process shapefiles and output XML with CRS information
        // ...
    }
    
    private static void findShapefiles(File directory, List<File> shapefiles) {
        // Recursively find shapefiles in directories
        // ...
    }
}
```

### Maven Dependencies (pom.xml)
```xml
<dependencies>
    <dependency>
        <groupId>org.geotools</groupId>
        <artifactId>gt-main</artifactId>
        <version>${geotools.version}</version>
    </dependency>
    <dependency>
        <groupId>org.geotools</groupId>
        <artifactId>gt-shapefile</artifactId>
        <version>${geotools.version}</version>
    </dependency>
    <dependency>
        <groupId>org.geotools</groupId>
        <artifactId>gt-swing</artifactId>
        <version>${geotools.version}</version>
    </dependency>
    <!-- ... other dependencies ... -->
</dependencies>
```

## Key GeoTools Functions Used

- `FileDataStoreFinder.getDataStore(File)` - To load shapefile data
- `store.getFeatureSource()` - To access the shapefile's feature data
- `featureSource.getInfo().getCRS()` - To get the CRS from the shapefile
- `crs.getName()` - To get the CRS name
- `crs.toWKT()` - To get the Well-Known Text representation of the CRS
- `CRS.lookupIdentifier(crs, true)` - To detect the EPSG code from the CRS parameters

## Findings

All five tested shapefiles had the same CRS information:
- Declared as EPSG:3857 (Web Mercator) in the WKT
- Detected as EPSG:3395 (World Mercator) by `CRS.lookupIdentifier()`

This discrepancy highlights the importance of validating CRS information in GIS data, as even small differences in projection methods can lead to spatial inaccuracies.

## Next Steps

Potential improvements to the application:
- Add the ability to reproject shapefiles to a specified CRS
- Include more detailed comparison between declared and detected CRS parameters
- Create a GUI for easier file selection and visualization of results
- Add a reporting feature for batch processing of large shapefile collections