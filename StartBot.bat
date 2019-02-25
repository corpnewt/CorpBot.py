@echo off

cls
echo   ###                   ###
echo  # BotStarter - CorpNewt #
echo ###                   ###
echo.

set "thisDir=%~dp0"
set "rd=Redis-x64-3.2.100"
set "redis=redis-server.exe"
set "start=Start.bat"
set /a wait=5

if EXIST "%thisDir%\%rd%\%redis%" (
    echo Starting database...
    pushd "%thisDir%\%rd%"
    start "" "%redis%"
    popd
    echo Waiting %wait% seconds...
    echo.
    timeout %wait%
) else (
    echo "%thisDir%\%redis%"
    echo does not exist!
)
echo.
if EXIST "%thisDir%\%start%" (
    echo Starting bot...
    start cmd /c "%thisDir%\%start%"
    echo.
) else (
    echo "%thisDir%\%start%"
    echo does not exist!
)
echo.
echo Done.
timeout %wait%