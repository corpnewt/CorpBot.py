@echo off
setlocal enabledelayedexpansion

cls
echo   ###                ###
echo  # CorpBot - CorpNewt #
echo ###                ###
echo.

set "botFile=WatchDog.py"
set "pyPath=python"

for /f "tokens=*" %%i in ('where python 2^>nul') do (
    set "p=%%i"
    if /i NOT "!p:~0,5!"=="INFO:" (
        set "pyPath=%%i"
    )
)

set "thisDir=%~dp0"

goto start

:start
if /i "%update%" == "Yes" (
    call :update
)

"%pyPath%" "%botFile%"

pause > nul