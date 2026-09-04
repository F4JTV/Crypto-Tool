@echo off
rem ===========================================================================
rem  build_windows.cmd - construit Crypto Tool sans toucher a la strategie
rem  d'execution de PowerShell.
rem
rem  Double-cliquez ce fichier, ou lancez-le depuis cmd ou PowerShell :
rem
rem      .\build_windows.cmd              build complet
rem      .\build_windows.cmd app          build portable seul
rem      .\build_windows.cmd installer    installateur seul, depuis dist\
rem      .\build_windows.cmd clean        nettoie puis reconstruit
rem
rem  POURQUOI CE FICHIER EXISTE
rem  --------------------------
rem  Lancer build_windows.ps1 directement echoue souvent avec « n'est pas
rem  signe numeriquement » ou « l'execution de scripts est desactivee ».
rem  C'est une strategie Windows, pas un defaut du script. Deux mecanismes
rem  distincts sont en jeu :
rem
rem    1. La strategie d'execution. « Restricted » bloque tout script ;
rem       « AllSigned » bloque tout ce qui n'a pas de certificat de
rem       signature de code.
rem    2. La marque du web. Un fichier extrait d'une archive telechargee
rem       porte un flux de donnees alternatif indiquant son origine, et
rem       « RemoteSigned » le refuse alors meme que la strategie autoriserait
rem       un script local.
rem
rem  Ce lanceur traite les deux : il retire la marque sur les fichiers du
rem  projet, puis demarre PowerShell avec -ExecutionPolicy Bypass, ce qui ne
rem  vaut que pour ce seul processus. Rien n'est modifie sur votre machine et
rem  aucune strategie n'est affaiblie ailleurs.
rem
rem  Si votre strategie est imposee par une strategie de groupe,
rem  -ExecutionPolicy est ignore et cela echouera quand meme. Dans ce cas,
rem  suivez les etapes manuelles listees dans README.md.
rem ===========================================================================

setlocal
cd /d "%~dp0"

echo Retrait de la marque du web sur les fichiers du projet...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Get-ChildItem -Path '%~dp0' -Recurse -File -ErrorAction SilentlyContinue | Unblock-File -ErrorAction SilentlyContinue"

echo Demarrage de la construction...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_windows.ps1" %*
set BUILD_ERROR=%ERRORLEVEL%

if not "%BUILD_ERROR%"=="0" (
    echo.
    echo La construction a echoue avec le code %BUILD_ERROR%.
)

echo.
pause
exit /b %BUILD_ERROR%
