import org.geotools.api.data.FileDataStore;
import org.geotools.api.data.FileDataStoreFinder;
import org.geotools.api.data.SimpleFeatureSource;
import org.geotools.api.referencing.crs.CoordinateReferenceSystem;
import org.geotools.referencing.CRS;

import java.io.File;

public class GeotoolsTest {
    public static void main(String[] args) throws Exception {
        // Choose one approach:

        // Option 1: Hardcoded path
        String shapefilePath = "/Users/brendanhall/Sewall/Projects/ATFS/_ArcGIS/ATFS_Scratch/Data/Shapefiles/1st Batch/Volz Joint Trust/Volz_Joint_Trust.shp";
        File shpFile = new File(shapefilePath);

        // Option 2: Command-line argument
        // File shpFile = new File(args[0]);

        if (!shpFile.exists()) {
            System.out.println("File not found: " + shpFile.getAbsolutePath());
            return;
        }

        FileDataStore store = FileDataStoreFinder.getDataStore(shpFile);
        SimpleFeatureSource featureSource = store.getFeatureSource();
        CoordinateReferenceSystem crs = featureSource.getInfo().getCRS();

        System.out.println("🔍 CRS Name: " + crs.getName());
        System.out.println("📐 CRS WKT:");
        System.out.println(crs.toWKT());

        try {
            String code = CRS.lookupIdentifier(crs, true);
            System.out.println("✅ EPSG Code Detected: " + code);
        } catch (Exception e) {
            System.out.println("❌ Unable to resolve EPSG code.");
            e.printStackTrace();
        }

        // Don't forget to dispose of the store when done
        store.dispose();

        System.out.println("\n---");
    }
}