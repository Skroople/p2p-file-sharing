# 🌐 P2P File Sharing Application - Team git commit -m

> **CMP2204 Term Project** • A decentralized peer-to-peer file-sharing application built in Python.

This project features a robust backend using UDP for network discovery and TCP for file transfer, wrapped in a modern, dark-themed graphical user interface (GUI).

---

## ✨ Features

* 🖥️ **Modern GUI:** A sleek, dark-themed interface built with `customtkinter`, optimized for both macOS and Windows.
* 📡 **UDP Peer Discovery:** Broadcasts and listens on port `6000` every 8 seconds to maintain a live map of the network.
* ⚡ **TCP File Transfer:** Rapid, chunk-based downloading over port `6001`.
* 🔐 **Diffie-Hellman Key Exchange:** Establishes a shared secret for secure transfers ($p=907, g=7$).
* 🛡️ **DES Encryption:** Payloads are secured using `pyDes` (ECB mode, PKCS5 padding) and Base64 encoding.
* 🤝 **Altruistic Serving:** Nodes automatically seed chunks they have downloaded to assist the network.
* 🛑 **Dynamic Control:** Includes a "Stop System" feature to halt background threads and reconfigure settings on the fly.

## 🏗️ Architecture

The application adheres to a strict separation of concerns to ensure performance and maintainability:

- ⚙️ `[git commit -m]_p2p_file_sharing.py`: The core backend daemon. Handles multi-threading, socket programming, cryptography, and network routing.
- 🎨 `[git commit -m]_gui.py`: The frontend interface. Hooks into the backend instances to provide a visual dashboard without blocking critical network threads.

## 📦 Dependencies

This project requires **Python 3.x**. Install the required external libraries using pip:

```bash
pip install pyDes customtkinter
```

## 🚀 Usage

1. **Environment:** Ensure Python 3.x is installed. Install dependencies: `pip install pyDes customtkinter`.
2. **Network:** Connect to the same LAN. Ensure ports `6000` (UDP) and `6001` (TCP) are open in your firewall.
3. **Launch:** Run the graphical interface from your terminal:
   ```bash
   python [git commit -m]_gui.py
   ```
4. **Initialize:** Enter a username, select a file to host, and click **INITIALIZE SYSTEM**.
5. **Download:** Select a file from the "Network Content Discovery" list and choose **Standard** or **Secure Download**.
6. **Seed:** Keep the application running and do not delete the indexed chunk files (`_1`, `_2`, `_3`) to remain an active "altruistic" peer.
7. **Reset:** Use **STOP SYSTEM** if you need to change your username or host a different file.

## ⚠️ Known Limitations

* **Port Collisions:** The application requires ports `6000` and `6001` to be strictly available. Running two instances on the exact same machine without using a Virtual Machine or isolated network adapter will result in a TCP port collision and failed file transfers. Please test using two separate physical devices or a bridged VM.
* **Network Scope:** The system is designed specifically for LAN environments and relies on UDP broadcast (`192.168.1.255`) for peer discovery. It will not discover peers across different subnets or over the public internet without a virtual LAN setup (e.g., ZeroTier).

## 👥 Contributors

- Yiğit Erel
- Mehmet Eren Ekşi
