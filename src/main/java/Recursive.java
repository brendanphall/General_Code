import org.geotools.api.data.FileDataStore;
import org.geotools.api.data.FileDataStoreFinder;
import org.geotools.api.data.SimpleFeatureSource;
import org.geotools.api.referencing.crs.CoordinateReferenceSystem;
import org.geotools.referencing.CRS;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.transform.OutputKeys;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;
import org.w3c.dom.Document;
import org.w3c.dom.Element;

import java.io.File;
import java.io.FileOutputStream;
import java.util.ArrayList;
import java.util.List;

public class Recursive {
    public static void main(String[] args) throws Exception {
        // Specify the directory to search
        String directoryPath = "/Users/brendanhall/Sewall/Projects/ATFS/_ArcGIS/ATFS_Scratch/Data";
        if (args.length > 0) {
            directoryPath = args[0];
        }

        // Specify the output XML file
        String outputPath = "shapefile_crs_info.xml";
        if (args.length > 1) {
            outputPath = args[1];
        }

        File directory = new File(directoryPath);
        if (!directory.exists() || !directory.isDirectory()) {
            System.out.println("Invalid directory: " + directory.getAbsolutePath());
            return;
        }

        // Find all shapefiles
        List<File> shapefiles = new ArrayList<>();
        findShapefiles(directory, shapefiles);

        System.out.println("Found " + shapefiles.size() + " shapefiles");

        // Create XML document
        DocumentBuilderFactory docFactory = DocumentBuilderFactory.newInstance();
        DocumentBuilder docBuilder = docFactory.newDocumentBuilder();
        Document doc = docBuilder.newDocument();

        // Root element
        Element rootElement = doc.createElement("ShapefileCRSInfo");
        doc.appendChild(rootElement);

        // Process each shapefile
        for (File shapefile : shapefiles) {
            System.out.println("Processing: " + shapefile.getAbsolutePath());
            try {
                FileDataStore store = FileDataStoreFinder.getDataStore(shapefile);
                if (store == null) {
                    System.out.println("Failed to load shapefile: " + shapefile.getAbsolutePath());
                    continue;
                }

                SimpleFeatureSource featureSource = store.getFeatureSource();
                CoordinateReferenceSystem crs = featureSource.getInfo().getCRS();

                if (crs == null) {
                    System.out.println("No CRS found for: " + shapefile.getAbsolutePath());
                    store.dispose();
                    continue;
                }

                // Create shapefile element
                Element shapefileElement = doc.createElement("Shapefile");
                rootElement.appendChild(shapefileElement);

                // Add path attribute
                shapefileElement.setAttribute("path", shapefile.getAbsolutePath());

                // Add CRS name
                Element crsNameElement = doc.createElement("CRSName");
                crsNameElement.setTextContent(crs.getName().toString());
                shapefileElement.appendChild(crsNameElement);

                // Add CRS WKT
                Element crsWktElement = doc.createElement("CRSWKT");
                crsWktElement.setTextContent(crs.toWKT());
                shapefileElement.appendChild(crsWktElement);

                // Try to get EPSG code
                try {
                    String code = CRS.lookupIdentifier(crs, true);
                    Element epsgCodeElement = doc.createElement("EPSGCode");
                    epsgCodeElement.setTextContent(code);
                    shapefileElement.appendChild(epsgCodeElement);
                } catch (Exception e) {
                    Element epsgCodeElement = doc.createElement("EPSGCode");
                    epsgCodeElement.setTextContent("Unknown");
                    shapefileElement.appendChild(epsgCodeElement);
                }

                // Clean up
                store.dispose();
            } catch (Exception e) {
                System.out.println("Error processing: " + shapefile.getAbsolutePath());
                e.printStackTrace();
            }
        }

        // Write the XML document to file
        TransformerFactory transformerFactory = TransformerFactory.newInstance();
        Transformer transformer = transformerFactory.newTransformer();
        transformer.setOutputProperty(OutputKeys.INDENT, "yes");
        transformer.setOutputProperty("{http://xml.apache.org/xslt}indent-amount", "2");

        DOMSource source = new DOMSource(doc);
        StreamResult result = new StreamResult(new FileOutputStream(outputPath));
        transformer.transform(source, result);

        System.out.println("CRS information written to " + outputPath);
    }

    /**
     * Recursively find all shapefiles in the given directory and its subdirectories
     */
    private static void findShapefiles(File directory, List<File> shapefiles) {
        File[] files = directory.listFiles();
        if (files != null) {
            for (File file : files) {
                if (file.isDirectory()) {
                    findShapefiles(file, shapefiles);
                } else if (file.getName().toLowerCase().endsWith(".shp")) {
                    shapefiles.add(file);
                }
            }
        }
    }
}