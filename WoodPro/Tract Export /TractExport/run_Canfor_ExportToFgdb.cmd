@echo off
REM yyyymmdd_hhmmss is a date_time stamp like 20100902_134200
set hh=%time:~0,2%
REM Since there is no leading zero for times before 10 am, have to put in
REM a zero when this is run before 10 am.
if "%time:~0,1%"==" " set hh=0%hh:~1,1%
set yyyymmdd_hhmmss=%date:~10,4%%date:~4,2%%date:~7,2%_%hh%%time:~3,2%%time:~6,2%
set yyyymmdd=%date:~10,4%%date:~4,2%%date:~7,2%

D:
set batchdir=D:\ArcGIS\clients\canfor\TractExport
if not exist %batchdir%\ExportToFgdb.py GOTO :ERROR
cd %batchdir%

set shpdir=%batchdir%\Shapefiles
if exist %shpdir% rmdir /s /q %shpdir%
mkdir %shpdir%

@call propy ExportToFgdb.py

move %shpdir% %shpdir%_%yyyymmdd%

@call "C:\Program Files\7-Zip\7z.exe" a -tzip -r -bd -mx9 %shpdir%_%yyyymmdd% %shpdir%_%yyyymmdd%
move /y %shpdir%_%yyyymmdd%.zip Export

@call propy emailFilegdb.py %batchdir%\Export\Shapefiles_%yyyymmdd%.zip

rmdir /s /q %shpdir%_%yyyymmdd%

goto :END

:ERROR
echo ERROR: ExportToFgdb.py script not found
goto :END

:END
