@echo off
setlocal
set oldcurdir=%cd%
cd /d %~dp0
set PATH=%~dp0..\..\python;%~dp0..\..\python\Scripts;%PATH%
echo Attempting to add initial models if they do not yet exist>>..\..\install_hermes.log
for %%n in ("..\..\data\automodels\*.zip") do (
    python.exe add_model_to_db.py --no_overwrite_db --use_zip="%%n">>..\..\install_hermes.log 2>&1
)
cd /d %oldcurdir%
endlocal