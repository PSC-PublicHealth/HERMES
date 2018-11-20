REM ###################################################################################
REM # Copyright © 2015, Pittsburgh Supercomputing Center (PSC).  All Rights Reserved. #
REM # =============================================================================== #
REM #                                                                                 #
REM # Permission to use, copy, and modify this software and its documentation without # 
REM # fee for personal use within your organization is hereby granted, provided that  #
REM # the above copyright notice is preserved in all copies and that the copyright    # 
REM # and this permission notice appear in supporting documentation.  All other       #
REM # restrictions and obligations are defined in the GNU Affero General Public       #
REM # License v3 (AGPL-3.0) located at http://www.gnu.org/licenses/agpl-3.0.html  A   #
REM # copy of the license is also provided in the top level of the source directory,  #
REM # in the file LICENSE.txt.                                                        #
REM #                                                                                 #
REM ###################################################################################

@echo off
setlocal

if exist %HOMEDRIVE%\Python27\python.exe (
  set PATH="%path%";%HOMEDRIVE%\Python27;%HOMEDRIVE%\Python27\Scripts
) else if exist %HOMEDRIVE%\Python27-64\python.exe (
   set PATH="%path%";%HOMEDRIVE%\Python27-64;%HOMEDRIVE%\Python27-64\Scripts
) else if exist %HOMEDRIVE%\Python26\python.exe (
   set PATH="%path%";%HOMEDRIVE%\Python26;%HOMEDRIVE%\Python26\Scripts
) else if exist %HOMEDRIVE%\Python25\python.exe (
   set PATH="%path%";%HOMEDRIVE%\Python25;%HOMEDRIVE%\Python25\Scripts
) else ( 
   echo "Could not find python"
   exit /b %errorlevel%
)

REM There is no 'easy_install sqlite'
python "%cd%\..\ui_server\thirdparty\setuptools\ez_setup.py"
easy_install sqlalchemy
easy_install alembic

python "%cd%\install_hermes.py"
endlocal
