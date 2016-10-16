@echo off

cls
echo   ###                ###
echo  # CorpBot - CorpNewt #
echo ###                ###
echo.

set "botFile=Main.py"
set "pyPath=python"
set "autoRestart=Yes"

goto start

:start
"%pyPath%" "%botFile%"
if /i "%autoRestart%"=="Yes" goto start
pause