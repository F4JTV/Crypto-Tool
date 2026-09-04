; ===========================================================================
;  Installateur Crypto Tool  -  Inno Setup 6.3 ou superieur (7 recommande)
;
;  Construire l'application d'abord :
;      python make_icon.py
;      python make_version.py
;      pyinstaller --noconfirm --clean CryptoTool.spec
;
;  Puis compiler ce script :
;      "C:\Program Files (x86)\Inno Setup 7\ISCC.exe" installer.iss
;  ou l'ouvrir dans l'IDE du compilateur et appuyer sur F9.
;
;  build_windows.ps1 enchaine tout cela automatiquement.
;
;  Sortie : Output\CryptoTool-<version>-setup.exe
;
;  Notes sur Inno Setup 7 :
;    - SetupArchitecture est nouveau en 7. Le mettre a x64 produit un
;      installateur 64 bits et change les valeurs par defaut de
;      ArchitecturesAllowed et ArchitecturesInstallIn64BitMode. Les deux
;      sont declarees explicitement ci-dessous pour que le script reste
;      correct sous Inno Setup 6, ou SetupArchitecture est inconnu et
;      simplement ignore.
;    - x64compatible remplace l'ancien identifiant x64, deprecie en 6.3. Il
;      couvre le x64 et l'ARM64 executant du x64 en emulation, ce dont un
;      build PyInstaller x64 a effectivement besoin.
; ===========================================================================

#define AppName        "Crypto Tool"
#define AppShortName   "CryptoTool"
#define AppPublisher   "F4JTV"
#define AppExeName     "CryptoTool.exe"
#define AppURL         "https://github.com/F4JTV"
#define SourceDir      "dist\CryptoTool"

; AppVersion et AppVersionFull sont produits par make_version.py depuis
; __version__ dans crypto_tool.py. L'installateur ne peut donc pas annoncer
; une version differente de celle du binaire qu'il empaquette.
#include "version.iss"

[Setup]
; Un AppId stable est ce qui permet a une mise a jour de remplacer
; l'installation precedente au lieu de s'installer a cote. Cette valeur ne
; doit JAMAIS changer apres une premiere diffusion.
AppId={{2F8D4C17-6B3E-4A95-9E27-5C1A0F73D8B6}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}

DefaultDirName={autopf}\{#AppShortName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName} {#AppVersion}

; --- metadonnees de version du setup.exe lui-meme ------------------------
; Sans ces directives, l'onglet « Details » des proprietes de l'installateur
; reste vide et il s'annonce comme un produit Inno Setup anonyme. Une page
; de telechargement, un antivirus ou un deploiement automatise les lisent.
; VersionInfoVersion exige quatre nombres, d'ou AppVersionFull.
VersionInfoVersion={#AppVersionFull}
VersionInfoProductVersion={#AppVersionFull}
VersionInfoProductTextVersion={#AppVersion}
VersionInfoCompany={#AppPublisher}
VersionInfoProductName={#AppName}
VersionInfoDescription={#AppName} {#AppVersion} - programme d'installation
VersionInfoCopyright=Copyright (C) 2026 F4JTV. GPL-3.0 ou ulterieure.
VersionInfoOriginalFileName={#AppShortName}-{#AppVersion}-setup.exe

; Installateur 64 bits, en accord avec un Python et un PyInstaller 64 bits.
SetupArchitecture=x64
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; Installation par utilisateur par defaut, donc sans invite administrateur.
; L'operateur peut toujours choisir une installation machine sur la premiere
; page. Ce choix a une consequence reelle ici : le coffre a cles vit dans la
; ruche de l'utilisateur courant, donc une installation machine ne partage
; pas les cles entre comptes.
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

OutputDir=Output
OutputBaseFilename={#AppShortName}-{#AppVersion}-setup
SetupIconFile=assets\cryptotool.ico
WizardStyle=modern
Compression=lzma2/max
SolidCompression=yes
LicenseFile=LICENSE.txt
InfoBeforeFile=INSTALL-NOTES.txt
AllowNoIcons=yes

; Une mise a jour par-dessus une instance en cours d'execution echoue avec un
; fichier verrouille. Mieux vaut la fermer proprement et la relancer.
CloseApplications=yes
RestartApplications=yes

[Languages]
Name: "french";  MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
french.LaunchAfter=Lancer %1
french.PurgeVault=Supprimer aussi le coffre a cles
english.LaunchAfter=Launch %1
english.PurgeVault=Also delete the key vault

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
    GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; \
    Flags: ignoreversion recursesubdirs createallsubdirs
Source: "LICENSE.txt";        DestDir: "{app}"; Flags: ignoreversion
Source: "README.md";          DestDir: "{app}"; Flags: ignoreversion
Source: "INSTALL-NOTES.txt";  DestDir: "{app}"; Flags: ignoreversion

[InstallDelete]
; PyInstaller reecrit entierement _internal a chaque montee de version. Le
; vider avant d'ecrire evite qu'une DLL orpheline d'une version precedente
; survive et soit chargee a la place de la bonne.
Type: filesandordirs; Name: "{app}\_internal"

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; \
    Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; \
    Description: "{cm:LaunchAfter,{#AppName}}"; \
    Flags: nowait postinstall skipifsilent

[UninstallDelete]
; PyInstaller et Python laissent des __pycache__ que l'installateur n'a pas
; deposes : sans cela le dossier survivrait a la desinstallation.
Type: filesandordirs; Name: "{app}\_internal"
Type: dirifempty;     Name: "{app}"

[Code]
//  Le coffre a cles n'est pas dans le dossier d'installation : QSettings
//  l'ecrit dans HKCU\Software\CryptoTool\CryptoToolPro. Le desinstalleur ne
//  le touche donc pas par accident, ce qui est le bon comportement par
//  defaut : perdre ses cles a cause d'une mise a jour mal menee serait une
//  perte irreversible, les donnees chiffrees avec devenant illisibles.
//
//  On propose quand meme la suppression, sans la cocher : quelqu'un qui
//  desinstalle pour de bon a le droit de ne pas laisser trainer un coffre.
//
//  Les commentaires de ce bloc sont en // et non entre accolades : en
//  Pascal les commentaires { } ne s'imbriquent pas, et une accolade citee
//  dans le texte refermerait le commentaire par surprise.

const
  VaultKey = 'Software\CryptoTool\CryptoToolPro';

function VaultExists(): Boolean;
begin
  Result := RegKeyExists(HKEY_CURRENT_USER, VaultKey);
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  Message: String;
begin
  if CurUninstallStep <> usPostUninstall then
    Exit;
  if not VaultExists() then
    Exit;

  Message :=
    'Vos cles de chiffrement enregistrees sont conservees.' + #13#10#13#10 +
    'Voulez-vous egalement les supprimer definitivement ?' + #13#10#13#10 +
    'Attention : sans ces cles, tout ce que vous avez chiffre avec elles ' +
    'sera definitivement illisible. Repondez Non si vous comptez ' +
    'reinstaller le programme ou si vous conservez des donnees chiffrees.';

  if MsgBox(Message, mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
  begin
    if RegDeleteKeyIncludingSubkeys(HKEY_CURRENT_USER, VaultKey) then
      RegDeleteKeyIfEmpty(HKEY_CURRENT_USER, 'Software\CryptoTool')
    else
      MsgBox('Le coffre a cles n''a pas pu etre supprime.',
             mbError, MB_OK);
  end;
end;
