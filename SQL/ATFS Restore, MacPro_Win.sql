USE [master]
GO

-- === Restore ATFS full backup ===
RESTORE DATABASE [atfs]
FROM DISK = N'C:\Temp\ATFS\atfs_bak_20250408_020000\atfs.bak'
WITH FILE = 1,
MOVE N'atfs' TO N'C:\Program Files\Microsoft SQL Server\MSSQL16.SQL_MACPRO_MAUTH\MSSQL\DATA\atfs.mdf',
MOVE N'atfs_log' TO N'C:\Program Files\Microsoft SQL Server\MSSQL16.SQL_MACPRO_MAUTH\MSSQL\DATA\atfs.ldf',
NOUNLOAD, NORECOVERY, REPLACE
GO

-- === Restore ATFS log backup ===
RESTORE LOG [atfs]
FROM DISK = N'C:\Temp\ATFS\atfs_bak_20250408_020000\atfs_log.bak'
WITH FILE = 1, NORECOVERY
GO

-- === Finalize restore ===
RESTORE DATABASE [atfs] WITH RECOVERY
GO

-- === Fix user mapping for ATFS ===
USE [atfs]
GO
IF NOT EXISTS (SELECT * FROM sysusers WHERE name = 'atfs')
    CREATE USER [atfs] FOR LOGIN [atfs] WITH DEFAULT_SCHEMA = [dbo];
ELSE
    ALTER USER [atfs] WITH DEFAULT_SCHEMA = [dbo];
GO
EXEC sp_addrolemember N'db_owner', N'atfs'
GO
EXEC sp_change_users_login 'Auto_Fix', 'atfs'
GO

-- === Set ATFS to SIMPLE recovery ===
USE [master]
GO
ALTER DATABASE [atfs] SET RECOVERY SIMPLE WITH NO_WAIT
GO

-- === Restore ATFS_GDB full backup ===
RESTORE DATABASE [atfs_gdb]
FROM DISK = N'C:\Temp\ATFS\atfs_bak_20250408_020000\atfs_gdb.bak'
WITH FILE = 1,
MOVE N'atfs_gdb' TO N'C:\Program Files\Microsoft SQL Server\MSSQL16.SQL_MACPRO_MAUTH\MSSQL\DATA\atfs_gdb.mdf',
MOVE N'atfs_gdb_log' TO N'C:\Program Files\Microsoft SQL Server\MSSQL16.SQL_MACPRO_MAUTH\MSSQL\DATA\atfs_gdb_log.ldf',
NOUNLOAD, NORECOVERY, REPLACE, STATS = 10
GO

-- === Restore ATFS_GDB log backup ===
RESTORE LOG [atfs_gdb]
FROM DISK = N'C:\Temp\ATFS\atfs_bak_20250408_020000\atfs_gdb_log.bak'
WITH FILE = 1, NORECOVERY
GO

-- === Finalize restore for ATFS_GDB ===
RESTORE DATABASE [atfs_gdb] WITH RECOVERY
GO

-- === Fix user mapping for ATFS_GDB ===
USE [atfs_gdb]
GO
IF NOT EXISTS (SELECT * FROM sysusers WHERE name = 'atfs')
    CREATE USER [atfs] FOR LOGIN [atfs] WITH DEFAULT_SCHEMA = [dbo];
ELSE
    ALTER USER [atfs] WITH DEFAULT_SCHEMA = [dbo];
GO
EXEC sp_addrolemember N'db_owner', N'atfs'
GO
EXEC sp_change_users_login 'Auto_Fix', 'atfs'
GO

-- === Set ATFS_GDB to SIMPLE recovery ===
USE [master]
GO
ALTER DATABASE [atfs_gdb] SET RECOVERY SIMPLE WITH NO_WAIT
GO

-- === Optional shrink (for dev/testing only) ===
USE [atfs]
GO
DBCC shrinkfile (atfs_log, 100);
DBCC shrinkfile (atfs, 500);
GO
