:::::::::::::::::::::::::::::::::::::::::
:: Automatically check & get admin rights
:::::::::::::::::::::::::::::::::::::::::
@echo off
CLS
ECHO.
ECHO =============================
ECHO Running Admin shell
ECHO =============================

:checkPrivileges
NET FILE 1>NUL 2>NUL
if '%errorlevel%' == '0' ( goto gotPrivileges ) else ( goto getPrivileges )

:getPrivileges
if '%1'=='ELEV' (shift & goto gotPrivileges)
ECHO.
ECHO **************************************
ECHO Invoking UAC for Privilege Escalation
ECHO **************************************

setlocal DisableDelayedExpansion
set "batchPath=%~0"
setlocal EnableDelayedExpansion
ECHO Set UAC = CreateObject^("Shell.Application"^) > "%temp%\OEgetPrivileges.vbs"
ECHO UAC.ShellExecute "!batchPath!", "ELEV", "", "runas", 1 >> "%temp%\OEgetPrivileges.vbs"
"%temp%\OEgetPrivileges.vbs"
exit /B

:gotPrivileges
::::::::::::::::::::::::::::
::START
::::::::::::::::::::::::::::


@echo off

cls
echo   ###                ###
echo  # CorpBot - CorpNewt #
echo ###                ###
echo.

REM echo Installing Chatterbot...
REM echo.
REM call :install "chatterbot"
REM echo.

REM echo Installing Discord...
REM echo.
REM call :install "discord.py[voice]"
REM echo.

echo Installing Discord [Development Version]...
echo.
call :install "https://github.com/Rapptz/discord.py/archive/rewrite.zip#egg=discord.py[voice]"
echo.

echo Installing Pillow...
echo.
call :install "Pillow"
echo.

echo Installing Youtube-dl...
echo.
call :install "youtube-dl"
echo.

echo Installing Requests...
echo.
call :install "requests"
echo.

echo Installing ParseDateTime...
echo.
call :install "parsedatetime"
echo.

echo Installing Psutil...
echo.
call :install "psutil"
echo.

echo Installing PyParsing...
echo.
call :install "pyparsing"
echo.

echo Installing PyQuery...
echo.
call :install "pyquery"
echo.

echo Installing PyAIML...
echo.
call :install "git+https://github.com/paulovn/python-aiml"
echo.

echo Installing PySpeedTest...
echo.
call :install "pyspeedtest"
echo.

echo Installing Pytz...
echo.
call :install "pytz"
echo.

echo Installing Wikipedia...
echo.
call :install "wikipedia"
echo.

echo Installing MTranslate...
echo.
call :install "mtranslate"
echo.

echo Installing GiphyPop
echo.
call :install "git+https://github.com/shaunduncan/giphypop.git#egg=giphypop"
echo.

echo Installing NumPy
echo.
call :install "numpy"
echo.

echo Installing Weather
echo.
call :install "weather-api"
echo.


REM echo Installing Flask...
REM echo.
REM call :install "Flask"
REM echo.

REM echo Installing Levenshtein...
REM echo.
REM call :install "python-levenshtein"
REM echo.

echo Done.
timeout 5 > nul
exit /b

:install <module>
pip install -U %~1
