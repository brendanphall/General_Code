USE [master]
GO

-- Restore primary database: atfs
RESTORE DATABASE [atfs]
FROM DISK = N'C:\Program Files\Microsoft SQL Server\MSSQL15.SQLEXPRESS\MSSQL\Backup\atfs_bak_20250408_020000\atfs.bak'
WITH FILE = 1,
MOVE N'atfs' TO N'C:\Program Files\Microsoft SQL Server\MSSQL15.SQLEXPRESS\MSSQL\DATA\atfs.mdf',
MOVE N'atfs_log' TO N'C:\Program Files\Microsoft SQL Server\MSSQL15.SQLEXPRESS\MSSQL\DATA\atfs.ldf',
NOUNLOAD, REPLACE, STATS = 10;
GO

USE [atfs]
GO
IF NOT EXISTS (SELECT * FROM sysusers WHERE name = 'atfs')
    CREATE USER [atfs] FOR LOGIN [atfs] WITH DEFAULT_SCHEMA=[dbo];
ELSE
    ALTER USER [atfs] WITH DEFAULT_SCHEMA=[dbo];
GO
EXEC sp_addrolemember N'db_owner', N'atfs';
GO
-- see about replacing below,
EXEC sp_change_users_login 'Auto_Fix', 'atfs';
-- ALTER USER [atfs] WITH LOGIN = [atfs];
GO

USE [master]
GO
ALTER DATABASE [atfs] SET RECOVERY SIMPLE WITH NO_WAIT;
GO

-- Restore second database: atfs_gdb (unique file names!)
RESTORE DATABASE [atfs_gdb]
FROM DISK = N'C:\Program Files\Microsoft SQL Server\MSSQL15.SQLEXPRESS\MSSQL\Backup\atfs_bak_20250408_020000\atfs.bak'
WITH FILE = 1,
MOVE N'atfs' TO N'C:\Program Files\Microsoft SQL Server\MSSQL15.SQLEXPRESS\MSSQL\DATA\atfs_gdb.mdf',
MOVE N'atfs_log' TO N'C:\Program Files\Microsoft SQL Server\MSSQL15.SQLEXPRESS\MSSQL\DATA\atfs_gdb.ldf',
NOUNLOAD, REPLACE, STATS = 10;
GO

ALTER DATABASE [atfs_gdb] SET RECOVERY SIMPLE WITH NO_WAIT;
GO

USE [atfs_gdb]
GO
IF NOT EXISTS (SELECT * FROM sysusers WHERE name = 'atfs')
    CREATE USER [atfs] FOR LOGIN [atfs] WITH DEFAULT_SCHEMA=[dbo];
ELSE
    ALTER USER [atfs] WITH DEFAULT_SCHEMA=[dbo];
GO
EXEC sp_addrolemember N'db_owner', N'atfs';
GO
EXEC sp_change_users_login 'Auto_Fix', 'atfs';
GO

-- Optional: No-op backups (for recovery model reset)
BACKUP DATABASE [atfs] TO DISK='NUL';
GO
BACKUP DATABASE [atfs_gdb] TO DISK='NUL';
GO

-- Optional: Shrink files (careful in production!)
USE [atfs]
GO
DBCC shrinkfile (atfs_log, 100);
DBCC shrinkfile (atfs, 500);
GO
