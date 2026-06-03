# AGENTS.md — cmp2204_p2p-file-sharing

## Project

CMP2204 term project: LAN peer-to-peer file sharing with optional DES encryption.
Python 3.x, no build system, no tests, no linter/formatter/typechecker.

## Files

- `[git commit -m]_gui.py` — GUI entrypoint (run this)
- `[git commit -m]_p2p_file_sharing.py` — backend `PeerNode` class
- GUI uses `importlib` to load the backend by absolute path (filename has special chars unsupported by Python imports).

## Commands

```bash
pip install pyDes customtkinter
python [git commit -m]_gui.py
```

## Network

| Port | Protocol | Purpose          |
|------|----------|------------------|
| 6000 | UDP      | Peer discovery   |
| 6001 | TCP      | File transfer    |

- Broadcast address hardcoded to `192.168.1.255:6000` — LAN only.
- Content discovery dict wiped every 60 s by `DictionaryWiper` thread.

## Crypto

- Diffie-Hellman: `p=907`, `g=7` (hardcoded in `PeerNode` top-level constants)
- DES/ECB with PKCS5 padding via `pyDes`, payload Base64-encoded.

## Chunking

Files split into 3 chunks on init. Chunk files saved as `<filename>_1`, `<filename>_2`, `<filename>_3` in CWD. Downloaded chunks are re-seeded altruistically.

## Logs

- `download_log.txt` — chunk download records
- `upload_log_file.txt` — chunk upload records (note: `_file` typo is intentional)
- Both in `.gitignore`.

## Gotchas

- Cannot run two instances on the same machine (TCP port 6001 collision).
- GUI import already resolved via `importlib` — no symlink needed.
