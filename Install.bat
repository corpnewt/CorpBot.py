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

echo Installing Chatterbot...
echo.
call :install "chatterbot"
echo.

echo Installing Discord...
echo.
call :install "discord.py[voice]"
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

REM echo Installing Levenshtein...
REM echo.
REM call :install "python-levenshtein"
REM echo.

echo Done.
timeout 5 > nul
exit /b

:install <module>
pip install -U %~1
