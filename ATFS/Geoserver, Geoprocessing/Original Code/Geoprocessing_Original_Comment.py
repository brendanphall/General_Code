'''
--------------------------------------------------------------------------------------------
Project: Kapstone Stumps 2.0
Version: ArcGIS server 10.1
Author: Nathan Gurney
Params:
    [0] inZipFile {data type: File, direction: in, type: optional}
    [1] outFeatureClass {data type: FeatureClass, direction: out, type: optional}
--------------------------------------------------------------------------------------------
2021-07-22: updated for python 3
'''

import sys, zipfile, arcpy, os, traceback
from os.path import isdir, join, normpath, split

def logMessage(msg):
    arcpy.AddMessage("[py] " + msg)

# Function to unzipping the contents of the zip file
#
def unzipfiles(path, zip):
    shapefileName = ''
    # If the output location does not yet exist, create it
    #
    if not isdir(path):
        os.makedirs(path)

    for x in zip.namelist():
        arcpy.AddMessage("Extracting " + os.path.basename(x) + " ...")

        # if we file a shapefile, cache the file name
        fileExt = os.path.splitext(x)[1].lower()
        # logMessage(fileExt)
        if (fileExt == ".shp"):
            # logMessage("found a shapefile " + str(x))
            shapefileName = normpath(str(x))

        # Check to see if the item was written to the zip file with an
        # archive name that includes a parent directory. If it does, create
        # the parent folder in the output workspace and then write the file,
        # otherwise, just write the file to the workspace.
        #
        if not x.endswith('/'):
            root, name = split(x)
            directory = normpath(join(path, root))
            if not isdir(directory):
                os.makedirs(directory)
            open(join(directory, name), 'wb').write(zip.read(x))

    return shapefileName

# **********************************************************************
# Description:
#    Unzips the contents of a zip file into an existing folder.
# Arguments:
#  0 - Input zip file
#  1 - Input folder - path to existing folder that will contain
#      the contents of the zip file.
# **********************************************************************
def unzip(infile, outfol):
    try:
        # Get the tool parameter values
        #
        # infile = arcpy.GetParameterAsText(0)
        # outfol = arcpy.GetParameterAsText(1)

        # Create the zipfile handle for reading and unzip it
        #
        zip = zipfile.ZipFile(infile, 'r')
        shapefileName = unzipfiles(outfol, zip)
        zip.close()

        return shapefileName

    except:
        # Return any Python specific errors and any error returned by the geoprocessor
        #
        tb = sys.exc_info()[2]
        tbinfo = traceback.format_tb(tb)[0]
        pymsg = "PYTHON ERRORS:\nTraceback Info:\n" + tbinfo + "\nError Info:\n    " + str(sys.exc_type) + ": " + str(
            sys.exc_value) + "\n"
        arcpy.AddError(pymsg)

        msgs = "GP ERRORS:\n" + arcpy.GetMessages(2) + "\n"
        arcpy.AddError(msgs)

    # project shapefiel to web mercator

def project(shapefilename):
    # shapefileName might have sub-path
    inShp = os.path.join(arcpy.env.scratchFolder, shapefileName)
    root, name = split(inShp)
    outShp = os.path.join(root, "_" + name)
    spref = arcpy.SpatialReference(102100)
    arcpy.Project_management(inShp, outShp, spref)
    return outShp

if __name__ == '__main__':
    logMessage("script started")

    try:
        # debug
        logMessage("arcpy.env.scratchFolder: " + str(arcpy.env.scratchFolder))
        logMessage("arcpy.env.scratchWorkspace: " + str(arcpy.env.scratchWorkspace))
    except:
        logMessage("no scratch")

    try:
        # Get Parameters
        p5 = arcpy.GetParameter(0)
        logMessage("file: " + str(p5))

        # let script run with no zipfile for gp service setup
        if p5 == '#' or not p5 or str(p5) == '':
            logMessage("no zip file")
        else:
            shapefileName = unzip(str(p5), arcpy.env.scratchFolder)
            logMessage("shapefile: " + shapefileName)
            shapefile2 = project(shapefileName)
            arcpy.SetParameterAsText(1, shapefile2)
    except:
        logMessage("bad params")
        logMessage(sys.exc_info()[0])

    logMessage("finished")
