@echo off
set string=

:LOOP
IF "%1"=="" GOTO CONTINUE 
set "string=%string%  %1"
SHIFT
GOTO LOOP


:CONTINUE

set HERMES_DATA_PATH="\\fs\apps\HERMES2\master_data\unified"
set PYTHONPATH="%PYTHONPATH%;\\fs\apps\HERMES2\"
set PATH=%PATH%;\\fs\apps\Python2.7.1\

echo %HERMES_DATA_PATH%
echo %PYTHONPATH%
echo %PATH%

python.exe \\fs\apps\HERMES2\main.py %string%