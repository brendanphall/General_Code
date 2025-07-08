import sys
import os
import importlib.util

# ✅ Correct file path — watch for the space after 'Email' which caused a past issue!
file_path = "/Users/brendanhall/GitHub/General_Code/ATFS/Email/GraphHelperAFF004/graph_helper.py"
module_name = "graph_helper"

# Import graph_helper dynamically
spec = importlib.util.spec_from_file_location(module_name, file_path)
graph_helper = importlib.util.module_from_spec(spec)
sys.modules[module_name] = graph_helper
spec.loader.exec_module(graph_helper)

# Reference the class
GraphHelper = graph_helper.GraphHelper

# ✅ IMPORTANT: initialize first
GraphHelper.initialize_graph_for_user_auth()

# Now make request
helper = GraphHelper()
messages = helper.get("/me/mailFolders/inbox/messages?$top=5")  # Try using /me instead of full email
print(messages)
