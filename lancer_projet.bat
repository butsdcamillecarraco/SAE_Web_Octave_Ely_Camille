@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Comparateur de Villes - Demarrage

echo =======================================================
echo   Recherche d'un Python valide (avec pip)...
echo =======================================================

set PYTHON_EXE=

for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python39\python.exe"
    "C:\Python314\python.exe"
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
) do (
    if EXIST %%P (
        %%P -m pip --version >NUL 2>&1
        if !ERRORLEVEL! EQU 0 (
            set PYTHON_EXE=%%P
            goto PYTHON_TROUVE
        )
    )
)

py -m pip --version >NUL 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_EXE=py
    goto PYTHON_TROUVE
)

echo.
echo   Aucun Python avec pip n'a ete trouve sur ce PC.
echo   Installez Python depuis https://www.python.org/downloads/
echo   et cochez "Add Python to PATH".
echo.
pause
exit /b 1

:PYTHON_TROUVE
echo   Python trouve : %PYTHON_EXE%
%PYTHON_EXE% --version
echo.

echo =======================================================
echo   Installation des dependances...
echo =======================================================

%PYTHON_EXE% -m pip install -r requirements.txt -q
if %ERRORLEVEL% NEQ 0 (
    echo   ERREUR : Installation des dependances echouee.
    pause
    exit /b 1
)
echo   Dependances OK.

echo.
echo =======================================================
echo   Demarrage du serveur Streamlit (fenetre minimisee)...
echo =======================================================

start /min "Streamlit Server" %PYTHON_EXE% -m streamlit run app.py --server.headless true --browser.gatherUsageStats false --browser.serverAddress localhost --server.port 8501

echo   En attente du demarrage...
echo   (30 secondes environ la premiere fois)
echo.

set ATTENTE=0
:BOUCLE
set /a ATTENTE+=1
if %ATTENTE% GTR 60 (
    echo.
    echo   ERREUR : Serveur non demarre apres 2 minutes.
    echo   Verifiez la fenetre "Streamlit Server" dans la barre des taches.
    pause
    exit /b 1
)

curl -s --max-time 1 -o NUL http://localhost:8501/_stcore/health 2>NUL
if %ERRORLEVEL% EQU 0 (
    echo   Serveur pret !
    goto OUVERTURE
)

echo   [%ATTENTE%/60] En attente...
timeout /t 2 /nobreak >NUL
goto BOUCLE

:OUVERTURE
echo.
echo =======================================================
echo   Ouverture du dashboard...
echo =======================================================
start "" index.html
echo   Dashboard ouvert !
echo.
echo   Pour arreter le serveur, fermez la fenetre "Streamlit Server"
echo   dans la barre des taches.
echo.
pause
