<#
    build_windows.ps1 - Construit Crypto Tool et son installateur.

        .\build_windows.ps1              build complet
        .\build_windows.ps1 app          build portable seul, sans installateur
        .\build_windows.ps1 installer    installateur seul, depuis dist\
        .\build_windows.ps1 clean        nettoie puis reconstruit tout

        .\build_windows.ps1 -InnoSetupPath "D:\Inno\ISCC.exe"

    Prerequis : Python 3.10 ou superieur en 64 bits, et Inno Setup 6.3 ou
    superieur pour l'installateur (7 recommande).

    PyQt6, PyInstaller et Pillow sont installes dans un environnement virtuel
    local, .venv-build : rien n'est ajoute a votre Python systeme.

    Preferez lancer build_windows.cmd, qui contourne la strategie
    d'execution de PowerShell.
#>

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet("full", "app", "installer", "clean")]
    [string]$Mode = "full",

    [string]$InnoSetupPath = ""
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

$AppName = "CryptoTool"
$DistDir = "dist\$AppName"
$ExePath = "$DistDir\$AppName.exe"

function Write-Step($text) {
    Write-Host ""
    Write-Host "==> $text" -ForegroundColor Cyan
}

function Fail($text) {
    Write-Host ""
    Write-Host "ERREUR : $text" -ForegroundColor Red
    exit 1
}

# --- interpretation du mode ------------------------------------------------
# Filet de securite : la regle de positionnement des parametres a varie selon
# les versions de PowerShell. Si un mot de mode s'est malgre tout lie a
# -InnoSetupPath, on le remet ou il doit aller plutot que d'echouer plus loin
# sur un « ISCC.exe introuvable » qui n'expliquerait rien.
if ($InnoSetupPath -and @("full", "app", "installer", "clean") -contains $InnoSetupPath) {
    $Mode = $InnoSetupPath
    $InnoSetupPath = ""
}

$Clean = ($Mode -eq "clean")
$SkipInstaller = ($Mode -eq "app")
$SkipBuild = ($Mode -eq "installer")

Write-Host "Crypto Tool - construction Windows (mode : $Mode)" -ForegroundColor White

# --------------------------------------------------------------- clean ----
if ($Clean) {
    Write-Step "Nettoyage des sorties precedentes"
    foreach ($dir in @("build", "dist", "Output")) {
        if (Test-Path $dir) {
            Remove-Item -Recurse -Force $dir
            Write-Host "    supprime : $dir"
        }
    }
    foreach ($file in @("version_info.txt", "version.iss")) {
        if (Test-Path $file) { Remove-Item -Force $file }
    }
}

# ------------------------------------------------------------ python ------
Write-Step "Verification de Python"
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $python) {
    Fail ("Python est introuvable dans le PATH. Installez Python 3.10 ou " +
          "superieur en 64 bits depuis https://www.python.org/downloads/ " +
          "en cochant « Add python.exe to PATH ».")
}

$probe = & $python.Source -c "import struct, sys; print(struct.calcsize('P')*8); print('.'.join(map(str, sys.version_info[:3])))"
$bits = ($probe[0]).Trim()
$pyver = ($probe[1]).Trim()
Write-Host "    Python $pyver, $bits bits"
if ($bits -ne "64") {
    Fail ("Python $bits bits detecte. L'installateur produit un paquet " +
          "64 bits ; un Python 64 bits est necessaire.")
}

# ------------------------------------------------------- environnement ----
$venv = ".venv-build"
$venvPython = Join-Path $PSScriptRoot "$venv\Scripts\python.exe"

if (-not $SkipBuild) {
    if (-not (Test-Path $venv)) {
        Write-Step "Creation de l'environnement de construction"
        & $python.Source -m venv $venv
        if ($LASTEXITCODE -ne 0) { Fail "Creation de l'environnement virtuel echouee." }
    }
    if (-not (Test-Path $venvPython)) {
        Fail "L'environnement virtuel est casse. Supprimez $venv et relancez."
    }

    Write-Step "Installation des dependances de construction"
    & $venvPython -m pip install --upgrade pip --quiet
    & $venvPython -m pip install --upgrade PyQt6 cryptography pyinstaller pillow --quiet
    if ($LASTEXITCODE -ne 0) { Fail "L'installation des dependances a echoue." }
    Write-Host "    PyQt6, cryptography, PyInstaller et Pillow installes"

    # ---------------------------------------------------------- assets ----
    Write-Step "Generation de l'icone"
    & $venvPython make_icon.py
    if ($LASTEXITCODE -ne 0) { Fail "La generation de l'icone a echoue." }

    Write-Step "Generation des fichiers de version"
    & $venvPython make_version.py
    if ($LASTEXITCODE -ne 0) { Fail "La generation des fichiers de version a echoue." }

    # ----------------------------------------------------- pyinstaller ----
    Write-Step "Construction avec PyInstaller (un dossier)"
    & $venvPython -m PyInstaller --noconfirm --clean CryptoTool.spec
    if ($LASTEXITCODE -ne 0) { Fail "PyInstaller a echoue." }

    if (-not (Test-Path $ExePath)) { Fail "$ExePath n'a pas ete produit." }

    $mb = [math]::Round((Get-ChildItem -Recurse $DistDir |
        Measure-Object -Property Length -Sum).Sum / 1MB, 1)
    Write-Host "    $DistDir  ($mb Mo)"

    # ----------------------------------------------------- essai a vide ---
    # Un build qui ne demarre pas est pire que pas de build : autant s'en
    # apercevoir ici plutot que chez celui qui installera. --version sort
    # immediatement, ce qui verifie que l'executable gele resout tous ses
    # imports sans ouvrir de fenetre ni toucher aux reglages.
    Write-Step "Essai de demarrage de l'executable"
    $proc = Start-Process -FilePath $ExePath -ArgumentList "--version" `
        -NoNewWindow -Wait -PassThru
    if ($proc.ExitCode -ne 0) {
        Fail ("L'executable construit s'est termine avec le code " +
              "$($proc.ExitCode) sur --version. Relancez-le a la main depuis " +
              "une console pour voir le message d'erreur.")
    }
    Write-Host "    l'executable demarre correctement"
}
else {
    Write-Step "Construction ignoree (mode installer)"
    if (-not (Test-Path $ExePath)) {
        Fail ("$ExePath est absent. Le mode « installer » empaquete un build " +
              "existant ; lancez d'abord .\build_windows.cmd app")
    }
    if (-not (Test-Path "version.iss")) {
        Fail "version.iss est absent. Lancez : python make_version.py"
    }
    Write-Host "    empaquetage du build present dans $DistDir"
}

if ($SkipInstaller) {
    Write-Step "Termine (installateur ignore)"
    Write-Host "    Build portable : $DistDir\"
    exit 0
}

# -------------------------------------------------------- inno setup ------
# Aucun chemin n'est suppose. Inno Setup 7 existe en 32 et en 64 bits, donc
# sous « Program Files » comme sous « Program Files (x86) », et il peut aussi
# etre installe par utilisateur. On interroge donc, dans l'ordre : le
# parametre explicite, le PATH, les cles de desinstallation du registre,
# puis les dossiers habituels.
Write-Step "Recherche d'Inno Setup"

$searched = New-Object System.Collections.Generic.List[string]
$iscc = $null

function Try-Iscc([string]$path, [string]$how) {
    if (-not $path) { return $false }
    $script:searched.Add("$how : $path")
    if (Test-Path -LiteralPath $path -PathType Leaf) {
        $script:iscc = $path
        return $true
    }
    return $false
}

if ($InnoSetupPath) {
    if (-not (Try-Iscc $InnoSetupPath "-InnoSetupPath")) {
        Fail "-InnoSetupPath a ete donne mais $InnoSetupPath n'existe pas."
    }
}

if (-not $iscc) {
    $onPath = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($onPath) { [void](Try-Iscc $onPath.Source "PATH") }
}

if (-not $iscc) {
    $roots = @(
        "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*",
        "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\*"
    )
    foreach ($root in $roots) {
        if ($iscc) { break }
        $entries = Get-ItemProperty $root -ErrorAction SilentlyContinue |
            Where-Object { $_.DisplayName -like "Inno Setup*" -and $_.InstallLocation }
        foreach ($entry in $entries) {
            if (Try-Iscc (Join-Path $entry.InstallLocation "ISCC.exe") "registre") { break }
        }
    }
}

if (-not $iscc) {
    foreach ($base in @($env:ProgramFiles, ${env:ProgramFiles(x86)},
                        "$env:LOCALAPPDATA\Programs")) {
        if ($iscc -or -not $base) { continue }
        $dirs = Get-ChildItem -LiteralPath $base -Directory -Filter "Inno Setup*" `
            -ErrorAction SilentlyContinue | Sort-Object Name -Descending
        foreach ($dir in $dirs) {
            if (Try-Iscc (Join-Path $dir.FullName "ISCC.exe") "dossier") { break }
        }
    }
}

if (-not $iscc) {
    Write-Host "    Emplacements consultes :" -ForegroundColor Yellow
    foreach ($s in $searched) { Write-Host "      $s" -ForegroundColor DarkGray }
    Fail ("ISCC.exe est introuvable. Installez Inno Setup depuis " +
          "https://jrsoftware.org/isdl.php, ou passez -InnoSetupPath " +
          "avec le chemin complet d'ISCC.exe.")
}
Write-Host "    $iscc"

foreach ($required in @("LICENSE.txt", "INSTALL-NOTES.txt", "version.iss",
                        "assets\cryptotool.ico", "README.md")) {
    if (-not (Test-Path $required)) {
        Fail "$required est absent alors que installer.iss l'exige."
    }
}

Write-Step "Compilation de l'installateur"
& $iscc "installer.iss"
if ($LASTEXITCODE -ne 0) { Fail "La compilation Inno Setup a echoue." }

$setup = Get-ChildItem "Output\*.exe" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1

Write-Step "Termine"
if ($setup) {
    $smb = [math]::Round($setup.Length / 1MB, 1)
    Write-Host "    Installateur   : $($setup.FullName)  ($smb Mo)"
}
Write-Host "    Build portable : $DistDir\"
Write-Host ""
Write-Host ("    L'installateur n'est pas signe : SmartScreen affichera un " +
            "avertissement au") -ForegroundColor Yellow
Write-Host ("    premier lancement. C'est attendu, pas le signe d'un " +
            "probleme.") -ForegroundColor Yellow
Write-Host ""
Write-Host ("    Crypto Tool est sous GPL-3.0, PyQt6 aussi. Si vous " +
            "publiez cet installateur,") -ForegroundColor Yellow
Write-Host ("    vous devez rendre le code source correspondant " +
            "disponible sous la meme") -ForegroundColor Yellow
Write-Host ("    licence. Le plus simple : deposez l'archive des sources " +
            "de cette version a") -ForegroundColor Yellow
Write-Host ("    cote du setup.exe. Voyez LICENSE.txt.") -ForegroundColor Yellow
