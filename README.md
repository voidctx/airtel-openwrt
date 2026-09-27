# Zyxel AOT-5221ZY Backup/Restore Decryption & Encryption Tool

This repository contains the setup and tool based on the GitHub Gist [ankurpandeyvns/0f72eb73f5724f83b9ceebe079162505](https://gist.github.com/ankurpandeyvns/0f72eb73f5724f83b9ceebe079162505).

It enables downloading, decrypting, encrypting, and restoring configuration files for Zyxel routers (such as the **AOT-5221ZY** router commonly used by ISPs).

---

## Features & Highlights

- **Full Backup Download & Decrypt**: Authenticate to the router web interface (`/cgi-bin/login_advance.cgi`), trigger config generation, download `romfile.cfg`, and decrypt it to readable XML.
- **Encrypt & Restore**: Encrypt modified TR-069 XML configs into the router's OpenSSL-salted format and push back to `/cgi-bin/backupRestore.cgi`.
- **Dual Decryption/Encryption Engine**:
  - Automatically locates and uses **OpenSSL** (including Git for Windows' OpenSSL).
  - Built-in **pure-Python fallback** (`cryptography` + MD5 key derivation `EVP_BytesToKey`) ensuring seamless execution even if OpenSSL CLI is not in PATH.
- **Firmware Analysis**: Extract UBI/SquashFS images and search for hardcoded keys (requires `binwalk` & `unsquashfs`).

---

## Router & Encryption Details

- **Device**: Zyxel AOT-5221ZY
- **Default Gateway IP**: `192.168.1.1`
- **Default Username**: `admin`
- **Algorithm**: `AES-256-CBC`
- **Key Derivation**: `MD5` (`OpenSSL EVP_BytesToKey`)
- **Hardcoded Password**: `EwhJaD44DfprDOs7OXx9jzAtLg5PKtD8` (from `/lib/MSTC/libCmd.so`)

---

## Quick Start & Usage

Run using either `python zyxel_backup_restore.py` or `python zyxel_backup_tool.py`:

### 1. Download and Decrypt Backup in One Step
```bash
python zyxel_backup_restore.py full-backup -u admin -p <ROUTER_PASSWORD> -o config.xml
```

### 2. Decrypt an Existing Backup File
```bash
python zyxel_backup_restore.py decrypt -i backup.cfg -o config.xml
```

### 3. Encrypt an XML Configuration File
```bash
python zyxel_backup_restore.py encrypt -i config.xml -o backup.cfg
```

### 4. Restore Configuration to Router (⚠️ Reboots Router)
```bash
python zyxel_backup_restore.py full-restore -i modified.xml -u admin -p <ROUTER_PASSWORD>
```

### 5. Custom Router IP
```bash
python zyxel_backup_restore.py full-backup -r 192.168.1.1 -u admin -p <ROUTER_PASSWORD> -o config.xml
```

---

## CLI Options Reference

| Argument | Description | Default |
|---|---|---|
| `command` | `download`, `decrypt`, `encrypt`, `restore`, `full-backup`, `full-restore`, `extract` | Required |
| `-r`, `--router` | Router IP address | `192.168.1.1` |
| `-u`, `--username` | Router admin username | `admin` |
| `-p`, `--password` | Router admin password | |
| `-i`, `--input` | Input file path | |
| `-o`, `--output` | Output file path | |
| `-k`, `--key` | Encryption key | `EwhJaD44DfprDOs7OXx9jzAtLg5PKtD8` |