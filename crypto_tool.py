#!/usr/bin/env python3
"""
Outil de chiffrement/déchiffrement avancé avec interface PyQt6
Supporte: AES-128, AES-256, ChaCha20, 3DES, Blowfish, Camellia, RC4, XOR
Stockage sécurisé des clés avec chiffrement maître
"""

import sys
import os
import base64
import secrets
import locale
from typing import Optional, Dict, List
from enum import Enum

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QComboBox,
    QGroupBox, QMessageBox, QTabWidget, QFormLayout,
    QSplitter, QDialog, QDialogButtonBox, QListWidget,
    QListWidgetItem, QInputDialog, QCheckBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMenu
)
from PyQt6.QtCore import Qt, QSettings, QLocale
from PyQt6.QtGui import QFont

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


# =============================================================================
# TRADUCTIONS
# =============================================================================

TRANSLATIONS = {
    'fr': {
        'app_title': 'Crypto Tool',
        'tab_encryption': 'Chiffrement',
        'tab_keys': 'Gestion des clés',
        'tab_help': 'Aide',
        'status_locked': 'Coffre verrouillé',
        'status_unlocked': 'Coffre déverrouillé',
        'algorithm': 'Algorithme',
        'key': 'Clé',
        'format': 'Format',
        'display_format': "Format d'affichage",
        'plain_text': 'Texte en clair',
        'cipher_text': 'Texte chiffré',
        'encrypt': 'Chiffrer',
        'decrypt': 'Déchiffrer',
        'clear': 'Effacer',
        'algorithms': 'Algorithmes',
        'keys_max': 'Clés (max 50 par algorithme)',
        'add': 'Ajouter',
        'generate': 'Générer',
        'delete': 'Supprimer',
        'rename': 'Renommer',
        'copy': 'Copier',
        'lock_vault': 'Verrouiller le coffre',
        'change_password': 'Changer mot de passe',
        'master_password': 'Mot de passe maître',
        'create_master_password': 'Créer un mot de passe maître',
        'password': 'Mot de passe',
        'confirmation': 'Confirmation',
        'show_password': 'Afficher le mot de passe',
        'welcome': 'Bienvenue',
        'welcome_msg': 'Bienvenue dans Crypto Tool!\n\nCréez un mot de passe maître.',
        'create_master_msg': "Créez un mot de passe maître pour sécuriser vos clés.\nCe mot de passe sera demandé à chaque démarrage.\n\nSi vous l'oubliez, vos clés seront perdues !",
        'error': 'Erreur',
        'warning': 'Attention',
        'info': 'Info',
        'ok': 'OK',
        'min_8_chars': 'Minimum 8 caractères.',
        'passwords_no_match': 'Les mots de passe ne correspondent pas.',
        'wrong_password': 'Mot de passe incorrect.',
        'attempts_left': 'essai(s) restant(s).',
        'vault_locked_warning': 'Le coffre reste verrouillé.\nVous ne pouvez pas accéder aux clés.',
        'password_changed': 'Mot de passe changé.',
        'old_password': 'Ancien mot de passe',
        'old_password_wrong': 'Ancien mot de passe incorrect.',
        'key_name': 'Nom de la clé',
        'key_name_prompt': 'Nom de la clé:',
        'new_name': 'Nouveau nom:',
        'name_exists': 'Ce nom existe déjà.',
        'max_keys': 'Max {} clés.',
        'no_key_selected': 'Aucune clé sélectionnée.\nAllez dans "Gestion des clés".',
        'cannot_retrieve_key': 'Impossible de récupérer la clé.',
        'key_in_format': 'Clé en {}:',
        'wrong_size': 'Taille incorrecte: {} vs {}',
        'confirm_delete': 'Confirmer',
        'confirm_delete_key': "Supprimer '{}' ?",
        'robust': 'Robuste',
        'not_recommended': 'Non recommandé',
        'size': 'Taille',
        'bytes': 'octets',
        'bits': 'bits',
        'no_key': '(Aucune clé)',
        'weak_warning': 'ATTENTION: {} est FAIBLE. Ne pas utiliser pour des données sensibles.',
        'legacy_warning': 'Note: {} est un algorithme legacy. Préférez AES/ChaCha20.',
        'decrypt_error': "Déchiffrement impossible.\n\nVérifiez:\n- Clé correcte\n- Algorithme correct\n- Format correct\n\n{}",
        'cat_robust': 'Robustes (recommandés)',
        'cat_legacy': 'Legacy (compatibilité)',
        'cat_weak': 'Faibles (non recommandés)',
        'help_title': "Crypto Tool - Guide d'utilisation",
        'help_intro': "Crypto Tool est une application de chiffrement/déchiffrement multi-algorithmes avec stockage sécurisé des clés.",
        'help_quickstart': 'Démarrage rapide',
        'help_quickstart_content': '''
            <ol>
                <li><b>Premier lancement:</b> Créez un mot de passe maître (minimum 8 caractères). Ce mot de passe protège toutes vos clés.</li>
                <li><b>Créer une clé:</b> Allez dans "Gestion des clés", sélectionnez un algorithme, puis cliquez sur "Générer".</li>
                <li><b>Chiffrer:</b> Dans l'onglet "Chiffrement", sélectionnez l'algorithme et la clé, entrez votre texte, cliquez sur "Chiffrer".</li>
                <li><b>Déchiffrer:</b> Collez le texte chiffré, sélectionnez la même clé et le même algorithme, cliquez sur "Déchiffrer".</li>
            </ol>
        ''',
        'help_algorithms': 'Algorithmes disponibles',
        'help_algo_details': '''
            <h4>🔒 Robustes (recommandés pour usage sécurisé)</h4>
            <ul>
                <li><b>AES-128:</b> Standard de chiffrement avancé avec clé de 128 bits. Très sécurisé et rapide.</li>
                <li><b>AES-256:</b> Version renforcée d'AES avec clé de 256 bits. Recommandé pour données très sensibles.</li>
                <li><b>ChaCha20:</b> Algorithme moderne par flux, excellent sur mobile et sans accélération matérielle.</li>
                <li><b>Camellia-128/256:</b> Alternative à AES certifiée ISO/NESSIE, populaire au Japon.</li>
            </ul>
            <h4>⚠️ Legacy (compatibilité uniquement)</h4>
            <ul>
                <li><b>3DES:</b> Triple DES, prédécesseur d'AES. Lent mais encore présent dans les systèmes bancaires.</li>
                <li><b>Blowfish:</b> Algorithme des années 90, remplacé par son successeur Twofish.</li>
            </ul>
            <h4>⛔ Faibles (non recommandés)</h4>
            <ul>
                <li><b>RC4:</b> Vulnérabilités connues (attaques sur WEP/WPA). À éviter absolument.</li>
                <li><b>XOR:</b> Chiffrement trivial par ou-exclusif. Uniquement pour tests/démonstrations.</li>
            </ul>
        ''',
        'help_key_management': 'Gestion des clés',
        'help_key_content': '''
            <ul>
                <li><b>Ajouter:</b> Importez une clé existante en Base64 ou Hexadécimal.</li>
                <li><b>Générer:</b> Créez une clé aléatoire cryptographiquement sécurisée.</li>
                <li><b>Renommer:</b> Changez le nom d'une clé pour mieux l'identifier.</li>
                <li><b>Supprimer:</b> Supprimez définitivement une clé (action irréversible).</li>
                <li><b>Copier:</b> Clic droit sur une clé pour la copier dans le presse-papiers.</li>
            </ul>
            <p><b>Limite:</b> 50 clés maximum par algorithme.</p>
        ''',
        'help_formats': "Formats d'encodage",
        'help_formats_content': '''
            <ul>
                <li><b>Base64:</b> Encodage compact utilisant A-Z, a-z, 0-9, +, /. Idéal pour transmission par email ou web.</li>
                <li><b>Hexadécimal:</b> Représentation en caractères 0-9 et A-F. Plus lisible, utile pour le debug.</li>
            </ul>
        ''',
        'help_security': 'Sécurité',
        'help_security_content': '''
            <p>Vos clés sont protégées par plusieurs couches de sécurité:</p>
            <ul>
                <li><b>PBKDF2-SHA256:</b> 600 000 itérations pour dériver la clé maître du mot de passe.</li>
                <li><b>AES-256-GCM:</b> Chiffrement authentifié des clés stockées.</li>
                <li><b>Sel aléatoire:</b> 256 bits générés cryptographiquement pour chaque installation.</li>
                <li><b>Verrouillage automatique:</b> Le coffre se verrouille à la fermeture de l'application.</li>
            </ul>
            <p><b>⚠️ Important:</b> Si vous oubliez votre mot de passe maître, vos clés seront perdues définitivement.</p>
        ''',
        'help_tips': 'Conseils pratiques',
        'help_tips_content': '''
            <ul>
                <li>Utilisez AES-256 ou ChaCha20 pour les données sensibles.</li>
                <li>Conservez une copie de vos clés importantes dans un endroit sûr.</li>
                <li>Utilisez des noms de clés descriptifs (ex: "Backup 2024", "Communication Alice").</li>
                <li>Vérifiez toujours que vous utilisez la bonne clé et le bon algorithme pour déchiffrer.</li>
                <li>Le format d'encodage doit être identique pour chiffrer et déchiffrer.</li>
            </ul>
        ''',
        'help_technical': 'Détails techniques',
        'help_technical_content': '''
            <ul>
                <li>Mode de chiffrement: CBC pour AES/Camellia/3DES/Blowfish, flux pour ChaCha20/RC4.</li>
                <li>Padding: PKCS7 pour les algorithmes par blocs.</li>
                <li>IV/Nonce: Généré aléatoirement et préfixé au texte chiffré.</li>
                <li>Stockage: QSettings (registre Windows / fichier de config Linux/macOS).</li>
            </ul>
        ''',
        'help_robust': 'Robustes:',
        'help_legacy': 'Legacy:',
        'help_weak': 'Faibles:',
        'help_storage_security': 'Sécurité du stockage',
        'help_storage_desc': 'Les clés sont protégées par:',
        'help_base64': 'Compact, idéal pour transmission',
        'help_hex': 'Lisible, debug',
        'help_limits': 'Limites',
        'help_max_keys': '50 clés maximum par algorithme',
    },
    'en': {
        'app_title': 'Crypto Tool',
        'tab_encryption': 'Encryption',
        'tab_keys': 'Key Management',
        'tab_help': 'Help',
        'status_locked': 'Vault locked',
        'status_unlocked': 'Vault unlocked',
        'algorithm': 'Algorithm',
        'key': 'Key',
        'format': 'Format',
        'display_format': 'Display format',
        'plain_text': 'Plain text',
        'cipher_text': 'Cipher text',
        'encrypt': 'Encrypt',
        'decrypt': 'Decrypt',
        'clear': 'Clear',
        'algorithms': 'Algorithms',
        'keys_max': 'Keys (max 50 per algorithm)',
        'add': 'Add',
        'generate': 'Generate',
        'delete': 'Delete',
        'rename': 'Rename',
        'copy': 'Copy',
        'lock_vault': 'Lock vault',
        'change_password': 'Change password',
        'master_password': 'Master password',
        'create_master_password': 'Create master password',
        'password': 'Password',
        'confirmation': 'Confirmation',
        'show_password': 'Show password',
        'welcome': 'Welcome',
        'welcome_msg': 'Welcome to Crypto Tool!\n\nCreate a master password.',
        'create_master_msg': "Create a master password to secure your keys.\nThis password will be required at each startup.\n\nIf you forget it, your keys will be lost!",
        'error': 'Error',
        'warning': 'Warning',
        'info': 'Info',
        'ok': 'OK',
        'min_8_chars': 'Minimum 8 characters.',
        'passwords_no_match': 'Passwords do not match.',
        'wrong_password': 'Wrong password.',
        'attempts_left': 'attempt(s) left.',
        'vault_locked_warning': 'The vault remains locked.\nYou cannot access the keys.',
        'password_changed': 'Password changed.',
        'old_password': 'Old password',
        'old_password_wrong': 'Old password incorrect.',
        'key_name': 'Key name',
        'key_name_prompt': 'Key name:',
        'new_name': 'New name:',
        'name_exists': 'This name already exists.',
        'max_keys': 'Max {} keys.',
        'no_key_selected': 'No key selected.\nGo to "Key Management".',
        'cannot_retrieve_key': 'Cannot retrieve key.',
        'key_in_format': 'Key in {}:',
        'wrong_size': 'Wrong size: {} vs {}',
        'confirm_delete': 'Confirm',
        'confirm_delete_key': "Delete '{}'?",
        'robust': 'Robust',
        'not_recommended': 'Not recommended',
        'size': 'Size',
        'bytes': 'bytes',
        'bits': 'bits',
        'no_key': '(No key)',
        'weak_warning': 'WARNING: {} is WEAK. Do not use for sensitive data.',
        'legacy_warning': 'Note: {} is a legacy algorithm. Prefer AES/ChaCha20.',
        'decrypt_error': "Decryption failed.\n\nCheck:\n- Correct key\n- Correct algorithm\n- Correct format\n\n{}",
        'cat_robust': 'Robust (recommended)',
        'cat_legacy': 'Legacy (compatibility)',
        'cat_weak': 'Weak (not recommended)',
        'help_title': 'Crypto Tool - User Guide',
        'help_intro': 'Crypto Tool is a multi-algorithm encryption/decryption application with secure key storage.',
        'help_quickstart': 'Quick Start',
        'help_quickstart_content': '''
            <ol>
                <li><b>First launch:</b> Create a master password (minimum 8 characters). This password protects all your keys.</li>
                <li><b>Create a key:</b> Go to "Key Management", select an algorithm, then click "Generate".</li>
                <li><b>Encrypt:</b> In the "Encryption" tab, select the algorithm and key, enter your text, click "Encrypt".</li>
                <li><b>Decrypt:</b> Paste the encrypted text, select the same key and algorithm, click "Decrypt".</li>
            </ol>
        ''',
        'help_algorithms': 'Available Algorithms',
        'help_algo_details': '''
            <h4>🔒 Robust (recommended for secure use)</h4>
            <ul>
                <li><b>AES-128:</b> Advanced Encryption Standard with 128-bit key. Very secure and fast.</li>
                <li><b>AES-256:</b> Enhanced AES with 256-bit key. Recommended for highly sensitive data.</li>
                <li><b>ChaCha20:</b> Modern stream cipher, excellent on mobile and without hardware acceleration.</li>
                <li><b>Camellia-128/256:</b> AES alternative certified by ISO/NESSIE, popular in Japan.</li>
            </ul>
            <h4>⚠️ Legacy (compatibility only)</h4>
            <ul>
                <li><b>3DES:</b> Triple DES, predecessor of AES. Slow but still present in banking systems.</li>
                <li><b>Blowfish:</b> 1990s algorithm, replaced by its successor Twofish.</li>
            </ul>
            <h4>⛔ Weak (not recommended)</h4>
            <ul>
                <li><b>RC4:</b> Known vulnerabilities (WEP/WPA attacks). Avoid at all costs.</li>
                <li><b>XOR:</b> Trivial exclusive-or encryption. Only for tests/demonstrations.</li>
            </ul>
        ''',
        'help_key_management': 'Key Management',
        'help_key_content': '''
            <ul>
                <li><b>Add:</b> Import an existing key in Base64 or Hexadecimal format.</li>
                <li><b>Generate:</b> Create a cryptographically secure random key.</li>
                <li><b>Rename:</b> Change a key's name for better identification.</li>
                <li><b>Delete:</b> Permanently delete a key (irreversible action).</li>
                <li><b>Copy:</b> Right-click on a key to copy it to clipboard.</li>
            </ul>
            <p><b>Limit:</b> 50 keys maximum per algorithm.</p>
        ''',
        'help_formats': 'Encoding Formats',
        'help_formats_content': '''
            <ul>
                <li><b>Base64:</b> Compact encoding using A-Z, a-z, 0-9, +, /. Ideal for email or web transmission.</li>
                <li><b>Hexadecimal:</b> Representation using 0-9 and A-F characters. More readable, useful for debugging.</li>
            </ul>
        ''',
        'help_security': 'Security',
        'help_security_content': '''
            <p>Your keys are protected by multiple security layers:</p>
            <ul>
                <li><b>PBKDF2-SHA256:</b> 600,000 iterations to derive the master key from your password.</li>
                <li><b>AES-256-GCM:</b> Authenticated encryption for stored keys.</li>
                <li><b>Random salt:</b> 256 bits cryptographically generated for each installation.</li>
                <li><b>Auto-lock:</b> The vault locks automatically when the application closes.</li>
            </ul>
            <p><b>⚠️ Important:</b> If you forget your master password, your keys will be permanently lost.</p>
        ''',
        'help_tips': 'Practical Tips',
        'help_tips_content': '''
            <ul>
                <li>Use AES-256 or ChaCha20 for sensitive data.</li>
                <li>Keep a backup copy of your important keys in a safe place.</li>
                <li>Use descriptive key names (e.g., "Backup 2024", "Communication Alice").</li>
                <li>Always verify you're using the correct key and algorithm for decryption.</li>
                <li>The encoding format must be identical for encryption and decryption.</li>
            </ul>
        ''',
        'help_technical': 'Technical Details',
        'help_technical_content': '''
            <ul>
                <li>Encryption mode: CBC for AES/Camellia/3DES/Blowfish, stream for ChaCha20/RC4.</li>
                <li>Padding: PKCS7 for block ciphers.</li>
                <li>IV/Nonce: Randomly generated and prefixed to ciphertext.</li>
                <li>Storage: QSettings (Windows registry / Linux/macOS config file).</li>
            </ul>
        ''',
        'help_robust': 'Robust:',
        'help_legacy': 'Legacy:',
        'help_weak': 'Weak:',
        'help_storage_security': 'Storage Security',
        'help_storage_desc': 'Keys are protected by:',
        'help_base64': 'Compact, ideal for transmission',
        'help_hex': 'Readable, debug',
        'help_limits': 'Limits',
        'help_max_keys': '50 keys maximum per algorithm',
    }
}


def get_system_language() -> str:
    """Détecte la langue du système"""
    try:
        # Essaye QLocale d'abord
        qt_locale = QLocale.system().name()[:2].lower()
        if qt_locale in TRANSLATIONS:
            return qt_locale
    except:
        pass
    
    try:
        # Fallback sur locale
        sys_locale = locale.getdefaultlocale()[0]
        if sys_locale:
            lang = sys_locale[:2].lower()
            if lang in TRANSLATIONS:
                return lang
    except:
        pass
    
    return 'en'


class Tr:
    """Classe de traduction"""
    _lang = 'en'
    
    @classmethod
    def set_language(cls, lang: str):
        cls._lang = lang if lang in TRANSLATIONS else 'en'
    
    @classmethod
    def get(cls, key: str) -> str:
        return TRANSLATIONS.get(cls._lang, TRANSLATIONS['en']).get(key, key)


def tr(key: str) -> str:
    """Raccourci pour les traductions"""
    return Tr.get(key)


# =============================================================================
# CLASSES MÉTIER
# =============================================================================

class DisplayFormat(Enum):
    BASE64 = "Base64"
    HEX = "Hex"


class Algorithm(Enum):
    AES_128 = ("AES-128", 16, True)
    AES_256 = ("AES-256", 32, True)
    CHACHA20 = ("ChaCha20", 32, True)
    CAMELLIA_128 = ("Camellia-128", 16, True)
    CAMELLIA_256 = ("Camellia-256", 32, True)
    TRIPLE_DES = ("3DES", 24, False)
    BLOWFISH = ("Blowfish", 16, False)
    RC4 = ("RC4", 16, False)
    XOR = ("XOR", 16, False)
    
    def __init__(self, display_name: str, key_size: int, is_robust: bool):
        self.display_name = display_name
        self.key_size = key_size
        self.is_robust = is_robust
    
    @classmethod
    def get_categories(cls) -> Dict[str, List['Algorithm']]:
        return {
            tr('cat_robust'): [a for a in cls if a.is_robust],
            tr('cat_legacy'): [cls.TRIPLE_DES, cls.BLOWFISH],
            tr('cat_weak'): [cls.RC4, cls.XOR]
        }


class DataEncoder:
    @staticmethod
    def encode(data: bytes, fmt: DisplayFormat) -> str:
        if fmt == DisplayFormat.BASE64:
            return base64.b64encode(data).decode('ascii')
        return data.hex().upper()
    
    @staticmethod
    def decode(text: str, fmt: DisplayFormat) -> bytes:
        text = text.strip()
        if fmt == DisplayFormat.BASE64:
            return base64.b64decode(text)
        return bytes.fromhex(text.replace(' ', '').replace('\n', ''))


class SecureKeyStorage:
    def __init__(self, settings: QSettings):
        self.settings = settings
        self._master_key: Optional[bytes] = None
        self._salt: Optional[bytes] = None
    
    def is_initialized(self) -> bool:
        return self.settings.value("master/salt") is not None
    
    def is_unlocked(self) -> bool:
        return self._master_key is not None
    
    def initialize(self, master_password: str) -> bool:
        self._salt = secrets.token_bytes(32)
        self._master_key = self._derive_key(master_password, self._salt)
        self.settings.setValue("master/salt", base64.b64encode(self._salt).decode())
        verifier = self._encrypt_data(b"VERIFY_OK", self._master_key)
        self.settings.setValue("master/verifier", verifier)
        self.settings.sync()
        return True
    
    def unlock(self, master_password: str) -> bool:
        salt_b64 = self.settings.value("master/salt")
        if not salt_b64:
            return False
        self._salt = base64.b64decode(salt_b64)
        self._master_key = self._derive_key(master_password, self._salt)
        verifier = self.settings.value("master/verifier")
        if verifier:
            try:
                if self._decrypt_data(verifier, self._master_key) == b"VERIFY_OK":
                    return True
            except Exception:
                pass
        self._master_key = None
        return False
    
    def lock(self):
        self._master_key = None
    
    def change_master_password(self, old_password: str, new_password: str) -> bool:
        if not self.unlock(old_password):
            return False
        all_keys = {}
        for algo in Algorithm:
            keys = self.get_keys(algo)
            if keys:
                all_keys[algo] = keys
        self._salt = secrets.token_bytes(32)
        self._master_key = self._derive_key(new_password, self._salt)
        self.settings.setValue("master/salt", base64.b64encode(self._salt).decode())
        verifier = self._encrypt_data(b"VERIFY_OK", self._master_key)
        self.settings.setValue("master/verifier", verifier)
        for algo, keys in all_keys.items():
            for name, key_data in keys.items():
                self.save_key(algo, name, key_data)
        self.settings.sync()
        return True
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(), length=32, salt=salt,
            iterations=600000, backend=default_backend()
        )
        return kdf.derive(password.encode('utf-8'))
    
    def _encrypt_data(self, data: bytes, key: bytes) -> str:
        iv = secrets.token_bytes(12)
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(data) + encryptor.finalize()
        return base64.b64encode(iv + encryptor.tag + ciphertext).decode()
    
    def _decrypt_data(self, encrypted: str, key: bytes) -> bytes:
        data = base64.b64decode(encrypted)
        iv, tag, ciphertext = data[:12], data[12:28], data[28:]
        cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
        decryptor = cipher.decryptor()
        return decryptor.update(ciphertext) + decryptor.finalize()
    
    def save_key(self, algorithm: Algorithm, name: str, key: bytes) -> bool:
        if not self._master_key:
            return False
        encrypted = self._encrypt_data(key, self._master_key)
        self.settings.setValue(f"keys/{algorithm.display_name}/{name}", encrypted)
        self.settings.sync()
        return True
    
    def get_key(self, algorithm: Algorithm, name: str) -> Optional[bytes]:
        if not self._master_key:
            return None
        encrypted = self.settings.value(f"keys/{algorithm.display_name}/{name}")
        if not encrypted:
            return None
        try:
            return self._decrypt_data(encrypted, self._master_key)
        except Exception:
            return None
    
    def get_keys(self, algorithm: Algorithm) -> Dict[str, bytes]:
        if not self._master_key:
            return {}
        keys = {}
        names = self.get_key_names(algorithm)
        for name in names:
            key = self.get_key(algorithm, name)
            if key:
                keys[name] = key
        return keys
    
    def get_key_names(self, algorithm: Algorithm) -> List[str]:
        self.settings.beginGroup(f"keys/{algorithm.display_name}")
        names = list(self.settings.childKeys())
        self.settings.endGroup()
        return names
    
    def delete_key(self, algorithm: Algorithm, name: str) -> bool:
        self.settings.remove(f"keys/{algorithm.display_name}/{name}")
        self.settings.sync()
        return True
    
    def rename_key(self, algorithm: Algorithm, old_name: str, new_name: str) -> bool:
        key = self.get_key(algorithm, old_name)
        if key:
            self.save_key(algorithm, new_name, key)
            self.delete_key(algorithm, old_name)
            return True
        return False


class RC4Cipher:
    def __init__(self, key: bytes):
        self.S = list(range(256))
        j = 0
        for i in range(256):
            j = (j + self.S[i] + key[i % len(key)]) % 256
            self.S[i], self.S[j] = self.S[j], self.S[i]
    
    def process(self, data: bytes) -> bytes:
        S = self.S.copy()
        i = j = 0
        result = []
        for byte in data:
            i = (i + 1) % 256
            j = (j + S[i]) % 256
            S[i], S[j] = S[j], S[i]
            result.append(byte ^ S[(S[i] + S[j]) % 256])
        return bytes(result)


class CryptoEngine:
    @staticmethod
    def generate_key(algorithm: Algorithm) -> bytes:
        return secrets.token_bytes(algorithm.key_size)
    
    @staticmethod
    def encrypt(plaintext: str, key: bytes, algorithm: Algorithm) -> bytes:
        data = plaintext.encode('utf-8')
        
        if algorithm in (Algorithm.AES_128, Algorithm.AES_256):
            iv = secrets.token_bytes(16)
            padder = padding.PKCS7(128).padder()
            padded = padder.update(data) + padder.finalize()
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            return iv + cipher.encryptor().update(padded) + cipher.encryptor().finalize()
        
        elif algorithm == Algorithm.CHACHA20:
            nonce = secrets.token_bytes(16)
            cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None, backend=default_backend())
            return nonce + cipher.encryptor().update(data)
        
        elif algorithm in (Algorithm.CAMELLIA_128, Algorithm.CAMELLIA_256):
            iv = secrets.token_bytes(16)
            padder = padding.PKCS7(128).padder()
            padded = padder.update(data) + padder.finalize()
            cipher = Cipher(algorithms.Camellia(key), modes.CBC(iv), backend=default_backend())
            return iv + cipher.encryptor().update(padded) + cipher.encryptor().finalize()
        
        elif algorithm == Algorithm.TRIPLE_DES:
            iv = secrets.token_bytes(8)
            padder = padding.PKCS7(64).padder()
            padded = padder.update(data) + padder.finalize()
            cipher = Cipher(algorithms.TripleDES(key), modes.CBC(iv), backend=default_backend())
            return iv + cipher.encryptor().update(padded) + cipher.encryptor().finalize()
        
        elif algorithm == Algorithm.BLOWFISH:
            iv = secrets.token_bytes(8)
            padder = padding.PKCS7(64).padder()
            padded = padder.update(data) + padder.finalize()
            cipher = Cipher(algorithms.Blowfish(key), modes.CBC(iv), backend=default_backend())
            return iv + cipher.encryptor().update(padded) + cipher.encryptor().finalize()
        
        elif algorithm == Algorithm.RC4:
            return RC4Cipher(key).process(data)
        
        elif algorithm == Algorithm.XOR:
            return bytes(b ^ key[i % len(key)] for i, b in enumerate(data))
        
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    @staticmethod
    def decrypt(ciphertext: bytes, key: bytes, algorithm: Algorithm) -> str:
        if algorithm in (Algorithm.AES_128, Algorithm.AES_256):
            iv, encrypted = ciphertext[:16], ciphertext[16:]
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
            padded = cipher.decryptor().update(encrypted) + cipher.decryptor().finalize()
            unpadder = padding.PKCS7(128).unpadder()
            return (unpadder.update(padded) + unpadder.finalize()).decode('utf-8')
        
        elif algorithm == Algorithm.CHACHA20:
            nonce, encrypted = ciphertext[:16], ciphertext[16:]
            cipher = Cipher(algorithms.ChaCha20(key, nonce), mode=None, backend=default_backend())
            return cipher.decryptor().update(encrypted).decode('utf-8')
        
        elif algorithm in (Algorithm.CAMELLIA_128, Algorithm.CAMELLIA_256):
            iv, encrypted = ciphertext[:16], ciphertext[16:]
            cipher = Cipher(algorithms.Camellia(key), modes.CBC(iv), backend=default_backend())
            padded = cipher.decryptor().update(encrypted) + cipher.decryptor().finalize()
            unpadder = padding.PKCS7(128).unpadder()
            return (unpadder.update(padded) + unpadder.finalize()).decode('utf-8')
        
        elif algorithm == Algorithm.TRIPLE_DES:
            iv, encrypted = ciphertext[:8], ciphertext[8:]
            cipher = Cipher(algorithms.TripleDES(key), modes.CBC(iv), backend=default_backend())
            padded = cipher.decryptor().update(encrypted) + cipher.decryptor().finalize()
            unpadder = padding.PKCS7(64).unpadder()
            return (unpadder.update(padded) + unpadder.finalize()).decode('utf-8')
        
        elif algorithm == Algorithm.BLOWFISH:
            iv, encrypted = ciphertext[:8], ciphertext[8:]
            cipher = Cipher(algorithms.Blowfish(key), modes.CBC(iv), backend=default_backend())
            padded = cipher.decryptor().update(encrypted) + cipher.decryptor().finalize()
            unpadder = padding.PKCS7(64).unpadder()
            return (unpadder.update(padded) + unpadder.finalize()).decode('utf-8')
        
        elif algorithm == Algorithm.RC4:
            return RC4Cipher(key).process(ciphertext).decode('utf-8')
        
        elif algorithm == Algorithm.XOR:
            return bytes(b ^ key[i % len(key)] for i, b in enumerate(ciphertext)).decode('utf-8')
        
        raise ValueError(f"Unsupported algorithm: {algorithm}")


# =============================================================================
# WIDGETS
# =============================================================================

class MasterPasswordDialog(QDialog):
    def __init__(self, is_new: bool = False, parent=None):
        super().__init__(parent)
        self.is_new = is_new
        self.setWindowTitle(tr('create_master_password') if is_new else tr('master_password'))
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        
        if is_new:
            info = QLabel(tr('create_master_msg'))
            info.setWordWrap(True)
            layout.addWidget(info)
        
        form = QFormLayout()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow(tr('password') + ":", self.password_edit)
        
        if is_new:
            self.confirm_edit = QLineEdit()
            self.confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
            form.addRow(tr('confirmation') + ":", self.confirm_edit)
        
        layout.addLayout(form)
        
        show_cb = QCheckBox(tr('show_password'))
        show_cb.toggled.connect(self.toggle_visibility)
        layout.addWidget(show_cb)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.validate)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def toggle_visibility(self, show: bool):
        mode = QLineEdit.EchoMode.Normal if show else QLineEdit.EchoMode.Password
        self.password_edit.setEchoMode(mode)
        if self.is_new:
            self.confirm_edit.setEchoMode(mode)
    
    def validate(self):
        pwd = self.password_edit.text()
        if len(pwd) < 8:
            QMessageBox.warning(self, tr('error'), tr('min_8_chars'))
            return
        if self.is_new and pwd != self.confirm_edit.text():
            QMessageBox.warning(self, tr('error'), tr('passwords_no_match'))
            return
        self.accept()
    
    def get_password(self) -> str:
        return self.password_edit.text()


class KeyManagerWidget(QWidget):
    MAX_KEYS = 50
    
    def __init__(self, key_storage: SecureKeyStorage, status_callback=None, parent=None):
        super().__init__(parent)
        self.key_storage = key_storage
        self.status_callback = status_callback
        self.current_algo: Optional[Algorithm] = None
        self.display_fmt = DisplayFormat.BASE64
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Format
        fmt_layout = QHBoxLayout()
        fmt_layout.addWidget(QLabel(tr('display_format') + ":"))
        self.fmt_combo = QComboBox()
        self.fmt_combo.addItems([f.value for f in DisplayFormat])
        self.fmt_combo.currentTextChanged.connect(self.on_format_changed)
        fmt_layout.addWidget(self.fmt_combo)
        fmt_layout.addStretch()
        layout.addLayout(fmt_layout)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Algorithms
        algo_grp = QGroupBox(tr('algorithms'))
        algo_lay = QVBoxLayout(algo_grp)
        self.algo_list = QListWidget()
        self.algo_list.currentItemChanged.connect(self.on_algo_selected)
        algo_lay.addWidget(self.algo_list)
        splitter.addWidget(algo_grp)
        
        self.populate_algorithms()
        
        # Keys
        keys_grp = QGroupBox(tr('keys_max'))
        keys_lay = QVBoxLayout(keys_grp)
        
        self.keys_table = QTableWidget()
        self.keys_table.setColumnCount(2)
        self.keys_table.setHorizontalHeaderLabels([tr('key_name'), tr('key')])
        self.keys_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.keys_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.keys_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.keys_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.keys_table.customContextMenuRequested.connect(self.show_context_menu)
        keys_lay.addWidget(self.keys_table)
        
        btn_lay = QHBoxLayout()
        for text_key, slot in [('add', self.add_key), ('generate', self.gen_key),
                               ('delete', self.del_key), ('rename', self.rename_key)]:
            btn = QPushButton(tr(text_key))
            btn.clicked.connect(slot)
            btn_lay.addWidget(btn)
        keys_lay.addLayout(btn_lay)
        
        self.info_lbl = QLabel()
        self.info_lbl.setWordWrap(True)
        keys_lay.addWidget(self.info_lbl)
        
        splitter.addWidget(keys_grp)
        splitter.setSizes([200, 500])
        layout.addWidget(splitter)
        
        # Security - compact
        sec_lay = QHBoxLayout()
        sec_lay.setContentsMargins(0, 5, 0, 0)
        lock_btn = QPushButton(tr('lock_vault'))
        lock_btn.setMaximumWidth(160)
        lock_btn.clicked.connect(self.lock)
        sec_lay.addWidget(lock_btn)
        chg_btn = QPushButton(tr('change_password'))
        chg_btn.setMaximumWidth(180)
        chg_btn.clicked.connect(self.change_pwd)
        sec_lay.addWidget(chg_btn)
        sec_lay.addStretch()
        layout.addLayout(sec_lay)
    
    def populate_algorithms(self):
        self.algo_list.clear()
        for cat, algos in Algorithm.get_categories().items():
            cat_item = QListWidgetItem(cat)
            cat_item.setFlags(Qt.ItemFlag.NoItemFlags)
            cat_item.setFont(QFont("", -1, QFont.Weight.Bold))
            self.algo_list.addItem(cat_item)
            for algo in algos:
                item = QListWidgetItem(f"    {algo.display_name}")
                item.setData(Qt.ItemDataRole.UserRole, algo)
                self.algo_list.addItem(item)
    
    def on_format_changed(self, text: str):
        self.display_fmt = DisplayFormat.BASE64 if text == "Base64" else DisplayFormat.HEX
        self.refresh_keys()
    
    def on_algo_selected(self, current: QListWidgetItem, prev):
        if current:
            algo = current.data(Qt.ItemDataRole.UserRole)
            if algo:
                self.current_algo = algo
                self.refresh_keys()
                robust = tr('robust') if algo.is_robust else tr('not_recommended')
                self.info_lbl.setText(f"{tr('size')}: {algo.key_size} {tr('bytes')} ({algo.key_size*8} {tr('bits')}) | {robust}")
    
    def refresh_keys(self):
        self.keys_table.setRowCount(0)
        if not self.current_algo or not self.key_storage.is_unlocked():
            return
        for name, key in self.key_storage.get_keys(self.current_algo).items():
            row = self.keys_table.rowCount()
            self.keys_table.insertRow(row)
            self.keys_table.setItem(row, 0, QTableWidgetItem(name))
            key_item = QTableWidgetItem(DataEncoder.encode(key, self.display_fmt))
            key_item.setFont(QFont("Consolas", 9))
            self.keys_table.setItem(row, 1, key_item)
    
    def add_key(self):
        if not self.current_algo or not self.key_storage.is_unlocked():
            return
        existing = self.key_storage.get_key_names(self.current_algo)
        if len(existing) >= self.MAX_KEYS:
            QMessageBox.warning(self, tr('warning'), tr('max_keys').format(self.MAX_KEYS))
            return
        name, ok = QInputDialog.getText(self, tr('key_name'), tr('key_name_prompt'))
        if not ok or not name.strip() or name.strip() in existing:
            if name.strip() in existing:
                QMessageBox.warning(self, tr('error'), tr('name_exists'))
            return
        key_txt, ok = QInputDialog.getText(self, tr('key'), tr('key_in_format').format(self.display_fmt.value))
        if not ok:
            return
        try:
            key = DataEncoder.decode(key_txt.strip(), self.display_fmt)
            if len(key) != self.current_algo.key_size:
                QMessageBox.warning(self, tr('error'), tr('wrong_size').format(len(key), self.current_algo.key_size))
                return
            self.key_storage.save_key(self.current_algo, name.strip(), key)
            self.refresh_keys()
        except Exception as e:
            QMessageBox.critical(self, tr('error'), str(e))
    
    def gen_key(self):
        if not self.current_algo or not self.key_storage.is_unlocked():
            return
        existing = self.key_storage.get_key_names(self.current_algo)
        if len(existing) >= self.MAX_KEYS:
            QMessageBox.warning(self, tr('warning'), tr('max_keys').format(self.MAX_KEYS))
            return
        name, ok = QInputDialog.getText(self, tr('key_name'), tr('key_name_prompt'), text=f"Key {len(existing)+1}")
        if not ok or not name.strip() or name.strip() in existing:
            if name.strip() in existing:
                QMessageBox.warning(self, tr('error'), tr('name_exists'))
            return
        key = CryptoEngine.generate_key(self.current_algo)
        self.key_storage.save_key(self.current_algo, name.strip(), key)
        self.refresh_keys()
    
    def del_key(self):
        row = self.keys_table.currentRow()
        if row < 0:
            return
        name = self.keys_table.item(row, 0).text()
        if QMessageBox.question(self, tr('confirm_delete'), tr('confirm_delete_key').format(name)) == QMessageBox.StandardButton.Yes:
            self.key_storage.delete_key(self.current_algo, name)
            self.refresh_keys()
    
    def rename_key(self):
        row = self.keys_table.currentRow()
        if row < 0:
            return
        old = self.keys_table.item(row, 0).text()
        new, ok = QInputDialog.getText(self, tr('rename'), tr('new_name'), text=old)
        if ok and new.strip() and new.strip() != old:
            if new.strip() in self.key_storage.get_key_names(self.current_algo):
                QMessageBox.warning(self, tr('error'), tr('name_exists'))
                return
            self.key_storage.rename_key(self.current_algo, old, new.strip())
            self.refresh_keys()
    
    def show_context_menu(self, pos):
        row = self.keys_table.currentRow()
        if row < 0:
            return
        menu = QMenu(self)
        menu.addAction(tr('copy')).triggered.connect(lambda: QApplication.clipboard().setText(
            self.keys_table.item(row, 1).text()))
        menu.addSeparator()
        menu.addAction(tr('rename')).triggered.connect(self.rename_key)
        menu.addAction(tr('delete')).triggered.connect(self.del_key)
        menu.exec(self.keys_table.viewport().mapToGlobal(pos))
    
    def update_status(self, locked: bool):
        if self.status_callback:
            self.status_callback(locked)
    
    def lock(self):
        self.key_storage.lock()
        self.refresh_keys()
        self.update_status(True)
        
        # Demander le mot de passe pour déverrouiller
        while not self.key_storage.is_unlocked():
            dlg = MasterPasswordDialog(is_new=False, parent=self)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                QMessageBox.warning(self, tr('warning'), tr('vault_locked_warning'))
                return
            
            if self.key_storage.unlock(dlg.get_password()):
                self.refresh_keys()
                self.update_status(False)
                return
            else:
                QMessageBox.warning(self, tr('error'), tr('wrong_password'))
    
    def change_pwd(self):
        old, ok = QInputDialog.getText(self, tr('old_password'), tr('old_password') + ":", QLineEdit.EchoMode.Password)
        if not ok:
            return
        dlg = MasterPasswordDialog(is_new=True, parent=self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            if self.key_storage.change_master_password(old, dlg.get_password()):
                QMessageBox.information(self, tr('ok'), tr('password_changed'))
            else:
                QMessageBox.critical(self, tr('error'), tr('old_password_wrong'))
    
    def get_key(self, algo: Algorithm, name: str) -> Optional[bytes]:
        return self.key_storage.get_key(algo, name)
    
    def get_key_names(self, algo: Algorithm) -> List[str]:
        return self.key_storage.get_key_names(algo)


class CryptoWidget(QWidget):
    def __init__(self, key_mgr: KeyManagerWidget, parent=None):
        super().__init__(parent)
        self.key_mgr = key_mgr
        self.display_fmt = DisplayFormat.BASE64
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Config row
        cfg = QHBoxLayout()
        cfg.addWidget(QLabel(tr('algorithm') + ":"))
        self.algo_combo = QComboBox()
        for cat, algos in Algorithm.get_categories().items():
            for algo in algos:
                self.algo_combo.addItem(algo.display_name, algo)
        self.algo_combo.currentIndexChanged.connect(self.on_algo_changed)
        cfg.addWidget(self.algo_combo)
        
        cfg.addWidget(QLabel(tr('key') + ":"))
        self.key_combo = QComboBox()
        self.key_combo.setMinimumWidth(150)
        cfg.addWidget(self.key_combo)
        
        cfg.addWidget(QLabel(tr('format') + ":"))
        self.fmt_combo = QComboBox()
        self.fmt_combo.addItems([f.value for f in DisplayFormat])
        self.fmt_combo.currentTextChanged.connect(lambda t: setattr(self, 'display_fmt', 
            DisplayFormat.BASE64 if t == "Base64" else DisplayFormat.HEX))
        cfg.addWidget(self.fmt_combo)
        cfg.addStretch()
        layout.addLayout(cfg)
        
        # Warning
        self.warn_lbl = QLabel()
        self.warn_lbl.setWordWrap(True)
        self.warn_lbl.hide()
        layout.addWidget(self.warn_lbl)
        
        # Text areas
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        plain_grp = QGroupBox(tr('plain_text'))
        plain_lay = QVBoxLayout(plain_grp)
        self.plain_txt = QTextEdit()
        self.plain_txt.setFont(QFont("Consolas", 11))
        plain_lay.addWidget(self.plain_txt)
        splitter.addWidget(plain_grp)
        
        cipher_grp = QGroupBox(tr('cipher_text'))
        cipher_lay = QVBoxLayout(cipher_grp)
        self.cipher_txt = QTextEdit()
        self.cipher_txt.setFont(QFont("Consolas", 11))
        cipher_lay.addWidget(self.cipher_txt)
        splitter.addWidget(cipher_grp)
        
        layout.addWidget(splitter, 1)
        
        # Buttons
        btn_lay = QHBoxLayout()
        for text_key, slot in [('encrypt', self.encrypt), ('decrypt', self.decrypt), ('clear', self.clear)]:
            btn = QPushButton(tr(text_key))
            btn.setMinimumHeight(40)
            btn.clicked.connect(slot)
            btn_lay.addWidget(btn)
        layout.addLayout(btn_lay)
        
        self.on_algo_changed()
    
    def on_algo_changed(self):
        algo = self.algo_combo.currentData()
        if not algo:
            return
        
        # Warning
        if algo.is_robust:
            self.warn_lbl.hide()
        elif algo in (Algorithm.RC4, Algorithm.XOR):
            self.warn_lbl.setText(tr('weak_warning').format(algo.display_name))
            self.warn_lbl.setStyleSheet("color: red; padding: 5px;")
            self.warn_lbl.show()
        else:
            self.warn_lbl.setText(tr('legacy_warning').format(algo.display_name))
            self.warn_lbl.setStyleSheet("color: orange; padding: 5px;")
            self.warn_lbl.show()
        
        self.refresh_keys()
    
    def refresh_keys(self):
        self.key_combo.clear()
        algo = self.algo_combo.currentData()
        if algo:
            names = self.key_mgr.get_key_names(algo)
            self.key_combo.addItems(names if names else [tr('no_key')])
    
    def get_key(self) -> Optional[bytes]:
        algo = self.algo_combo.currentData()
        name = self.key_combo.currentText()
        if not algo or name == tr('no_key'):
            QMessageBox.warning(self, tr('error'), tr('no_key_selected'))
            return None
        key = self.key_mgr.get_key(algo, name)
        if not key:
            QMessageBox.warning(self, tr('error'), tr('cannot_retrieve_key'))
            return None
        return key
    
    def encrypt(self):
        text = self.plain_txt.toPlainText()
        if not text:
            return
        key = self.get_key()
        if not key:
            return
        try:
            cipher = CryptoEngine.encrypt(text, key, self.algo_combo.currentData())
            self.cipher_txt.setPlainText(DataEncoder.encode(cipher, self.display_fmt))
        except Exception as e:
            QMessageBox.critical(self, tr('error'), str(e))
    
    def decrypt(self):
        text = self.cipher_txt.toPlainText().strip()
        if not text:
            return
        key = self.get_key()
        if not key:
            return
        try:
            cipher = DataEncoder.decode(text, self.display_fmt)
            plain = CryptoEngine.decrypt(cipher, key, self.algo_combo.currentData())
            self.plain_txt.setPlainText(plain)
        except Exception as e:
            QMessageBox.critical(self, tr('error'), tr('decrypt_error').format(e))
    
    def clear(self):
        self.plain_txt.clear()
        self.cipher_txt.clear()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("CryptoTool", "CryptoToolPro")
        self.key_storage = SecureKeyStorage(self.settings)
        
        if not self.init_storage():
            sys.exit(0)
        
        self.setup_ui()
        geo = self.settings.value("window/geometry")
        if geo:
            self.restoreGeometry(geo)
    
    def init_storage(self) -> bool:
        if not self.key_storage.is_initialized():
            QMessageBox.information(None, tr('welcome'), tr('welcome_msg'))
            dlg = MasterPasswordDialog(is_new=True)
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return False
            self.key_storage.initialize(dlg.get_password())
            return True
        
        for i in range(3):
            dlg = MasterPasswordDialog()
            if dlg.exec() != QDialog.DialogCode.Accepted:
                return False
            if self.key_storage.unlock(dlg.get_password()):
                return True
            QMessageBox.warning(None, tr('error'), f"{tr('wrong_password')} {2-i} {tr('attempts_left')}")
        return False
    
    def setup_ui(self):
        self.setWindowTitle(tr('app_title'))
        self.setMinimumSize(800, 600)
        
        tabs = QTabWidget()
        self.key_mgr = KeyManagerWidget(self.key_storage, self.update_status_bar)
        self.crypto = CryptoWidget(self.key_mgr)
        
        tabs.addTab(self.crypto, tr('tab_encryption'))
        tabs.addTab(self.key_mgr, tr('tab_keys'))
        tabs.addTab(self.create_help(), tr('tab_help'))
        tabs.currentChanged.connect(lambda i: self.crypto.refresh_keys() if i == 0 else None)
        
        self.setCentralWidget(tabs)
        
        # Status bar
        self.status_label = QLabel()
        self.statusBar().addWidget(self.status_label)
        self.update_status_bar(False)
    
    def update_status_bar(self, locked: bool):
        if locked:
            self.status_label.setText(tr('status_locked'))
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.status_label.setText(tr('status_unlocked'))
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
    
    def create_help(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        txt = QTextEdit()
        txt.setReadOnly(True)
        txt.setHtml(f"""
        <h1>{tr('help_title')}</h1>
        <p><i>{tr('help_intro')}</i></p>
        
        <h2>{tr('help_quickstart')}</h2>
        {tr('help_quickstart_content')}
        
        <h2>{tr('help_algorithms')}</h2>
        {tr('help_algo_details')}
        
        <h2>{tr('help_key_management')}</h2>
        {tr('help_key_content')}
        
        <h2>{tr('help_formats')}</h2>
        {tr('help_formats_content')}
        
        <h2>{tr('help_security')}</h2>
        {tr('help_security_content')}
        
        <h2>{tr('help_tips')}</h2>
        {tr('help_tips_content')}
        
        <h2>{tr('help_technical')}</h2>
        {tr('help_technical_content')}
        """)
        lay.addWidget(txt)
        return w
    
    def closeEvent(self, e):
        self.settings.setValue("window/geometry", self.saveGeometry())
        self.key_storage.lock()
        e.accept()


def main():
    # Initialise la langue avant de créer l'application
    lang = get_system_language()
    Tr.set_language(lang)
    
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
