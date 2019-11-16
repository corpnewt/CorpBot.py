@echo off

cls
echo   ###                   ###
echo  # BotStarter - CorpNewt #
echo ###                   ###
echo.

set "thisDir=%~dp0"
set "start=Start.bat"
set "ld=Lavalink"
set "lava=Lavalink.jar"
set /a wait=5

if EXIST "%thisDir%\%ld%\%lava%" (
    echo Starting Lavalink server...
    pushd "%thisDir%\%ld%"
    start "" java -jar "%lava%"
    popd
    echo Waiting %wait% seconds...
    echo.
) else (
    echo "%thisDir%\%ld%\%lava%"
    echo does not exist!
    echo.
    echo You can get it from:
    echo   https://github.com/Frederikam/Lavalink/releases/latest
    pause
    exit /b
)
timeout %wait%
echo.
if EXIST "%thisDir%\%start%" (
    echo Starting bot...
    start cmd /c "%thisDir%\%start%"
    echo.
) else (
    echo "%thisDir%\%start%"
    echo does not exist!
    pause
    exit /b
)
echo.
echo Done.
timeout %wait%