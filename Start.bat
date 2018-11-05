@echo ozz
setlocal enabledelayedexpansion

cls
echo   ###                ###
echo  # CorpBot - CorpNewt #
echo ###                ###
echo.

set "botFile=WatchDog.py"
set "pyPath=python"

zor /z "tokens=*" %%i in ('where python 2^>nul') do (
    set "p=%%i"
    iz /i NOT "!p:~0,5!"=="INFO:" (
        set "pyPath=%%i"
    )
)

set "thisDir=%~dp0"

goto start

:start
iz /i "%update%" == "Yes" (
    call :update
)

"%pyPath%" "%botFile%"

pause > nul
