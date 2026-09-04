# Crypto Tool

A desktop app for encrypting and decrypting text, with a password-protected
vault for your keys. Runs entirely offline — no accounts, no network, nothing
leaves your machine.

Windows, Linux and macOS. Interface in English or French, following your
system language.

---

## What it does

You type or paste text, pick a key, and press **Encrypt**. You get back a
block of Base64 or hex that you can paste into an email, a chat message, or a
file. Whoever has the same key pastes it back and presses **Decrypt**.

That's the whole idea. The rest of the app exists to make the keys
manageable.

### Three tabs

**Encryption** — plain text on top, encrypted text below, an algorithm
picker, and a key picker. A coloured warning appears when you select an
algorithm that isn't safe.

**Key Management** — generate random keys, name them, import existing ones,
copy them out. Keys are grouped by algorithm, up to 50 per algorithm.

**Help** — a full guide in the interface language.

### The key vault

Keys are stored encrypted, not in plain text. On first launch the app asks
you to create a **master password**. Everything in the vault is encrypted
with a key derived from it.

The master password is never stored anywhere and cannot be reset. **If you
forget it, the keys are gone**, and so is anything you encrypted with them.
Write down the keys that matter somewhere else.

You can lock the vault at any time without closing the app.

---

## Algorithms

| Algorithm | Key size | Mode | Notes |
|---|---|---|---|
| **AES-256** | 256 bits | CBC | The safe default |
| **AES-128** | 128 bits | CBC | |
| **ChaCha20** | 256 bits | stream | Fast, no padding needed |
| **Camellia-256** | 256 bits | CBC | |
| **Camellia-128** | 128 bits | CBC | |
| 3DES | 192 bits | CBC | Old, slow — legacy use only |
| Blowfish | 128 bits | CBC | Old — legacy use only |
| RC4 | 128 bits | stream | **Broken. Not secure.** |
| XOR | 128 bits | stream | **Not encryption at all.** |

Key sizes are what the app asks you to supply. 3DES is the odd one: its
24-byte key carries 168 key bits plus parity, and a meet-in-the-middle attack
brings its real strength down to about 112 bits. Another reason not to pick
it for new work.

Block ciphers use a fresh random IV for every message, prepended to the
output, with PKCS7 padding. Encrypting the same text twice therefore gives
two different results — that's expected and correct.

**Why keep the broken ones?** To read old data that was encrypted with them,
and to let people see what weak encryption looks like. The interface flags
them in red. Don't protect anything with RC4 or XOR.

---

## Security

- Master key derived with **PBKDF2-SHA256, 600,000 iterations**, over a
  random 256-bit salt
- Each stored key encrypted with **AES-256-GCM**, which detects tampering
- Keys held in memory only while the vault is unlocked
- No telemetry, no network access, no auto-update

Crypto Tool is built on the [`cryptography`](https://github.com/pyca/cryptography)
library, which is well regarded. **This particular assembly has not been
independently audited.** Don't use it for anything where exposure would
seriously harm you.

---

## Installing

### Windows

Download `CryptoTool-<version>-setup.exe` and run it. It installs for your
user account by default, so no administrator prompt.

Windows SmartScreen will warn you, because the installer isn't code-signed.
Click **More info**, then **Run anyway**.

### Running from source

Needs Python 3.10 or newer.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python crypto_tool.py
```

---

## Where your keys live

On Windows, in the registry under
`HKEY_CURRENT_USER\Software\CryptoTool\CryptoToolPro`. On Linux and macOS,
in the equivalent per-user config location.

Never in the install folder. Two useful consequences:

- Updating the app cannot wipe your keys.
- The vault belongs to your user account. A machine-wide install does **not**
  share keys between Windows accounts — each account gets its own vault.

When you uninstall, the vault is **kept by default**. The uninstaller offers
to delete it, with "No" preselected. Say yes only if you have no encrypted
data left.

---

## Building the Windows installer

Needs 64-bit Python 3.10+ and
[Inno Setup](https://jrsoftware.org/isdl.php) 6.3 or newer.

```powershell
.\build_windows.cmd              # app + installer
.\build_windows.cmd app          # portable build only
.\build_windows.cmd installer    # installer only, from an existing dist\
.\build_windows.cmd clean        # wipe build, dist and Output, then rebuild
```

Use the `.cmd`, not the `.ps1` directly — PowerShell blocks unsigned scripts
and scripts carrying the mark of the web. The launcher clears both for that
one process without changing anything on your machine.

The script sets up its own virtual environment, generates the icon and
version files, runs PyInstaller, smoke-tests the result, finds Inno Setup
without assuming a path, and compiles the installer.

Output:

| Path | Contents |
|---|---|
| `dist\CryptoTool\` | portable build, runs as-is |
| `Output\CryptoTool-<version>-setup.exe` | the installer |

To check the packaging chain without building:

```bash
python3 test_packaging.py
```

### Version numbers

`__version__` in `crypto_tool.py` is the single source of truth.
`make_version.py` derives the exe's version resource and the installer's
version defines from it, so the title bar, file properties, installer
filename and "Installed apps" entry cannot disagree. To release, change
`__version__` and rebuild.

### The icon

`make_icon.py` draws it programmatically: lines of text, the top two solid
(plain text), the lower ones broken into fragments (cipher text), with a
padlock in the corner. Each size in the `.ico` is rendered at its own
resolution rather than downscaled from one bitmap, and detail drops away as
size shrinks.

---

## Project files

```
crypto_tool.py        the application, and __version__
requirements.txt
make_icon.py          draws assets/cryptotool.ico
make_version.py       derives version_info.txt and version.iss
CryptoTool.spec       PyInstaller recipe
installer.iss         Inno Setup script
build_windows.cmd     launcher
build_windows.ps1     build chain
test_packaging.py     packaging checks
LICENSE.txt           GPL-3.0, plus third-party licences
INSTALL-NOTES.txt     shown by the installer
assets/               generated icon
```

---

## Licence

**GNU General Public License v3 or later.** Full text in `LICENSE.txt`.

This isn't just a preference: Crypto Tool links against PyQt6, whose free
version is GPL-3.0, and shipping a binary built with it puts the whole thing
under GPL-3.0. The alternative would have been a commercial Riverbank
licence.

**If you redistribute the installer or the portable build**, you must make
the corresponding source available under the same licence. The simplest way,
and it costs almost nothing, is to publish the source archive for that same
version next to your installer.

Copyright (C) 2026 F4JTV.
