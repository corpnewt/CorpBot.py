@echo off

cls
echo   ###                ###
echo  # CorpBot - CorpNewt #
echo ###                ###
echo.

set "botFile=Main.py"
set "pyPath=python"
set "autoRestart=No"
set "update=No"

set "thisDir=%~dp0"

goto start

:update
pushd "%thisDir%"
echo Updating...
echo.
git pull origin rewrite
echo.
popd
goto :EOF

:start
if /i "%update%" == "Yes" (
    call :update
)

REM Launch our script - tell it we didn't reboot, and give it python's path
"%pyPath%" "%botFile%" -reboot No -path "%pyPath%"

if /i "%autoRestart%"=="Yes" (
    timeout 10
    goto start
)
pause