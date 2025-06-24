from graph_helper import GraphHelper

GraphHelper.initialize_graph_for_user_auth()
user_info = GraphHelper.get_user()  # May fail in app-only context
messages = GraphHelper.get("/users/youruser@yourdomain.com/mailFolders/inbox/messages?$top=5")

print(messages)
