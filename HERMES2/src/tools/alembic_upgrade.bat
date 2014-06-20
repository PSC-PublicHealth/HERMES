@echo off
setlocal

if exist %HOMEDRIVE%\Python27\python.exe (
  set PATH="%path%";%HOMEDRIVE%\Python27;%HOMEDRIVE%\Python27\Scripts
) else if exist %HOMEDRIVE%\Python26\python.exe (
   set PATH="%path%";%HOMEDRIVE%\Python26;%HOMEDRIVE%\Python26\Scripts
) else if exist %HOMEDRIVE%\Python25\python.exe (
   set PATH="%path%";%HOMEDRIVE%\Python25;%HOMEDRIVE%\Python25\Scripts
) else ( 
   echo "Could not find python"
   exit /b %errorlevel%
)

python alembic upgrade head

endlocal
