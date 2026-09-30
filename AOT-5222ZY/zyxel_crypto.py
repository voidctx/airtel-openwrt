#!/usr/bin/env python3

import sys
import os
import shutil
import hashlib
import subprocess
import argparse
from typing import Optional, Tuple

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding
    HAS_CRYPTOGRAPHY = True
except ImportError:
    HAS_CRYPTOGRAPHY = False

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
    data = b""
    d_i = b""
    while len(data) < key_len + iv_len:
        d_i = hashlib.md5(d_i + password + salt).digest()
        data += d_i
    return data[:key_len], data[key_len:key_len + iv_len]


ENCRYPTION_PASSWORD = "EwhJaD44DfprDOs7OXx9jzAtLg5PKtD8"

class Logger:
    @staticmethod
    def info(msg: str):
        print(f"{Colors.BLUE}[INFO]{Colors.NC} {msg}")

    @staticmethod
    def success(msg: str):
        print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {msg}")

    @staticmethod
    def warning(msg: str):
        print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {msg}")

    @staticmethod
    def error(msg: str):
        print(f"{Colors.RED}[ERROR]{Colors.NC} {msg}", file=sys.stderr)

    @staticmethod
    def header(msg: str):
        print(f"\n{Colors.GREEN}{'=' * 50}{Colors.NC}")
        print(f"{Colors.GREEN}{msg}{Colors.NC}")
        print(f"{Colors.GREEN}{'=' * 50}{Colors.NC}")


class ZyxelCrypto:
    def _get_openssl_cmd(self) -> Optional[str]:
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

    def decrypt_backup(self, input_file: str, output_file: str,password: str = ENCRYPTION_PASSWORD) -> bool:
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

    def encrypt_config(self, input_file: str, output_file: str,password: str = ENCRYPTION_PASSWORD) -> bool:
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

def main():
    parser = argparse.ArgumentParser(
        description="Zyxel Router Login / Configuration Crypto Utility"
    )

    parser.add_argument(
        "command",
        choices=["login", "decrypt", "encrypt"],
        help="Operation to execute"
    )
    parser.add_argument(
        "-r", "--router",
        default=DEFAULT_ROUTER_IP,
        help=f"Router IP address (default: {DEFAULT_ROUTER_IP})"
    )
    parser.add_argument(
        "-u", "--username",
        default=DEFAULT_USERNAME,
        help=f"Router username (default: {DEFAULT_USERNAME})"
    )
    parser.add_argument(
        "-p", "--password",
        help="Router password"
    )
    parser.add_argument(
        "-i", "--input",
        help="Input file path"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output file path"
    )
    parser.add_argument(
        "-k", "--key",
        default=ENCRYPTION_PASSWORD,
        help="Encryption password (default: hardcoded password from firmware)"
    )

    args = parser.parse_args()
    tool = ZyxelBackupTool(router_ip=args.router)

    if args.command == "login":
        if not args.password:
            Logger.error("login requires --password")
            sys.exit(1)

        success = tool.login(args.username, args.password)
        sys.exit(0 if success else 1)

    if args.command == "decrypt":
        if not args.input or not args.output:
            Logger.error("decrypt requires --input and --output")
            sys.exit(1)

        success = tool.decrypt_backup(
            args.input,
            args.output,
            args.key
        )
        sys.exit(0 if success else 1)

    if args.command == "encrypt":
        if not args.input or not args.output:
            Logger.error("encrypt requires --input and --output")
            sys.exit(1)

        success = tool.encrypt_config(
            args.input,
            args.output,
            args.key
        )
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        Logger.warning("\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        Logger.error(f"Unexpected error: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Zyxel Configuration Encryption / Decryption Utility"
    )
    parser.add_argument("command", choices=["decrypt", "encrypt"])
    parser.add_argument("-i", "--input", required=True, help="Input file path")
    parser.add_argument("-o", "--output", required=True, help="Output file path")
    parser.add_argument(
        "-k", "--key",
        default=ENCRYPTION_PASSWORD,
        help="Encryption password (default: hardcoded password from firmware)"
    )

    args = parser.parse_args()
    tool = ZyxelCrypto()

    if args.command == "decrypt":
        success = tool.decrypt_backup(args.input, args.output, args.key)
    else:
        success = tool.encrypt_config(args.input, args.output, args.key)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
