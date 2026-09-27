#!/usr/bin/env python3

"""
================================================================================
Zyxel Router Configuration Backup/Restore Tool
================================================================================

DESCRIPTION:
    This tool provides comprehensive functionality for working with Zyxel router
    configuration backups. It can download, decrypt, encrypt, and restore
    configuration files, as well as extract and analyze firmware images.

FEATURES:
    - Download encrypted backups from Zyxel routers via HTTP
    - Decrypt configuration files encrypted with AES-256-CBC
    - Encrypt configuration files for restoration
    - Restore configurations to router (triggers reboot)
    - Extract and analyze Zyxel firmware images
    - Automatic discovery of encryption password from firmware

ENCRYPTION DETAILS:
    - Algorithm: AES-256-CBC
    - Key Derivation: MD5 (OpenSSL EVP_BytesToKey)
    - Password: EwhJaD44DfprDOs7OXx9jzAtLg5PKtD8 (hardcoded in firmware)
    - Format: OpenSSL salted encryption (begins with "Salted__")

AUTHENTICATION:
    The router uses MD5-based authentication:
    1. Login page provides a Session ID (SID)
    2. Client calculates: MD5(password:sid)
    3. Submit hash with username
    4. Server validates and creates session cookie (COOKIE_SESSION_KEY)

FILE FORMAT:
    Encrypted:  Salted OpenSSL format (starts with "Salted__")
    Decrypted:  XML following TR-069 InternetGatewayDevice schema

ROUTER WEB INTERFACE:
    - Login Page:   /cgi-bin/login_advance.cgi
    - Backup/Restore: /cgi-bin/backupRestore.cgi
    - Backup File:  /romfile.cfg

USAGE EXAMPLES:
    # Download and decrypt backup
    python3 zyxel_backup_tool.py full-backup -u admin -p password -o config.xml

    # Decrypt existing backup
    python3 zyxel_backup_tool.py decrypt -i backup.cfg -o config.xml

    # Encrypt configuration
    python3 zyxel_backup_tool.py encrypt -i config.xml -o backup.cfg

    # Restore configuration (WARNING: reboots router)
    python3 zyxel_backup_tool.py full-restore -i config.xml -u admin -p password

    # Extract firmware
    python3 zyxel_backup_tool.py extract -i firmware.bin -o ./extracted

    # Use custom router IP
    python3 zyxel_backup_tool.py full-backup -u admin -p password -o config.xml -r 10.0.0.1

REQUIREMENTS:
    Python:
        - Python 3.6 or higher
        - Standard library only (no external packages)

    System Tools:
        - openssl: For encryption/decryption operations
        - binwalk: For firmware extraction (optional)
        - unsquashfs: For SquashFS extraction (optional)
        - strings: For binary analysis (optional)

INSTALLATION (System Tools):
    macOS:
        brew install openssl binwalk squashfs

    Ubuntu/Debian:
        sudo apt-get install openssl binwalk squashfs-tools

    RHEL/CentOS:
        sudo yum install openssl binwalk squashfs-tools

SECURITY NOTES:
    WARNING: This tool exposes several security vulnerabilities in the router:

    1. Hardcoded Encryption Key: Same password across all devices of same model
    2. Weak Key Derivation: MD5 is deprecated and vulnerable to attacks
    3. No Authentication: CBC mode without HMAC allows tampering attacks
    4. Plaintext Credentials: All passwords visible in decrypted config
    5. MD5 Password Hashing: Weak hashing algorithm for authentication

    RECOMMENDATIONS:
    - Only use on devices you own or have permission to access
    - Change default admin passwords immediately
    - Restrict web interface access to LAN only
    - Keep firmware updated
    - Don't share backup files publicly

LEGAL DISCLAIMER:
    This tool is provided for educational and research purposes only.
    Users should:
    - Only analyze devices they own or have explicit permission to examine
    - Comply with all applicable laws and regulations
    - Use this information responsibly and ethically
    - Respect manufacturer intellectual property

    Unauthorized access to network devices may be illegal in your jurisdiction.

TECHNICAL IMPLEMENTATION DETAILS:

    LOGIN PROCESS:
        1. GET /cgi-bin/login_advance.cgi
        2. Extract SID from JavaScript: var sid = 'XXXXXXXX'
        3. Calculate hash = MD5(password:sid)
        4. POST with Loginuser, LoginPasswordValue (hash), LoginSidValue, submitValue=1
        5. Receive COOKIE_SESSION_KEY in response
        6. Use cookie for subsequent requests

    BACKUP DOWNLOAD:
        1. POST /cgi-bin/backupRestore.cgi with configFilter=1
        2. Wait 3 seconds for backup generation
        3. GET /romfile.cfg
        4. File is encrypted with OpenSSL AES-256-CBC

    BACKUP RESTORE:
        1. Encrypt XML file first (must be encrypted!)
        2. POST /cgi-bin/backupRestore.cgi as multipart/form-data
        3. Field: tools_FW_UploadFile (file data)
        4. Field: postflag = "1"
        5. Router validates, applies, and reboots

    ENCRYPTION COMMAND (used by router):
        openssl aes-256-cbc -md MD5 -k EwhJaD44DfprDOs7OXx9jzAtLg5PKtD8 \\
            -e -in /var/config.cfg -out /var/romfile.cfg

    DECRYPTION COMMAND (used by router):
        openssl aes-256-cbc -md MD5 -k EwhJaD44DfprDOs7OXx9jzAtLg5PKtD8 \\
            -d -in /var/tmp/upload_config.cfg -out /var/tmp/decrypt_config.cfg

    FIRMWARE STRUCTURE:
        - Format: UBI images within GPT partitions
        - Root FS: SquashFS compressed (ubi_r0.ubifs)
        - Encryption password found in: /lib/MSTC/libCmd.so
        - Functions: EncodeRomfile, doSysBackupCfg, make_backup_config

CONFIGURATION FILE STRUCTURE:
    <?xml version="1.0" encoding="UTF-8"?>
    <InternetGatewayDevice>
      <X_5067F0_Ext>
        <!-- Vendor-specific extensions -->
        <WebHttp>...</WebHttp>
        <WlanScheduler>...</WlanScheduler>
      </X_5067F0_Ext>
      <ManagementServer>
        <!-- TR-069 management settings -->
      </ManagementServer>
      <LANDevice>
        <!-- LAN configuration -->
      </LANDevice>
      <WANDevice>
        <!-- WAN configuration -->
      </WANDevice>
    </InternetGatewayDevice>

TROUBLESHOOTING:
    Login Fails:
        - Verify username and password are correct
        - Check router IP address is accessible
        - Ensure web interface is enabled
        - Try accessing manually via browser first

    Decryption Fails:
        - Verify file starts with "Salted__" (check with hexdump)
        - Ensure OpenSSL is installed
        - Check if firmware version uses different encryption password
        - Extract firmware to find correct password

    Download Returns HTML:
        - Session may have expired, try logging in again
        - Check if backup creation is supported on this firmware
        - Verify router isn't in restricted mode

    Restore Fails:
        - Ensure file is encrypted before upload
        - Verify XML structure is valid
        - Check that configuration is compatible with firmware version
        - Router may need factory reset if it becomes unresponsive

VERSION HISTORY:
    v1.0 (2024-11-18): Initial release
        - Full backup/restore functionality
        - Firmware extraction support
        - Automated encryption/decryption

AUTHOR: Security Research Team
LICENSE: Educational and Research Use Only
================================================================================
"""

import sys
import os
import shutil
import hashlib
import subprocess
import argparse
import time
import re
from pathlib import Path
from typing import Optional, Tuple
import urllib.request
import urllib.parse
import http.cookiejar

# Optional cryptography for pure-Python fallback
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

# Auto-detect OpenSSL on Windows if installed via Git or standard locations
if sys.platform == 'win32':
    _win_tool_paths = [
        r"C:\Program Files\Git\usr\bin",
        r"C:\Program Files\OpenSSL-Win64\bin",
        r"C:\Program Files (x86)\OpenSSL-Win32\bin",
        os.path.expanduser(r"~\.local\bin")
    ]
    for _p in _win_tool_paths:
        if os.path.isdir(_p) and _p not in os.environ.get("PATH", ""):
            os.environ["PATH"] = _p + os.pathsep + os.environ.get("PATH", "")


def evp_bytes_to_key(password: bytes, salt: bytes, key_len: int = 32, iv_len: int = 16) -> Tuple[bytes, bytes]:
    """
    OpenSSL EVP_BytesToKey key derivation function with MD5.
    Used by 'openssl enc -aes-256-cbc -md MD5'.
    """
    data = b""
    d_i = b""
    while len(data) < key_len + iv_len:
        d_i = hashlib.md5(d_i + password + salt).digest()
        data += d_i
    return data[:key_len], data[key_len:key_len + iv_len]


# ============================================================================
# CONFIGURATION CONSTANTS
# ============================================================================

# Encryption password found in firmware /lib/MSTC/libCmd.so
ENCRYPTION_PASSWORD = "EwhJaD44DfprDOs7OXx9jzAtLg5PKtD8"

# Default router configuration
DEFAULT_ROUTER_IP = "192.168.1.1"
DEFAULT_USERNAME = "admin"

# Working directory for temporary files
WORK_DIR = "./zyxel_work"

# ANSI color codes for terminal output
class Colors:
    """ANSI color codes for colored terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color


# ============================================================================
# LOGGER CLASS
# ============================================================================

class Logger:
    """
    Simple logger with colored output for different message types

    Methods:
        info(msg):    Blue info messages
        success(msg): Green success messages
        warning(msg): Yellow warning messages
        error(msg):   Red error messages
        header(msg):  Green section headers
    """

    @staticmethod
    def info(msg: str):
        """Print informational message in blue"""
        print(f"{Colors.BLUE}[INFO]{Colors.NC} {msg}")

    @staticmethod
    def success(msg: str):
        """Print success message in green"""
        print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {msg}")

    @staticmethod
    def warning(msg: str):
        """Print warning message in yellow"""
        print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {msg}")

    @staticmethod
    def error(msg: str):
        """Print error message in red to stderr"""
        print(f"{Colors.RED}[ERROR]{Colors.NC} {msg}", file=sys.stderr)

    @staticmethod
    def header(msg: str):
        """Print section header in green"""
        print(f"\n{Colors.GREEN}{'=' * 50}{Colors.NC}")
        print(f"{Colors.GREEN}{msg}{Colors.NC}")
        print(f"{Colors.GREEN}{'=' * 50}{Colors.NC}")


# ============================================================================
# MAIN TOOL CLASS
# ============================================================================

class ZyxelBackupTool:
    """
    Main class for Zyxel router backup/restore operations

    This class handles all interactions with the Zyxel router including:
    - Authentication and session management
    - Downloading encrypted backups
    - Encrypting and decrypting configuration files
    - Restoring configurations
    - Extracting and analyzing firmware

    Attributes:
        router_ip (str): IP address of the router
        work_dir (Path): Working directory for temporary files
        cookie_jar (CookieJar): HTTP cookie storage
        opener (OpenerDirector): URL opener with cookie handling

    Example:
        tool = ZyxelBackupTool(router_ip="192.168.1.1")
        if tool.login("admin", "password"):
            tool.download_backup("backup.cfg")
            tool.decrypt_backup("backup.cfg", "config.xml")
    """

    def __init__(self, router_ip: str = DEFAULT_ROUTER_IP):
        """
        Initialize the Zyxel Backup Tool

        Args:
            router_ip: IP address of the router (default: 192.168.1.1)
        """
        self.router_ip = router_ip
        self.work_dir = Path(WORK_DIR)
        self.work_dir.mkdir(exist_ok=True)
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar)
        )

    def _calculate_md5(self, data: str) -> str:
        """
        Calculate MD5 hash of string

        Used for password authentication: hash = MD5(password:sid)

        Args:
            data: String to hash

        Returns:
            MD5 hash as hexadecimal string
        """
        #return hashlib.md5(s.encode('utf-8')).hexdigest()
        return hashlib.md5(data.encode('latin-1')).hexdigest()

    def _make_request(self, url: str, data: Optional[dict] = None,
                      headers: Optional[dict] = None) -> bytes:
        """
        Make HTTP request with cookie handling

        Args:
            url: URL to request
            data: Optional POST data dictionary
            headers: Optional HTTP headers dictionary

        Returns:
            Response body as bytes

        Raises:
            urllib.error.URLError: If request fails
        """
        req_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        if headers:
            req_headers.update(headers)

        post_data = None
        if data:
            post_data = urllib.parse.urlencode(data).encode()

        request = urllib.request.Request(url, data=post_data, headers=req_headers)
        response = self.opener.open(request)
        return response.read()

    def login(self, username: str, password: str) -> bool:
        """
        Login to router and establish session

        Authentication process:
        1. GET login page to obtain Session ID (SID)
        2. Calculate MD5 hash: hash = MD5(password:sid)
        3. POST with username, hash, SID, and submit flag
        4. Verify COOKIE_SESSION_KEY is set in response

        Args:
            username: Router admin username (usually "admin")
            password: Router admin password

        Returns:
            True if login successful, False otherwise

        Example:
            tool = ZyxelBackupTool()
            if tool.login("admin", "mypassword"):
                print("Login successful!")
        """
        Logger.header("Logging into Router")
        Logger.info(f"Router: {self.router_ip}")
        Logger.info(f"Username: {username}")

        try:
            # Get login page and extract SID
            Logger.info("Fetching login page...")
            login_url = f"http://{self.router_ip}/cgi-bin/login_advance.cgi"
            login_page = self._make_request(login_url).decode('utf-8', errors='ignore')

            # Extract SID from JavaScript: var sid = 'XXXXXXXX'
            sid_match = re.search(r"var sid = '([^']+)'", login_page)
            if not sid_match:
                Logger.error("Failed to extract SID from login page")
                return False

            sid = sid_match.group(1)
            Logger.info(f"Session ID: {sid}")

            # Calculate MD5 hash: MD5(password:sid) directly as done in router JavaScript
            hash_input = f"{password}:{sid}"
            password_hash = self._calculate_md5(hash_input)
            Logger.info(f"Password hash: {password_hash}")

            # Perform login
            Logger.info("Authenticating...")
            login_data = {
                "Loginuser": username,
                "LoginPasswordValue": password_hash,
                "LoginSidValue": sid,
                "submitValue": "1",
                "Prestige_Login": "Login",
                "fake_username": "",
                "fake_pass": ""
            }
            login_headers = {
                "Referer": login_url,
                "Origin": f"http://{self.router_ip}"
            }
            login_resp_bytes = self._make_request(login_url, data=login_data, headers=login_headers)
            login_resp_text = login_resp_bytes.decode('utf-8', errors='ignore')

            # Verify login by checking for session cookie
            session_cookie = None
            for cookie in self.cookie_jar:
                if cookie.name == "COOKIE_SESSION_KEY":
                    session_cookie = cookie.value
                    break

            if session_cookie or "indexmain.cgi" in login_resp_text:
                Logger.success("Login successful!")
                return True
            else:
                Logger.error("Login failed!")
                return False

        except Exception as e:
            Logger.error(f"Login error: {e}")
            return False

    def download_backup(self, output_file: str) -> bool:
        """
        Download encrypted backup from router

        Process:
        1. POST to /cgi-bin/backupRestore.cgi with configFilter=1
        2. Wait 3 seconds for backup generation
        3. GET /romfile.cfg (encrypted backup file)
        4. Verify file starts with "Salted__" header

        Args:
            output_file: Path to save encrypted backup file

        Returns:
            True if download successful, False otherwise

        Note:
            Requires active session (call login() first)

        Example:
            tool.login("admin", "password")
            tool.download_backup("backup.cfg")
        """
        Logger.header("Downloading Backup from Router")

        try:
            # Trigger backup creation
            Logger.info("Triggering backup creation...")
            backup_url = f"http://{self.router_ip}/cgi-bin/backupRestore.cgi"
            headers = {"Referer": backup_url}
            self._make_request(backup_url, data={"configFilter": "1"}, headers=headers)

            # Wait for backup to be created
            Logger.info("Waiting for backup file to be generated...")
            time.sleep(3)

            # Download backup
            Logger.info("Downloading backup file...")
            romfile_url = f"http://{self.router_ip}/romfile.cfg"
            backup_data = self._make_request(romfile_url, headers=headers)

            # Save to file
            with open(output_file, 'wb') as f:
                f.write(backup_data)

            # Verify download
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                # Check if it's actually encrypted (should start with "Salted__")
                with open(output_file, 'rb') as f:
                    header = f.read(8)
                    if header == b'Salted__':
                        size = os.path.getsize(output_file)
                        Logger.success(f"Backup downloaded successfully: {output_file} ({size} bytes)")
                        return True
                    else:
                        Logger.error("Downloaded file is not encrypted (may be an error page)")
                        with open(output_file, 'r') as f:
                            print(f.read())
                        return False
            else:
                Logger.error("Download failed!")
                return False

        except Exception as e:
            Logger.error(f"Download error: {e}")
            return False

    def decrypt_backup(self, input_file: str, output_file: str,
                      password: str = ENCRYPTION_PASSWORD) -> bool:
        """
        Decrypt backup file using OpenSSL AES-256-CBC

        Decryption command equivalent:
            openssl aes-256-cbc -md MD5 -k <password> -d -in <input> -out <output>

        File format:
            Bytes 0-7:   "Salted__" (ASCII header)
            Bytes 8-15:  8-byte random salt
            Bytes 16+:   AES-256-CBC encrypted data

        Args:
            input_file: Path to encrypted backup file
            output_file: Path to save decrypted XML file
            password: Encryption password (default: hardcoded password from firmware)

        Returns:
            True if decryption successful, False otherwise

        Example:
            tool.decrypt_backup("backup.cfg", "config.xml")
        """
        Logger.header("Decrypting Backup File")
        Logger.info(f"Input: {input_file}")
        Logger.info(f"Output: {output_file}")

        # Verify input file exists
        if not os.path.exists(input_file):
            Logger.error(f"Input file not found: {input_file}")
            return False

        # Check if file is encrypted
        with open(input_file, 'rb') as f:
            header = f.read(8)
    def _get_openssl_cmd(self) -> Optional[str]:
        """Find the openssl executable."""
        cmd = shutil.which('openssl')
        if cmd:
            return cmd
        if sys.platform == 'win32':
            candidates = [
                r"C:\Program Files\Git\usr\bin\openssl.exe",
                r"C:\Program Files\OpenSSL-Win64\bin\openssl.exe",
                r"C:\Program Files (x86)\OpenSSL-Win32\bin\openssl.exe",
                os.path.expanduser(r"~\.local\bin\openssl.cmd"),
            ]
            for c in candidates:
                if os.path.exists(c):
                    return c
        return None

    def _decrypt_backup_py(self, input_file: str, output_file: str, password: str) -> bool:
        """Pure-Python AES-256-CBC decryption with EVP_BytesToKey(MD5)."""
        if not HAS_CRYPTOGRAPHY:
            Logger.error("cryptography library not found for fallback decryption")
            return False
        try:
            with open(input_file, 'rb') as f:
                data = f.read()
            if not data.startswith(b'Salted__') or len(data) < 16:
                Logger.error("Input file is not a valid OpenSSL salted ciphertext")
                return False
            salt = data[8:16]
            ciphertext = data[16:]
            key, iv = evp_bytes_to_key(password.encode('latin-1'), salt)
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
            decryptor = cipher.decryptor()
            padded = decryptor.update(ciphertext) + decryptor.finalize()
            unpadder = padding.PKCS7(128).unpadder()
            plaintext = unpadder.update(padded) + unpadder.finalize()
            with open(output_file, 'wb') as f:
                f.write(plaintext)
            return True
        except Exception as e:
            Logger.error(f"Fallback decryption error: {e}")
            return False

    def _encrypt_config_py(self, input_file: str, output_file: str, password: str) -> bool:
        """Pure-Python AES-256-CBC encryption with EVP_BytesToKey(MD5)."""
        if not HAS_CRYPTOGRAPHY:
            Logger.error("cryptography library not found for fallback encryption")
            return False
        try:
            with open(input_file, 'rb') as f:
                plaintext = f.read()
            salt = os.urandom(8)
            key, iv = evp_bytes_to_key(password.encode('latin-1'), salt)
            padder = padding.PKCS7(128).padder()
            padded = padder.update(plaintext) + padder.finalize()
            cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
            encryptor = cipher.encryptor()
            ciphertext = b'Salted__' + salt + encryptor.update(padded) + encryptor.finalize()
            with open(output_file, 'wb') as f:
                f.write(ciphertext)
            return True
        except Exception as e:
            Logger.error(f"Fallback encryption error: {e}")
            return False

    def decrypt_backup(self, input_file: str, output_file: str,
                      password: str = ENCRYPTION_PASSWORD) -> bool:
        """
        Decrypt backup file using OpenSSL AES-256-CBC

        Decryption command equivalent:
            openssl aes-256-cbc -md MD5 -k <password> -d -in <input> -out <output>

        File format:
            Bytes 0-7:   "Salted__" (ASCII header)
            Bytes 8-15:  8-byte random salt
            Bytes 16+:   AES-256-CBC encrypted data

        Args:
            input_file: Path to encrypted backup file
            output_file: Path to save decrypted XML file
            password: Encryption password (default: hardcoded password from firmware)

        Returns:
            True if decryption successful, False otherwise

        Example:
            tool.decrypt_backup("backup.cfg", "config.xml")
        """
        Logger.header("Decrypting Backup File")
        Logger.info(f"Input: {input_file}")
        Logger.info(f"Output: {output_file}")

        # Verify input file exists
        if not os.path.exists(input_file):
            Logger.error(f"Input file not found: {input_file}")
            return False

        # Check if file is encrypted
        with open(input_file, 'rb') as f:
            header = f.read(8)
            if header != b'Salted__':
                Logger.warning("File does not appear to be OpenSSL encrypted (no 'Salted__' header)")

        openssl_bin = self._get_openssl_cmd()
        used_openssl = False
        if openssl_bin:
            try:
                Logger.info("Decrypting via OpenSSL...")
                cmd = [
                    openssl_bin, 'aes-256-cbc',
                    '-md', 'MD5',
                    '-k', password,
                    '-d',
                    '-in', input_file,
                    '-out', output_file
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0 and os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                    used_openssl = True
                elif result.returncode != 0 and 'bad decrypt' in result.stderr:
                    Logger.error("Decryption failed! Wrong password or corrupted file.")
                    return False
            except Exception as e:
                Logger.warning(f"OpenSSL execution failed ({e}), attempting Python fallback...")

        if not used_openssl:
            if HAS_CRYPTOGRAPHY:
                Logger.info("Decrypting via internal Python cryptography engine...")
                if not self._decrypt_backup_py(input_file, output_file, password):
                    return False
            else:
                Logger.error("OpenSSL not found and cryptography package not installed.")
                return False

        # Verify output is valid XML
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            with open(output_file, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline().strip()
                if first_line.startswith('<?xml'):
                    size = os.path.getsize(output_file)
                    f.seek(0)
                    lines = len(f.readlines())
                    Logger.success("Decryption successful!")
                    Logger.info(f"Output file: {output_file} ({size} bytes, {lines} lines)")
                    return True
                else:
                    Logger.error("Decrypted file is not XML (decryption may have failed)")
                    return False
        else:
            Logger.error("Decryption failed!")
            return False

    def encrypt_config(self, input_file: str, output_file: str,
                      password: str = ENCRYPTION_PASSWORD) -> bool:
        """
        Encrypt configuration file using OpenSSL AES-256-CBC

        Encryption command equivalent:
            openssl aes-256-cbc -md MD5 -k <password> -e -in <input> -out <output>

        Output format:
            Bytes 0-7:   "Salted__" (ASCII header)
            Bytes 8-15:  8-byte random salt
            Bytes 16+:   AES-256-CBC encrypted data

        Args:
            input_file: Path to XML configuration file
            output_file: Path to save encrypted backup file
            password: Encryption password (default: hardcoded password from firmware)

        Returns:
            True if encryption successful, False otherwise

        Note:
            Input file should be valid XML in TR-069 format

        Example:
            tool.encrypt_config("modified.xml", "backup.cfg")
        """
        Logger.header("Encrypting Configuration File")
        Logger.info(f"Input: {input_file}")
        Logger.info(f"Output: {output_file}")

        # Verify input file exists
        if not os.path.exists(input_file):
            Logger.error(f"Input file not found: {input_file}")
            return False

        # Check if file is XML
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
            first_line = f.readline().strip()
            if not first_line.startswith('<?xml'):
                Logger.warning("Input file does not appear to be XML")

        openssl_bin = self._get_openssl_cmd()
        used_openssl = False
        if openssl_bin:
            try:
                Logger.info("Encrypting via OpenSSL...")
                cmd = [
                    openssl_bin, 'aes-256-cbc',
                    '-md', 'MD5',
                    '-k', password,
                    '-e',
                    '-in', input_file,
                    '-out', output_file
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0 and os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                    used_openssl = True
                else:
                    Logger.warning(f"OpenSSL failed ({result.stderr}), attempting Python fallback...")
            except Exception as e:
                Logger.warning(f"OpenSSL execution failed ({e}), attempting Python fallback...")

        if not used_openssl:
            if HAS_CRYPTOGRAPHY:
                Logger.info("Encrypting via internal Python cryptography engine...")
                if not self._encrypt_config_py(input_file, output_file, password):
                    return False
            else:
                Logger.error("OpenSSL not found and cryptography package not installed.")
                return False

        # Verify output has correct format
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            with open(output_file, 'rb') as f:
                header = f.read(8)
                if header == b'Salted__':
                    size = os.path.getsize(output_file)
                    Logger.success("Encryption successful!")
                    Logger.info(f"Output file: {output_file} ({size} bytes)")
                    return True
                else:
                    Logger.error("Encrypted file format is incorrect")
                    return False
        else:
            Logger.error("Encryption failed!")
            return False

    def restore_backup(self, config_file: str) -> bool:
        """
        Upload and restore configuration to router

        WARNING: This will reboot the router!

        Process:
        1. Verify file is encrypted (must start with "Salted__")
        2. Create multipart/form-data request
        3. POST to /cgi-bin/backupRestore.cgi with:
           - tools_FW_UploadFile: encrypted file data
           - postflag: "1"
        4. Router applies configuration and reboots

        Form structure from router JavaScript:
            <form name="uiPostUpdateForm" method="post"
                  action="/cgi-bin/backupRestore.cgi"
                  enctype="multipart/form-data">
              <input type="file" name="tools_FW_UploadFile" />
              <input type="hidden" name="postflag" value="1" />
            </form>

        Args:
            config_file: Path to encrypted configuration file

        Returns:
            True if upload successful, False otherwise

        Note:
            - Configuration file MUST be encrypted first
            - Router will reboot after successful restore
            - Will need to login again after reboot

        Example:
            tool.encrypt_config("modified.xml", "backup.cfg")
            tool.login("admin", "password")
            tool.restore_backup("backup.cfg")
        """
        Logger.header("Restoring Configuration to Router")
        Logger.warning("This will overwrite router configuration and reboot the device!")

        # Verify file is encrypted
        with open(config_file, 'rb') as f:
            header = f.read(8)
            if header != b'Salted__':
                Logger.error("Configuration file must be encrypted first!")
                Logger.info(f"Use: {sys.argv[0]} encrypt -i <xml_file> -o <encrypted_file>")
                return False

        try:
            Logger.info("Uploading configuration...")
            backup_url = f"http://{self.router_ip}/cgi-bin/backupRestore.cgi"

            # Read file data
            with open(config_file, 'rb') as f:
                file_data = f.read()

            # Create multipart form data
            # This mimics the HTML form submission from the web interface
            boundary = '----WebKitFormBoundary' + os.urandom(16).hex()
            headers = {
                'Content-Type': f'multipart/form-data; boundary={boundary}',
                'Referer': backup_url
            }

            # Build multipart body
            # Format follows RFC 2388 (multipart/form-data)
            body = []
            body.append(f'--{boundary}'.encode())
            body.append(b'Content-Disposition: form-data; name="tools_FW_UploadFile"; filename="config.cfg"')
            body.append(b'Content-Type: application/octet-stream')
            body.append(b'')
            body.append(file_data)
            body.append(f'--{boundary}'.encode())
            body.append(b'Content-Disposition: form-data; name="postflag"')
            body.append(b'')
            body.append(b'1')
            body.append(f'--{boundary}--'.encode())
            body.append(b'')

            body_bytes = b'\r\n'.join(body)

            # Make request
            request = urllib.request.Request(
                backup_url,
                data=body_bytes,
                headers=headers
            )
            self.opener.open(request)

            Logger.success("Configuration uploaded!")
            Logger.warning("Router is rebooting... This may take 1-2 minutes.")
            Logger.info("You will need to log in again after reboot.")
            return True

        except Exception as e:
            Logger.error(f"Restore error: {e}")
            return False

    def extract_firmware(self, firmware_file: str, output_dir: str) -> bool:
        """
        Extract and analyze Zyxel firmware image

        Process:
        1. Use binwalk to extract UBI images from firmware
        2. Locate SquashFS root filesystem (ubi_r0.ubifs)
        3. Extract SquashFS using unsquashfs
        4. Search for encryption password in libCmd.so

        Firmware structure:
            - Format: UBI images within GPT partitions
            - Root FS: ubi_r0.ubifs (SquashFS compressed)
            - Config: ubi_Config.ubifs
            - Kernel: ubi_k0.ubifs
            - Encryption password location: /lib/MSTC/libCmd.so

        Args:
            firmware_file: Path to firmware binary file
            output_dir: Directory to extract firmware to

        Returns:
            True if extraction successful, False otherwise

        Requires:
            - binwalk: Firmware analysis and extraction
            - unsquashfs: SquashFS filesystem extraction
            - strings: Binary string extraction (optional)

        Example:
            tool.extract_firmware("firmware.bin", "./extracted")
        """
        Logger.header("Extracting Firmware")
        Logger.info(f"Firmware: {firmware_file}")
        Logger.info(f"Output directory: {output_dir}")

        # Check for required tools
        try:
            subprocess.run(['binwalk', '--version'], capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            Logger.error("binwalk is required for firmware extraction")
            Logger.info("Install with: brew install binwalk (macOS) or apt-get install binwalk (Linux)")
            return False

        try:
            subprocess.run(['unsquashfs', '-v'], capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            Logger.error("unsquashfs is required for filesystem extraction")
            Logger.info("Install with: brew install squashfs (macOS) or apt-get install squashfs-tools (Linux)")
            return False

        try:
            # Create output directory
            os.makedirs(output_dir, exist_ok=True)

            # Extract firmware using binwalk
            Logger.info("Running binwalk extraction...")
            subprocess.run(
                ['binwalk', '-e', firmware_file],
                cwd=output_dir,
                check=True
            )

            # Find SquashFS filesystem
            Logger.info("Locating root filesystem...")
            squashfs_files = list(Path(output_dir).rglob('*ubi_r0.ubifs'))

            if not squashfs_files:
                Logger.error("Could not find root filesystem")
                return False

            squashfs_file = str(squashfs_files[0])
            Logger.info(f"Found: {squashfs_file}")

            # Extract SquashFS
            Logger.info("Extracting SquashFS...")
            rootfs_dir = os.path.join(output_dir, 'rootfs')
            subprocess.run(
                ['unsquashfs', '-d', rootfs_dir, squashfs_file],
                capture_output=True
            )

            if os.path.exists(rootfs_dir):
                Logger.success("Firmware extracted successfully!")
                Logger.info(f"Root filesystem: {rootfs_dir}")

                # Search for encryption password in libCmd.so
                Logger.info("Searching for encryption password in firmware...")
                libcmd_path = os.path.join(rootfs_dir, 'lib', 'MSTC', 'libCmd.so')
                if os.path.exists(libcmd_path):
                    try:
                        result = subprocess.run(
                            ['strings', libcmd_path],
                            capture_output=True,
                            text=True
                        )
                        if ENCRYPTION_PASSWORD in result.stdout:
                            Logger.success(f"Found encryption password in libCmd.so: {ENCRYPTION_PASSWORD}")
                    except Exception:
                        pass

                return True
            else:
                Logger.error("Extraction failed!")
                return False

        except Exception as e:
            Logger.error(f"Extraction error: {e}")
            return False


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main():
    """
    Main entry point for command-line interface

    Parses command-line arguments and executes the requested operation.
    """
    parser = argparse.ArgumentParser(
        description='Zyxel Router Backup/Restore Tool v1.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:
  Download and decrypt backup:
    %(prog)s full-backup -u admin -p password -o config.xml

  Encrypt and restore configuration:
    %(prog)s full-restore -i modified.xml -u admin -p password

  Decrypt existing backup file:
    %(prog)s decrypt -i backup.cfg -o config.xml

  Encrypt configuration file:
    %(prog)s encrypt -i config.xml -o backup.cfg

  Extract firmware:
    %(prog)s extract -i firmware.bin -o ./extracted

  Use custom router IP:
    %(prog)s full-backup -u admin -p password -o config.xml -r 10.0.0.1

COMMANDS:
  download     Download encrypted backup from router
  decrypt      Decrypt an encrypted backup file
  encrypt      Encrypt a configuration file
  restore      Restore configuration to router (reboots!)
  full-backup  Download and decrypt in one step
  full-restore Encrypt and restore in one step
  extract      Extract and analyze firmware image

For detailed documentation, see the header comments in this script.
        """
    )

    parser.add_argument('command', choices=[
        'download', 'decrypt', 'encrypt', 'restore',
        'full-backup', 'full-restore', 'extract', 'disable-dhcp'
    ], help='Command to execute')

    parser.add_argument('-r', '--router', default=DEFAULT_ROUTER_IP,
                       help=f'Router IP address (default: {DEFAULT_ROUTER_IP})')
    parser.add_argument('-u', '--username', default=DEFAULT_USERNAME,
                       help=f'Router username (default: {DEFAULT_USERNAME})')
    parser.add_argument('-p', '--password', help='Router password')
    parser.add_argument('-i', '--input', help='Input file path')
    parser.add_argument('-o', '--output', help='Output file path')
    parser.add_argument('-k', '--key', default=ENCRYPTION_PASSWORD,
                       help='Encryption password (default: hardcoded password from firmware)')

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    # Create tool instance
    tool = ZyxelBackupTool(router_ip=args.router)

    # Execute command
    if args.command == 'download':
        if not args.password or not args.output:
            Logger.error("download requires --password and --output")
            sys.exit(1)
        if tool.login(args.username, args.password):
            success = tool.download_backup(args.output)
            sys.exit(0 if success else 1)
        sys.exit(1)

    elif args.command == 'decrypt':
        if not args.input or not args.output:
            Logger.error("decrypt requires --input and --output")
            sys.exit(1)
        success = tool.decrypt_backup(args.input, args.output, args.key)
        sys.exit(0 if success else 1)

    elif args.command == 'encrypt':
        if not args.input or not args.output:
            Logger.error("encrypt requires --input and --output")
            sys.exit(1)
        success = tool.encrypt_config(args.input, args.output, args.key)
        sys.exit(0 if success else 1)

    elif args.command == 'restore':
        if not args.password or not args.input:
            Logger.error("restore requires --password and --input")
            sys.exit(1)
        confirm = input("Are you sure you want to restore configuration? This will reboot the router (yes/no): ")
        if confirm.lower() != 'yes':
            Logger.info("Restore cancelled")
            sys.exit(0)
        if tool.login(args.username, args.password):
            success = tool.restore_backup(args.input)
            sys.exit(0 if success else 1)
        sys.exit(1)

    elif args.command == 'full-backup':
        if not args.password or not args.output:
            Logger.error("full-backup requires --password and --output")
            sys.exit(1)
        temp_encrypted = os.path.join(WORK_DIR, 'temp_backup.cfg')
        if tool.login(args.username, args.password):
            if tool.download_backup(temp_encrypted):
                if tool.decrypt_backup(temp_encrypted, args.output, args.key):
                    os.remove(temp_encrypted)
                    sys.exit(0)
        sys.exit(1)

    elif args.command == 'full-restore':
        if not args.password or not args.input:
            Logger.error("full-restore requires --password and --input")
            sys.exit(1)
        confirm = input("Are you sure you want to restore configuration? This will reboot the router (yes/no): ")
        if confirm.lower() != 'yes':
            Logger.info("Restore cancelled")
            sys.exit(0)
        temp_encrypted = os.path.join(WORK_DIR, 'temp_restore.cfg')
        if tool.encrypt_config(args.input, temp_encrypted, args.key):
            if tool.login(args.username, args.password):
                if tool.restore_backup(temp_encrypted):
                    sys.exit(0)
        sys.exit(1)

    elif args.command == 'extract':
        if not args.input or not args.output:
            Logger.error("extract requires --input and --output")
            sys.exit(1)
        success = tool.extract_firmware(args.input, args.output)
        sys.exit(0 if success else 1)

    elif args.command == 'disable-dhcp':
        if not args.password:
            Logger.error("disable-dhcp requires --password")
            sys.exit(1)
        confirm = input("Are you sure you want to disable LAN DHCP and reboot the router? (yes/no): ")
        if confirm.lower() != 'yes':
            Logger.info("Operation cancelled")
            sys.exit(0)
        temp_encrypted = os.path.join(WORK_DIR, 'temp_backup.cfg')
        temp_xml = args.output or 'config.xml'
        original_backup = 'config_original_backup.xml'
        if tool.login(args.username, args.password):
            if tool.download_backup(temp_encrypted):
                if tool.decrypt_backup(temp_encrypted, temp_xml, args.key):
                    with open(temp_xml, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    with open(original_backup, 'w', encoding='utf-8') as f:
                        f.write(content)
                    Logger.info(f"Original configuration saved to: {original_backup}")
                    # Patch DHCP and unlock GUI
                    content, n1 = re.subn(r'(<DHCPServerEnable[^>]*>)[01](</DHCPServerEnable>)', r'\g<1>0\g<2>', content)
                    content, n2 = re.subn(r'(<DHCPServerConfigurable[^>]*>)[01](</DHCPServerConfigurable>)', r'\g<1>1\g<2>', content)
                    content, n3 = re.subn(r'(<Alias[^>]*>CPE-create-ServerPool-1</Alias>\s*<Status[^>]*>)Enabled(</Status>)', r'\g<1>Disabled\g<2>', content)
                    Logger.info(f"Patched DHCPServerEnable ({n1}), DHCPServerConfigurable ({n2}), ServerPool ({n3})")
                    with open(temp_xml, 'w', encoding='utf-8') as f:
                        f.write(content)
                    temp_restore = os.path.join(WORK_DIR, 'temp_restore.cfg')
                    if tool.encrypt_config(temp_xml, temp_restore, args.key):
                        if tool.login(args.username, args.password):
                            if tool.restore_backup(temp_restore):
                                Logger.success("LAN DHCP disabled and router is rebooting!")
                                sys.exit(0)
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        Logger.warning("\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        Logger.error(f"Unexpected error: {e}")
        sys.exit(1)

