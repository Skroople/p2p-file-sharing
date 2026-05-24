Github Link: https://github.com/Skroople/cmp2204\_p2p-file-sharing/tree/main - Provided the extra wireshark captures here and a more detailed Readme.md file


How to Run the P2P File Sharing System

1 Ensure Python 3.x is installed on the system.

2 Install the required external dependencies by running: pip install pyDes customtkinter

3 Ensure that the machines are on the same Local Area Network (LAN).

4 Verify that the firewall allows traffic on Port 6000 (UDP) and Port 6001 (TCP).

5 Run the application from the terminal: python \[git commit -m]\_gui.py

6 Enter a username, select a file to host, and click "Initialize System".

7 Discovered network content will appear in the treeview. Select a file and choose either Standard or Secure Download.

Known Limitations

The application requires ports 6000 and 6001 to be strictly available. Running two instances on the same machine without using a VM or isolated network adapter will result in a TCP port collision.

The system is designed for LAN environments and relies on UDP broadcast (192.168.1.255), meaning it will not discover peers across different subnets or over the public internet without a VPN/ZeroTier.

