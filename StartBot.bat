@echo off

cls
echo   ###                   ###
echo  # BotStarter - CorpNewt #
echo ###                   ###
echo.

set "thisDir=%~dp0"
set "rd=Redis-x64-5.0.14.1"
set "rdold=Redis-x64-3.2.100"
set "redis=redis-server.exe"
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
    echo   https://github.com/lavalink-devs/Lavalink/releases/latest
    echo.
    pause
    exit /b
)
timeout %wait%
echo.
REM Only start the Redis server if we're using the redis
REM branch of CorpBot.py
if EXIST "%thisDir%\Cogs\PandorasDB.py" (
    if EXIST "%thisDir%\%rd%\%redis%" (
        echo Starting database...
        pushd "%thisDir%\%rd%"
        start "" "%redis%"
        popd
        echo Waiting %wait% seconds...
        echo.
    ) else (
        if EXIST "%thisDir%\%rdold%\%redis%" (
            echo !! WARNING: Located older redis install, please consider updating via the following link:
            echo   https://github.com/tporadowski/redis/releases/download/v5.0.14.1/Redis-x64-5.0.14.1.zip
            echo.
            echo Starting database...
            pushd "%thisDir%\%rdold%"
            start "" "%redis%"
            popd
            echo Waiting %wait% seconds...
            echo.
        ) else (
            echo "%thisDir%\%rd%\%redis%"
            echo does not exist!
            echo.
            echo You can get it from:
            echo   https://github.com/tporadowski/redis/releases/download/v5.0.14.1/Redis-x64-5.0.14.1.zip
            echo.
            pause
            exit /b
        )
    )
    timeout %wait%
    echo.
)
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
