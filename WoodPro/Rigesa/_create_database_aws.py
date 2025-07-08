### 2024-04-10 - create database and 3 connections

import arcpy, os

### config

db_name = 'westrock_brasil'
postgres_admin = ['westrock_brasil_postgres_db.sde', 'postgres', 'Megaera123']
gdb_admin =      ['westrock_brasil_sde-lic_db', 'sde', 'Megaera123']
client_user =    ['westrock_brasil_db', 'westrock_brasil', 'westrock_brasil$1234']
wip =            r'D:\arcgis\clients\westrock_brasil'

### create a postgres geodatabase

# CreateEnterpriseGeodatabase(
#   database_platform, instance_name, {database_name}, {account_authentication}, {database_admin}, {database_admin_password},
#   {sde_schema}, {gdb_admin_name}, {gdb_admin_password}, {tablespace_name}, authorization_file)
arcpy.CreateEnterpriseGeodatabase_management(
    "POSTGRESQL", "db", db_name, "DATABASE_AUTH", postgres_admin[1], postgres_admin[2], "", gdb_admin[1], gdb_admin[2], "",
    r"C:\Program Files\ESRI\License11.3\sysgen\keycodes")

### create connections

# arcpy.management.CreateDatabaseConnection(
#  out_folder_path, out_name, database_platform, instance, {account_authentication}, {username}, {password}, {save_user_pass}, {database}, {schema}, {version_type}, {version}, {date})
arcpy.CreateDatabaseConnection_management(
    wip,  postgres_admin[0], "POSTGRESQL", "db",
    "DATABASE_AUTH", postgres_admin[1], postgres_admin[2], "SAVE_USERNAME", db_name)

arcpy.CreateDatabaseConnection_management(
    wip,  gdb_admin[0], "POSTGRESQL", "db",
    "DATABASE_AUTH", gdb_admin[1], gdb_admin[2], "SAVE_USERNAME", db_name)

conn = os.path.join(wip, postgres_admin[0])

# arcpy.management.CreateDatabaseUser(input_database, {user_authentication_type}, user_name, {user_password}, {role}, {tablespace_name})
arcpy.CreateDatabaseUser_management(conn, "DATABASE_USER", client_user[1], client_user[2])

arcpy.CreateDatabaseConnection_management(
    wip, client_user[0], "POSTGRESQL", "db",
    "DATABASE_AUTH", client_user[1], client_user[2], "SAVE_USERNAME", db_name)

print('done')