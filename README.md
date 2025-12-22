# Crypto Tool

A powerful, multi-algorithm encryption and decryption desktop application with secure key management, built with PyQt6.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![PyQt6](https://img.shields.io/badge/PyQt6-6.4+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Features

- **Multiple Encryption Algorithms**: Support for 9 different encryption algorithms
- **Secure Key Storage**: Keys are encrypted with AES-256-GCM using a master password
- **Multi-language Support**: Automatic detection of system language (English/French)
- **Flexible Key Management**: Store up to 50 keys per algorithm
- **Multiple Output Formats**: Base64 and Hexadecimal encoding support
- **Cross-platform**: Works on Windows, macOS, and Linux

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Supported Algorithms](#supported-algorithms)
- [User Guide](#user-guide)
  - [Master Password](#master-password)
  - [Key Management](#key-management)
  - [Encryption](#encryption)
  - [Decryption](#decryption)
- [Security Architecture](#security-architecture)
- [Technical Specifications](#technical-specifications)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Install Dependencies

```bash
pip install PyQt6 cryptography
```

### Run the Application

```bash
python crypto_tool.py
```

### Optional: Create a Desktop Shortcut

**Windows:**
```batch
pythonw crypto_tool.py
```

**Linux/macOS:**
```bash
chmod +x crypto_tool.py
./crypto_tool.py
```

## Quick Start

1. **Launch the application** - Run `python crypto_tool.py`
2. **Create a master password** - On first launch, you'll be prompted to create a master password (minimum 8 characters)
3. **Generate a key** - Go to "Key Management" tab, select an algorithm (e.g., AES-256), and click "Generate"
4. **Encrypt text** - Switch to "Encryption" tab, select your key, enter text, and click "Encrypt"
5. **Copy the result** - The encrypted text appears in Base64 or Hex format, ready to share

## Supported Algorithms

### 🔒 Robust (Recommended)

| Algorithm | Key Size | Description |
|-----------|----------|-------------|
| **AES-128** | 128 bits | Industry standard, very fast, hardware-accelerated |
| **AES-256** | 256 bits | Maximum security AES variant, recommended for sensitive data |
| **ChaCha20** | 256 bits | Modern stream cipher, excellent performance without hardware acceleration |
| **Camellia-128** | 128 bits | ISO/NESSIE certified, AES alternative |
| **Camellia-256** | 256 bits | Enhanced Camellia with 256-bit key |

### ⚠️ Legacy (Compatibility Only)

| Algorithm | Key Size | Description |
|-----------|----------|-------------|
| **3DES** | 192 bits | Triple DES, still used in banking systems |
| **Blowfish** | 128 bits | 1990s algorithm, predecessor to Twofish |

### ⛔ Weak (Not Recommended)

| Algorithm | Key Size | Description |
|-----------|----------|-------------|
| **RC4** | 128 bits | Known vulnerabilities, used in WEP/early WPA |
| **XOR** | 128 bits | Trivial cipher, for educational purposes only |

## User Guide

### Master Password

The master password protects all your encryption keys. It is used to derive a strong encryption key via PBKDF2-SHA256 with 600,000 iterations.

**Important considerations:**
- Minimum length: 8 characters
- Use a strong, unique password
- **If you forget your master password, all keys are permanently lost**
- The password is never stored; only a verification hash is kept

**Changing your master password:**
1. Go to "Key Management" tab
2. Click "Change password"
3. Enter your old password
4. Enter and confirm your new password

### Key Management

#### Creating Keys

**Generate a random key:**
1. Select an algorithm from the list
2. Click "Generate"
3. Enter a descriptive name (e.g., "Work Backup 2024")
4. The key is automatically generated and saved

**Import an existing key:**
1. Select an algorithm
2. Click "Add"
3. Enter a name for the key
4. Paste the key in Base64 or Hex format (depending on current display setting)

#### Managing Keys

- **Rename**: Select a key and click "Rename" or right-click → Rename
- **Delete**: Select a key and click "Delete" or right-click → Delete
- **Copy**: Right-click on a key → Copy (copies to clipboard)

#### Key Limits

- Maximum 50 keys per algorithm
- Keys are stored encrypted in system settings
- Key names must be unique within an algorithm

### Encryption

1. Go to the "Encryption" tab
2. Select the desired algorithm from the dropdown
3. Select the key to use
4. Choose output format (Base64 or Hex)
5. Enter or paste your plain text in the upper text area
6. Click "Encrypt"
7. The encrypted result appears in the lower text area

### Decryption

1. Go to the "Encryption" tab
2. Select the **same algorithm** used for encryption
3. Select the **same key** used for encryption
4. Set the format to match the encrypted text (Base64 or Hex)
5. Paste the encrypted text in the lower text area
6. Click "Decrypt"
7. The decrypted text appears in the upper text area

**Common decryption errors:**
- Wrong key selected
- Wrong algorithm selected
- Wrong format (Base64 vs Hex)
- Corrupted or truncated ciphertext

## Security Architecture

### Key Derivation

```
Master Password → PBKDF2-SHA256 (600,000 iterations) → 256-bit Master Key
```

### Key Storage Encryption

```
Encryption Key + Random Salt → AES-256-GCM → Encrypted Key Blob
```

**Components:**
- **Salt**: 256 bits, randomly generated per installation
- **IV/Nonce**: 96 bits, randomly generated per encryption
- **Authentication Tag**: 128 bits, ensures integrity

### Encryption Modes

| Algorithm | Mode | IV Size | Padding |
|-----------|------|---------|---------|
| AES-128/256 | CBC | 128 bits | PKCS7 |
| Camellia-128/256 | CBC | 128 bits | PKCS7 |
| 3DES | CBC | 64 bits | PKCS7 |
| Blowfish | CBC | 64 bits | PKCS7 |
| ChaCha20 | Stream | 128 bits | None |
| RC4 | Stream | None | None |
| XOR | Stream | None | None |

### Data Format

Encrypted output structure:
```
[IV/Nonce][Ciphertext] → Base64 or Hex encoding
```

## Technical Specifications

### Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| PyQt6 | ≥ 6.4.0 | GUI framework |
| cryptography | ≥ 41.0.0 | Cryptographic primitives |

### Storage Locations

| Platform | Location |
|----------|----------|
| Windows | Registry: `HKEY_CURRENT_USER\Software\CryptoTool` |
| macOS | `~/Library/Preferences/com.cryptotool.plist` |
| Linux | `~/.config/CryptoTool/CryptoToolPro.conf` |

### System Requirements

- **OS**: Windows 10+, macOS 10.14+, Linux (X11 or Wayland)
- **Python**: 3.8 or higher
- **RAM**: 50 MB minimum
- **Disk**: 10 MB for application + keys storage

## Troubleshooting

### "Wrong password" on startup

- Ensure Caps Lock is off
- Try typing your password in a text editor first to verify
- If you've forgotten your password, you must delete the settings and start fresh (all keys will be lost)

**Reset settings:**
- Windows: Delete registry key `HKEY_CURRENT_USER\Software\CryptoTool`
- macOS: `rm ~/Library/Preferences/com.cryptotool.plist`
- Linux: `rm ~/.config/CryptoTool/CryptoToolPro.conf`

### Decryption fails

1. Verify you're using the exact same key
2. Verify you're using the exact same algorithm
3. Check that the format (Base64/Hex) matches
4. Ensure the ciphertext wasn't truncated or modified

### Application won't start

1. Verify Python version: `python --version` (must be 3.8+)
2. Reinstall dependencies: `pip install --upgrade PyQt6 cryptography`
3. Check for error messages in terminal

### Keys not showing

1. Make sure the vault is unlocked (status bar should show "Vault unlocked" in green)
2. Select an algorithm from the list
3. If vault is locked, enter your master password to unlock

## Command Line Arguments

Currently, the application does not support command-line arguments. All operations are performed through the GUI.

## Building Standalone Executables

### Windows (PyInstaller)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "CryptoTool" crypto_tool.py
```

### macOS (py2app)

```bash
pip install py2app
python setup.py py2app
```

### Linux (AppImage)

Use tools like `appimage-builder` or `pyinstaller` to create portable executables.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin feature/my-feature`
5. Submit a Pull Request

### Code Style

- Follow PEP 8 guidelines
- Use type hints where possible
- Add docstrings to new functions and classes
- Update translations for new UI strings

### Adding a New Language

1. Add a new entry to the `TRANSLATIONS` dictionary in `crypto_tool.py`
2. Copy all keys from the English (`'en'`) translation
3. Translate all values to the target language
4. The language will be automatically detected based on system locale

## Security Considerations

- **This software is provided as-is** for educational and personal use
- **Do not use weak algorithms** (RC4, XOR) for sensitive data
- **Backup your keys** - if you lose your master password, keys cannot be recovered
- **The application does not transmit any data** - all operations are local
- **Keys are stored encrypted** but physical access to the machine could allow extraction

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - GUI framework
- [cryptography](https://cryptography.io/) - Cryptographic library
- [Python](https://www.python.org/) - Programming language

## Changelog

### Version 1.0.0

- Initial release
- Support for 9 encryption algorithms
- Secure key storage with master password
- Multi-language support (English, French)
- Base64 and Hexadecimal encoding
- Up to 50 keys per algorithm

---

**⚠️ Disclaimer**: This software is provided for educational and personal use. The authors are not responsible for any misuse or data loss. Always backup important data and keys.
