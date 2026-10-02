# Zyxel AOT-5222ZY — Root SSH Unlock

This guide documents the configuration-based unlock procedure for the **Zyxel AOT-5222ZY** supplied by Airtel.

The procedure does **not require replacing the firmware**.

---

## Overview

The complete process is:

```text
AOT-5222ZY WebUI
       │
       ▼
Maintenance
       │
       ▼
Browser DevTools → Console
       │
       ▼
backup_settings()
       │
       ▼
Download configuration
       │
       ▼
Decrypt with the supplied Python tool
       │
       ▼
Modify configuration
       │
       ▼
Re-encrypt configuration
       │
       ▼
Paste console.js into DevTools Console
       │
       ▼
File picker appears
       │
       ▼
Select re-encrypted configuration
       │
       ▼
Restore configuration
       │
       ▼
Reboot / reconnect
       │
       ▼
SSH
       │
       ▼
root access
```

---

# 1. Open the Maintenance page

Log into the AOT-5222ZY WebUI.

Navigate to:

```text
Maintenance
```

Keep this page open.

---

# 2. Open Developer Tools

Open your browser's Developer Tools.

For Chromium-based browsers:

```text
F12
```

or:

```text
Ctrl + Shift + I
```

Open:

```text
Console
```

You may need to enable pasting into the console if the browser displays a self-XSS warning.

---

# 3. Download the original configuration

In the DevTools console, execute:

```javascript
backup_settings()
```

The router should generate and download its configuration backup.

Keep the original file.

**Do not modify the original backup.**

Make a separate working copy.

For example:

```text
original.cfg
working.cfg
```

The original backup is your recovery reference.

---

# 4. Decrypt the configuration

Use the Python decryption tool included with this repository.

The exact command depends on the script shipped in this directory.

Conceptually:

```text
encrypted configuration
        ↓
Python decryptor
        ↓
decrypted XML
```

Example:

```bash
python zyxel_crypto.py decrypt -i working.cfg -o config.xml
```

After decryption, verify that the output is a valid configuration before making modifications.

**Do not overwrite your original backup.**

---

# 5. Modify the configuration

Modify the decrypted configuration according to the unlock procedure.

The objective is to expose the existing privileged management functionality, including SSH access.

Keep the changes minimal.

A useful workflow is:

```text
original
   │
   └── untouched backup

working copy
   │
   ├── decrypt
   ├── modify
   └── encrypt
```

Do not randomly change unrelated parameters.

---

# 6. Re-encrypt the configuration

After modification, use the Python tool to encrypt the configuration again.

Conceptually:

```text
modified XML
        ↓
Python encryptor
        ↓
re-encrypted configuration
```

Example:

```bash
python zyxel_crypto.py encrypt -i config.xml -o unlocked.cfg
```

The resulting file is the file that must be restored to the router.

Do **not** upload the decrypted XML/configuration directly.

---

# 7. Prepare `console.js`

This directory contains the browser-side restore helper:

```text
console.js
```

Open it as text.

Copy the **entire contents** of `console.js`.

Do not modify the JavaScript unless the device-specific documentation says otherwise.

---

# 8. Upload the modified configuration

Return to the AOT-5222ZY WebUI's Maintenance page.

Open DevTools:

```text
F12
```

Then:

```text
Console
```

Paste the complete contents of:

```text
console.js
```

into the console and execute it.

The script will invoke the WebUI's configuration-upload mechanism.

A file picker should appear.

---

# 9. Select the re-encrypted file

When the file picker appears, select the **recently re-encrypted configuration file**.

Allow the router to process the configuration.

If the router reboots, wait for it to become reachable again before attempting SSH.

---

# 10. Connect through SSH

After the configuration has been restored and the router is reachable, connect using SSH.

The AOT-5222ZY uses an older RSA SSH host-key/signature configuration that modern OpenSSH clients reject by default.

If your client reports an error concerning `ssh-rsa`, explicitly enable the legacy RSA algorithm for this connection.

For example:

```bash
ssh \
  -o HostKeyAlgorithms=+ssh-rsa \
  -o PubkeyAcceptedAlgorithms=+ssh-rsa \
  root@192.168.1.1
```

If only the host-key algorithm is rejected, the shorter form may be sufficient:

```bash
ssh \
  -o HostKeyAlgorithms=+ssh-rsa \
  root@192.168.1.1
```

Use the exact root credentials produced by the configuration modification.

**Do not globally enable `ssh-rsa` in your SSH configuration.** Apply the compatibility option to this device/connection only.

---

# 11. Verify access

Once connected:

```bash
id
```

You should see a privileged/root identity.

Then:

```bash
uname -a
```

and:

```bash
cat /etc/openwrt_release 2>/dev/null
```

can be useful for identifying the underlying firmware.

You can also inspect:

```bash
cat /proc/version
```

and:

```bash
ls /etc/config
```

to confirm the underlying Linux/OpenWrt environment.

---

# Recovery

Keep the untouched configuration backup.

If your modified configuration causes unexpected behavior, restore the original configuration using the router's normal configuration restore mechanism.

Do not experiment with firmware flashing unless you have first established a reliable recovery method for the specific hardware revision.

---

# Security considerations

After obtaining root access, the device is no longer restricted to the capabilities exposed by the ISP WebUI.

Treat the SSH interface accordingly.

If SSH is enabled only for local administration, restrict it to the LAN interface where possible.

Avoid exposing port 22 directly to the Internet.

Also remember that changes made at root level can affect:

- GPON/PON functionality
- ISP provisioning
- VLAN configuration
- routing
- firewalling
- Wi-Fi
- TR-069/remote management
- firmware updates
- device recovery

Make one change at a time and keep backups.