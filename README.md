# Crypto Tool

Chiffrement et dechiffrement de texte avec neuf algorithmes symetriques, et
un coffre a cles protege par un mot de passe maitre. Interface PyQt6,
francais et anglais selon la locale du systeme. Aucune connexion reseau.

Logiciel libre sous **GPL-3.0 ou ulterieure**.

---

## Sommaire

- [Lancer depuis les sources](#lancer-depuis-les-sources)
- [Construire l'installateur Windows](#construire-linstallateur-windows)
- [Ce que fait le script de construction](#ce-que-fait-le-script-de-construction)
- [Numero de version](#numero-de-version)
- [L'icone](#licone)
- [L'installateur](#linstallateur)
- [Choix de conception](#choix-de-conception)
- [Depannage](#depannage)
- [Fichiers du projet](#fichiers-du-projet)

---

## Lancer depuis les sources

```bash
python -m venv .venv
source .venv/bin/activate          # Windows : .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python crypto_tool.py
```

L'icone n'existe pas tant que `make_icon.py` n'a pas tourne ; le programme
demarre quand meme, sans icone de fenetre.

---

## Construire l'installateur Windows

Il faut un **Python 3.10 ou superieur en 64 bits** et **Inno Setup 6.3 ou
superieur** (7 recommande), depuis <https://jrsoftware.org/isdl.php>.

```powershell
.\build_windows.cmd              # build complet, application + installateur
.\build_windows.cmd app          # build portable seul, sans installateur
.\build_windows.cmd installer    # installateur seul, depuis un dist\ existant
.\build_windows.cmd clean        # efface build, dist et Output puis reconstruit
```

**Utilisez le `.cmd`, pas le `.ps1` directement.** PowerShell refuse les
scripts non signes sous la strategie `AllSigned`, et refuse les scripts
portant la marque du web — ce que porte tout fichier extrait d'une archive
telechargee — sous `RemoteSigned`. Le lanceur retire cette marque et demarre
PowerShell avec `-ExecutionPolicy Bypass` **pour ce seul processus** : rien
n'est modifie sur votre machine.

Pour lancer le `.ps1` malgre tout :

```powershell
Get-ChildItem -Recurse | Unblock-File
powershell -ExecutionPolicy Bypass -File .\build_windows.ps1
```

Ou lever la strategie pour votre compte seulement, sans droits
administrateur :

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
Get-ChildItem -Recurse | Unblock-File     # toujours necessaire
```

`Get-ExecutionPolicy -List` indique quelle portee decide. Si la strategie
vient d'une strategie de groupe, `-ExecutionPolicy` est ignore et il faut
passer par les etapes manuelles ci-dessous.

### A la main

```powershell
python -m venv .venv-build
.\.venv-build\Scripts\Activate.ps1
pip install PyQt6 cryptography pyinstaller pillow
python make_icon.py
python make_version.py
pyinstaller --noconfirm --clean CryptoTool.spec
& "C:\Program Files\Inno Setup 7\ISCC.exe" installer.iss
```

### Resultats

| Chemin | Contenu |
|---|---|
| `dist\CryptoTool\` | build portable, fonctionne tel quel, rien a installer |
| `Output\CryptoTool-<version>-setup.exe` | l'installateur |

---

## Ce que fait le script de construction

`build_windows.ps1` enchaine, en s'arretant a la premiere erreur :

1. **Verifie Python** et refuse un interpreteur 32 bits, qui produirait un
   paquet incoherent avec l'installateur 64 bits.
2. **Cree `.venv-build`** et y installe PyQt6, cryptography, PyInstaller et
   Pillow. Votre Python systeme n'est jamais modifie.
3. **Genere l'icone** (`make_icon.py`) et **les fichiers de version**
   (`make_version.py`).
4. **Lance PyInstaller** sur `CryptoTool.spec`.
5. **Essaie de demarrer l'executable** avec `--version`. Un build qui ne
   demarre pas est pire que pas de build : autant s'en apercevoir ici plutot
   que chez celui qui installera. `--version` sort immediatement, sans ouvrir
   de fenetre ni toucher aux reglages.
6. **Cherche Inno Setup** sans supposer aucun chemin, puis compile
   l'installateur.

### La recherche d'Inno Setup ne suppose rien

Inno Setup 7 existe en 32 et en 64 bits, donc sous « Program Files » comme
sous « Program Files (x86) », et il peut aussi etre installe par utilisateur.
Le script interroge donc, dans l'ordre : le parametre `-InnoSetupPath`, le
`PATH`, les cles de desinstallation du registre (`InstallLocation`), puis les
dossiers `Inno Setup*` des emplacements habituels. En cas d'echec, il enumere
ce qu'il a consulte plutot que de se contenter d'un « introuvable » sans
explication.

```powershell
.\build_windows.cmd -InnoSetupPath "D:\Outils\Inno Setup 7\ISCC.exe"
```

---

## Numero de version

`__version__` dans `crypto_tool.py` est **la seule source de verite**.

`make_version.py` en derive deux fichiers, tous deux generes et jamais edites
a la main :

| Fichier | Role |
|---|---|
| `version_info.txt` | ressource de version de l'`.exe`, onglet « Details » des proprietes |
| `version.iss` | `#define AppVersion` et `#define AppVersionFull`, inclus par `installer.iss` |

Consequence : la barre de titre, les proprietes du fichier, le nom de
l'installateur et ce qu'affiche « Applications installees » ne peuvent pas
diverger. Pour publier une nouvelle version, changez `__version__` et
reconstruisez, rien d'autre.

`AppVersionFull` existe parce que la directive `VersionInfoVersion` d'Inno
Setup exige quatre nombres et rien d'autre : un `1.0.0-rc1` y provoquerait
une erreur de compilation. `AppVersion` garde la forme lisible pour
l'affichage et le nom de fichier, `AppVersionFull` vaut `1.0.0.0`.

---

## L'icone

`make_icon.py` dessine l'icone par programme. Le motif evoque du texte
chiffre : quatre lignes de texte dont les deux premieres sont pleines et
claires — le texte en clair — et les suivantes brisees en fragments de
largeurs irregulieres et teintees de vert — le texte chiffre. Un cadenas
ambre chevauche l'angle inferieur droit.

Chaque taille du `.ico` (16 a 256 px) est **rendue a sa propre resolution**
puis suréchantillonnée, et non reduite depuis un seul bitmap : reduire une
image de 256 px vers 16 px donne de la bouillie, la rendre a 16 px avec un
trait epaissi donne une forme lisible.

Le detail disparait progressivement quand la place manque :

- le cadenas sous 24 px, il ne serait plus qu'une tache indistincte ;
- la quatrieme ligne sous 24 px, l'interligne tomberait sous un pixel ;
- le trou de serrure sous 48 px.

Le cadenas et les lignes s'accrochent a **une seule grille**, calculee par
`layout()`. Le cadenas occupe exactement la hauteur des lignes 3 et 4 : bord
haut sur la ligne 3, bord bas sur la base de la ligne 4, bord droit sur la
marge. Les lignes chiffrees s'arretent avant lui. Aucune des deux formes ne
peut donc deriver par rapport a l'autre quand on retouche une valeur.

### Le raccord de l'anse

Pillow n'applique pas l'epaisseur de la meme facon a `arc()` et a `line()` :

| Appel | Ou tombe l'axe du trait |
|---|---|
| `arc(boite de rayon R, width=W)` | rayon **R - W/2**, l'epaisseur va vers l'interieur |
| `line(a la distance R, width=W)` | rayon **R**, l'epaisseur va de part et d'autre |

Passer le meme `R` aux deux, ce qui semble evident a la lecture, donne une
anse dont le sommet est plus etroit que ses montants de `W` au total, avec un
ressaut visible au raccord. `draw_lock()` compense en donnant a l'arc une
boite de rayon `R + W/2`.

Ce genre de defaut ne se voit pas dans le source, seulement dans les pixels.
`test_packaging.py` mesure donc l'epaisseur et le rayon de l'axe au sommet de
l'anse et sur les montants, et les compare. Le controle a ete verifie en
reintroduisant volontairement l'erreur : il signale alors un axe a 195 la ou
il devrait etre a 282, soit exactement la demi-epaisseur d'ecart.

Le fond ardoise, le blanc casse, le vert et l'ambre ont ete verifies sur un
Explorateur en theme clair **et** en theme sombre.

---

## L'installateur

`installer.iss` est un script Inno Setup 7, retro-compatible 6.3.

**Metadonnees de version du `setup.exe` lui-meme.** Sans les directives
`VersionInfo*`, l'onglet « Details » des proprietes de l'installateur reste
vide et il s'annonce comme un produit Inno Setup anonyme. Une page de
telechargement, un antivirus ou un deploiement automatise les lisent.

**Installation par utilisateur par defaut**, donc sans invite administrateur.
L'operateur peut choisir une installation machine sur la premiere page. Ce
choix a une consequence reelle ici : le coffre a cles vit dans la ruche de
l'utilisateur courant, donc une installation machine ne partage pas les cles
entre les comptes.

**`AppId` est un GUID fixe.** C'est ce qui permet a une mise a jour de
remplacer l'installation precedente au lieu de s'installer a cote. Ne le
changez **jamais** apres une premiere diffusion.

**`[InstallDelete]` vide `_internal` avant d'ecrire.** PyInstaller reecrit
entierement ce dossier a chaque montee de version ; sans cela une DLL
orpheline d'une version precedente pourrait survivre et etre chargee a la
place de la bonne.

### Le coffre a cles et la desinstallation

Les cles sont dans le registre, sous
`HKEY_CURRENT_USER\Software\CryptoTool\CryptoToolPro`, jamais dans le dossier
d'installation. Une mise a jour ne peut donc pas les effacer.

A la desinstallation, le coffre est **conserve par defaut**. Le
desinstalleur propose de le supprimer, avec la reponse « Non »
preselectionnee (`MB_DEFBUTTON2`) : perdre ses cles a cause d'une
desinstallation menee un peu vite serait irreversible, tout ce qui a ete
chiffre avec devenant illisible.

Les commentaires du bloc `[Code]` sont en `//` et non entre accolades. En
Pascal les commentaires `{ }` ne s'imbriquent pas : une accolade citee dans
le texte du commentaire le refermerait par surprise, et l'erreur de
compilation qui suit ne designe pas la bonne ligne.

---

## Choix de conception

**Un dossier, pas un fichier unique.** Un build onefile se decompresse dans
un dossier temporaire a chaque lancement : plusieurs secondes avec Qt, et un
declenchement frequent des heuristiques antivirus, un binaire qui
s'auto-extrait ressemblant beaucoup a un paquet malveillant. Pour un outil de
chiffrement, deja plus expose que la moyenne aux faux positifs, ce n'etait
pas un bon choix.

**UPX desactive.** Compresser les DLL Qt est une cause classique de plantages
difficiles a diagnostiquer, et aggrave encore la detection heuristique.

**Modules Qt exclus.** Le `.spec` exclut une trentaine de modules PyQt6 que
l'application ne charge jamais (WebEngine, Quick, Multimedia, 3D, Charts...),
ce qui fait passer le build d'environ 180 Mo a une petite centaine. Notez que
`excludes` ne porte que sur les modules Python : quelques bibliotheques Qt
restent presentes parce qu'elles sont des dependances des greffons de
plateforme, pas des imports.

**`cryptography.hazmat.bindings._rust` en import cache.** La bibliotheque
charge son moteur natif par un chemin que l'analyse statique ne suit pas
toujours. Le declarer coute une ligne et evite un « backend introuvable » qui
n'apparaitrait qu'apres le gel.

---

## Depannage

**« ISCC.exe est introuvable »** — le script enumere les emplacements
consultes. Si Inno Setup est installe ailleurs, passez
`-InnoSetupPath "chemin\vers\ISCC.exe"`.

**« Python 32 bits detecte »** — reinstallez Python en 64 bits. `python -c
"import struct; print(struct.calcsize('P')*8)"` doit repondre `64`.

**L'executable se termine avec un code non nul sur `--version`** — relancez
`dist\CryptoTool\CryptoTool.exe --version` a la main depuis une console pour
voir le message. C'est presque toujours un import manquant, a ajouter dans
`hiddenimports` du `.spec`.

**L'environnement virtuel est casse** — supprimez `.venv-build` et relancez.

**SmartScreen avertit au lancement** — l'installateur n'est pas signe
numeriquement. « Informations complementaires », puis « Executer quand
meme ». Signer demande un certificat de signature de code payant.

**Un antivirus met l'executable en quarantaine** — c'est un faux positif
frequent sur les outils de chiffrement empaquetes par PyInstaller. Le mode
« un dossier » et l'absence d'UPX le rendent moins probable, sans l'exclure.

### Verifier la chaine avant de construire

```bash
python3 test_packaging.py
```

Controle statiquement `installer.iss` (sections, GUID, `#if`/`#endif`,
equilibrage du bloc Pascal, fichiers references, metadonnees de version), le
`.spec`, la coherence des numeros de version, les tailles presentes dans le
`.ico`, les scripts de construction, et simule une installation gelee pour
verifier que l'icone reste trouvable une fois empaquetee.

---

## Fichiers du projet

```
CryptoTool-1.0.0\
├── crypto_tool.py           l'application, et __version__
├── requirements.txt
├── make_icon.py             icone parametrique -> assets/cryptotool.ico
├── make_version.py          version a source unique -> version_info.txt, version.iss
├── CryptoTool.spec          recette PyInstaller
├── installer.iss            script Inno Setup 7
├── build_windows.cmd        lanceur, contourne la strategie d'execution
├── build_windows.ps1        chaine de construction
├── test_packaging.py        controles de la chaine d'empaquetage
├── LICENSE.txt              GPL-3.0, et les licences des composants tiers
├── INSTALL-NOTES.txt        page d'accueil de l'installateur
├── README.md                ce fichier
└── assets/                  cryptotool.ico et .png (generes)
```

`version_info.txt`, `version.iss` et le contenu d'`assets/` sont generes ;
ils figurent dans `.gitignore`.

---

## Licence

**GNU General Public License version 3 ou ulterieure.** Le texte complet est
dans `LICENSE.txt`, avec les licences des composants tiers.

Ce n'est pas seulement une preference : Crypto Tool est lie a PyQt6, dont la
version libre est sous GPL-3.0, et distribuer un binaire construit avec elle
place l'ensemble sous GPL-3.0. La seule alternative aurait ete une licence
commerciale Riverbank.

**Si vous redistribuez l'installateur ou le build portable**, vous devez
rendre disponible le code source correspondant, sous cette meme licence.
L'article 6 decrit les facons acceptables de le faire ; la plus simple, et
elle ne coute presque rien, consiste a publier l'archive des sources de la
meme version a cote de votre installateur, et a la garder disponible aussi
longtemps que l'installateur l'est. Le script de construction vous le
rappelle a la fin.

L'avis de licence figure en tete de `crypto_tool.py`, dans la ressource de
version de l'`.exe`, dans les metadonnees de l'installateur, et s'affiche sur
`CryptoTool.exe --version`.

Aucun audit independant n'a ete mene sur cet assemblage. RC4 et XOR sont
presents pour l'interoperabilite et l'etude, jamais pour proteger quoi que ce
soit.
