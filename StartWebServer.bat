@echo off

cls
echo   ###                ###
echo  # CorpBot - CorpNewt #
echo ###                ###
echo WebServer
echo.

set "botFile=WebServer.py"
set "pyPath=python"
set "autoRestart=Yes"

REM Set the FLASK_APP PATH var
set FLASK_APP=%botFile%

flask run

pause
goto :EOF

REM goto start

:start
"%pyPath%" "%botFile%"
if /i "%autoRestart%"=="Yes" (
    timeout 10
    goto start
)
pause