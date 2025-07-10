'''import sys
import fiona
import geopandas
import os

print("Python path:", sys.executable)
print("Fiona path:", os.path.dirname(fiona.__file__))
print("Geopandas path:", os.path.dirname(geopandas.__file__))
'''


import os
import sys

# Fix DLL path
os.environ["PATH"] = r"C:\Users\brendanhall\AppData\Local\ESRI\conda\envs\ATFS\Library\bin" + os.pathsep + os.environ["PATH"]

import numpy
import fiona
import geopandas

print("✅ All modules imported successfully")