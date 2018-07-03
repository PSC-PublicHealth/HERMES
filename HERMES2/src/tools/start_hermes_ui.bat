@echo off
setlocal

set curdir=%cd%
set pythonexe=python

if exist "%cd%\..\..\python\python.exe" (
 rem pass
) else if exist %HOMEDRIVE%\Python27\python.exe (
  set PATH="%path%";%HOMEDRIVE%\Python27;%HOMEDRIVE%\Python27\Scripts
) else if exist %HOMEDRIVE%\Python27-64\python.exe (
  set PATH="%path%";%HOMEDRIVE%\Python27-64;%HOMEDRIVE%\Python27-64\Scripts
) else if exist %HOMEDRIVE%\Python26\python.exe (
   set PATH="%path%";%HOMEDRIVE%\Python26;%HOMEDRIVE%\Python26\Scripts
) else if exist %HOMEDRIVE%\Python25\python.exe (
   set PATH="%path%";%HOMEDRIVE%\Python25;%HOMEDRIVE%\Python25\Scripts
) else ( 
   echo "Could not find python"
REM   exit /b %errorlevel%
)




REM Start the server

cd "%cd%\..\ui_server\"
if exist "%cd%\..\..\python\python.exe" (
  start "HERMES Server" ..\..\python\python standalone_server.py
) else (
  start python standalone_server.py
)

REM Sleep 5 seconds by pinging a non-existant address 6 times
C:\Windows\system32\PING.exe -n 5 127.0.0.1 > nul

REM Tell the browser to open the right web page

if exist "%cd%\..\..\python\python.exe" (
  ..\..\python\python -m webbrowser -t "http://localhost:8080/bottle_hermes/top"
else (
  python -m webbrowser -t "http://localhost:8080/bottle_hermes/top"
)

endlocal
