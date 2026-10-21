import socket
import json
import base64
import threading
import time
import os
import secrets
import pyDes

DH_PRIME = 907
DH_BASE = 7

def _get_broadcast_addr():
    import platform, subprocess, re, struct
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()

        system = platform.system()
        if system == 'Windows':
            r = subprocess.run(['ipconfig'], capture_output=True, text=True, check=True)
            for block in re.split(r'\n(?=\S)', r.stdout):
                if ip not in block:
                    continue
                m = re.search(r'Subnet Mask[ .:]+(\d+\.\d+\.\d+\.\d+)', block)
                if m:
                    parts = list(map(int, m.group(1).split('.')))
                    nm = (parts[0]<<24)|(parts[1]<<16)|(parts[2]<<8)|parts[3]
                    ip_i = struct.unpack('>I', socket.inet_aton(ip))[0]
                    return socket.inet_ntoa(struct.pack('>I', ip_i | (~nm & 0xffffffff)))
        else:
            r = subprocess.run(['ifconfig'], capture_output=True, text=True, check=True)
            for m in re.finditer(r'inet (\S+) netmask (0x[0-9a-f]+) broadcast (\S+)', r.stdout):
                if m.group(1) == ip:
                    return m.group(3)
            for m in re.finditer(r'inet (\S+) netmask (0x[0-9a-f]+)', r.stdout):
                if m.group(1) == ip:
                    nm = int(m.group(2), 16)
                    ip_i = struct.unpack('>I', socket.inet_aton(ip))[0]
                    return socket.inet_ntoa(struct.pack('>I', ip_i | (~nm & 0xffffffff)))
    except:
        pass
    return '255.255.255.255'

class PeerNode:
    def __init__(self, username=None, file_path=None, dl_path=None):
        self.username = username or input("Enter your username: ").strip()
        if not self.username:
            raise ValueError("Username cannot be empty")

        self.file_path = file_path
        if not self.file_path:
            print("Enter the path to the file you want to host:")
            self.file_path = input().strip()

        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"File not found: {self.file_path}")

        self.dl_path = dl_path or os.getcwd()
        self.file_name = os.path.basename(self.file_path)
        self.chunks = self._split_file_into_chunks()
        print(f"Split '{self.file_name}' into {len(self.chunks)} chunks")

        self.ip_to_username = {}
        self.username_to_ip = {}
        self.content_dict = {}

        self.running = False
        self.threads = []

        self.download_log_file = "download_log.txt"
        self.upload_log_file = "upload_log.txt"

    def _split_file_into_chunks(self):
        with open(self.file_path, 'rb') as f:
            data = f.read()

        chunk_size = len(data) // 3
        if len(data) % 3 != 0:
            chunk_size += 1

        chunks = []
        for i in range(3):
            start = i * chunk_size
            end = start + chunk_size
            chunk_name = f"{self.file_name}_{i + 1}"
            chunk_data = data[start:end]
            chunks.append((chunk_name, chunk_data))
            
            # Store them as separate files locally immediately as per specification
            with open(chunk_name, 'wb') as chunk_file:
                chunk_file.write(chunk_data)
                
        return chunks

    def start(self):
        self.running = True
        self.threads = [
            threading.Thread(target=self._chunk_announcer, daemon=True, name="ChunkAnnouncer"),
            threading.Thread(target=self._content_discovery, daemon=True, name="ContentDiscovery"),
            threading.Thread(target=self._chunk_uploader, daemon=True, name="ChunkUploader"),
            threading.Thread(target=self._dictionary_wiper, daemon=True, name="DictionaryWiper"),
        ]

        for t in self.threads:
            t.start()
            print(f"Started {t.name}")

        print(f"\nPeerNode '{self.username}' running with {len(self.chunks)} chunks.")
        print("Press Ctrl+C to stop.\n")

    def _chunk_announcer(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        broadcast_addr = (_get_broadcast_addr(), 6000)

        while self.running:
            chunk_names = set([chunk[0] for chunk in self.chunks])
            
            # Scan for altruistic chunks
            if os.path.exists(self.dl_path):
                for f in os.listdir(self.dl_path):
                    if f.endswith('_1') or f.endswith('_2') or f.endswith('_3'):
                        chunk_names.add(f)

            payload = json.dumps({
                "username": self.username,
                "chunks": list(chunk_names)
            })

            try:
                sock.sendto(payload.encode('utf-8'), broadcast_addr)
            except Exception as e:
                print(f"[ANNOUNCER] Error: {e}")

            time.sleep(8)

    def _content_discovery(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', 6000))
        sock.settimeout(1)

        while self.running:
            try:
                data, addr = sock.recvfrom(4096)
                msg = json.loads(data.decode('utf-8'))
                peer_username = msg.get("username", "")
                peer_chunks = msg.get("chunks", [])

                if peer_username == self.username:
                    continue

                self.ip_to_username[addr[0]] = peer_username
                self.username_to_ip[peer_username] = addr[0]

                new_chunks_added = False
                for chunk in peer_chunks:
                    if chunk not in self.content_dict:
                        self.content_dict[chunk] = []
                    if peer_username not in self.content_dict[chunk]:
                        self.content_dict[chunk].append(peer_username)
                        new_chunks_added = True
                        
                if new_chunks_added:
                    print(f"[DISCOVERY] {peer_username} : {', '.join(peer_chunks)}")

            except socket.timeout:
                continue
            except json.JSONDecodeError:
                continue
            except Exception as e:
                if self.running:
                    print(f"[DISCOVERY] Error: {e}")

    def _dictionary_wiper(self):
        while self.running:
            time.sleep(60)
            self.content_dict.clear()
            print("[DISCOVERY] Content dictionary wiped.")

    def _chunk_uploader(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', 6001))
        sock.listen(5)
        print("[UPLOADER] Listening on TCP port 6001...")

        def handle_client(client_sock, addr):
            try:
                client_sock.settimeout(300)
                data = b""
                while True:
                    chunk = client_sock.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                    try:
                        json.loads(data.decode('utf-8'))
                        break
                    except json.JSONDecodeError:
                        continue

                msg = json.loads(data.decode('utf-8'))
                client_name = self.ip_to_username.get(addr[0], "Unknown")

                if "key" in msg:
                    shared_secret = self._handle_dh_key_exchange(client_sock, msg["key"])
                    if shared_secret is not None:
                        sec_data = b""
                        while True:
                            chunk = client_sock.recv(8192)
                            if not chunk:
                                break
                            sec_data += chunk
                            try:
                                json.loads(sec_data.decode('utf-8'))
                                break
                            except json.JSONDecodeError:
                                continue
                        sec_msg = json.loads(sec_data.decode('utf-8'))
                        if "requested_secured_content" in sec_msg:
                            self._handle_secured_download(client_sock, sec_msg["requested_secured_content"], shared_secret, client_name)
                elif "requested_content" in msg:
                    self._handle_unsecure_download(client_sock, msg["requested_content"], client_name)

            except Exception as e:
                print(f"[UPLOADER] Error handling {addr}: {e}")
            finally:
                try:
                    client_sock.close()
                except:
                    pass

        while self.running:
            try:
                sock.settimeout(1)
                try:
                    client_sock, addr = sock.accept()
                    threading.Thread(target=handle_client, args=(client_sock, addr), daemon=True).start()
                except socket.timeout:
                    continue
            except Exception as e:
                if self.running:
                    print(f"[UPLOADER] Error: {e}")

    def _handle_dh_key_exchange(self, sock, client_key):
        try:
            client_public = int(client_key)
            server_private = secrets.randbelow(DH_PRIME - 2) + 2
            server_public = pow(DH_BASE, server_private, DH_PRIME)
            shared_secret = pow(client_public, server_private, DH_PRIME)

            response = json.dumps({"key": str(server_public)})
            sock.sendall(response.encode('utf-8'))

            return shared_secret

        except Exception as e:
            print(f"[DH] Error: {e}")
            sock.close()
            return None

    def _serve_chunk(self, chunk_name):
        for chunk_tuple in self.chunks:
            if chunk_tuple[0] == chunk_name:
                return chunk_tuple[1]

        chunk_path = os.path.join(self.dl_path, chunk_name)
        if os.path.exists(chunk_path) and os.path.isfile(chunk_path):
            try:
                with open(chunk_path, 'rb') as f:
                    return f.read()
            except Exception as e:
                print(f"[UPLOADER] Error reading altruistic chunk {chunk_name}: {e}")

        return None

    def _handle_secured_download(self, sock, requested_chunk, shared_secret, recipient_name):
        chunk_data = self._serve_chunk(requested_chunk)

        if chunk_data is None:
            sock.close()
            return

        key_str = str(shared_secret).zfill(8)[:8]
        key_bytes = key_str.encode('utf-8')

        des = pyDes.des(key_bytes, pyDes.ECB, padmode=pyDes.PAD_PKCS5)
        encrypted = des.encrypt(chunk_data)
        b64_encrypted = base64.b64encode(encrypted).decode('utf-8')

        response = json.dumps({
            "chunk_name": requested_chunk,
            "encrypted_chunk": b64_encrypted
        })
        sock.sendall(response.encode('utf-8'))

        self._log_upload(requested_chunk, recipient_name)
        print(f"[UPLOADER] SENT {requested_chunk} TO {recipient_name}")
        sock.close()

    def _handle_unsecure_download(self, sock, requested_chunk, recipient_name):
        chunk_data = self._serve_chunk(requested_chunk)

        if chunk_data is None:
            sock.close()
            return

        b64_data = base64.b64encode(chunk_data).decode('utf-8')

        response = json.dumps({
            "chunk_name": requested_chunk,
            "data": b64_data
        })
        sock.sendall(response.encode('utf-8'))

        self._log_upload(requested_chunk, recipient_name)
        print(f"[UPLOADER] SENT {requested_chunk} TO {recipient_name}")
        sock.close()

    def _log_upload(self, chunk_name, recipient_name):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(self.upload_log_file, "a") as f:
            f.write(f"[{timestamp}] {chunk_name} {recipient_name} SENT\n")

    def _download_unsecure_chunk(self, ip, chunk_name):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, 6001))
        sock.settimeout(120)

        request = json.dumps({"requested_content": chunk_name})
        sock.sendall(request.encode('utf-8'))

        data = b""
        while True:
            chunk = sock.recv(8192)
            if not chunk:
                break
            data += chunk
            try:
                msg = json.loads(data.decode('utf-8'))
                break
            except json.JSONDecodeError:
                continue

        sock.close()

        if "data" in msg:
            chunk_data = base64.b64decode(msg["data"])
            self._log_download(chunk_name, ip)
            return chunk_data

        return None

    def _download_secure_chunk(self, ip, chunk_name):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((ip, 6001))
        sock.settimeout(300)

        client_private = secrets.randbelow(904) + 2
        client_public = pow(DH_BASE, client_private, DH_PRIME)

        request = json.dumps({"key": str(client_public)})
        sock.sendall(request.encode('utf-8'))

        response = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response += chunk
            try:
                msg = json.loads(response.decode('utf-8'))
                break
            except json.JSONDecodeError:
                continue

        if "key" not in msg:
            sock.close()
            return None

        server_public = int(msg["key"])
        shared_secret = pow(server_public, client_private, DH_PRIME)

        key_str = str(shared_secret).zfill(8)[:8]
        key_bytes = key_str.encode('utf-8')

        request = json.dumps({"requested_secured_content": chunk_name})
        sock.sendall(request.encode('utf-8'))

        response = b""
        while True:
            chunk = sock.recv(8192)
            if not chunk:
                break
            response += chunk
            try:
                msg = json.loads(response.decode('utf-8'))
                break
            except json.JSONDecodeError:
                continue

        sock.close()

        if "encrypted_chunk" in msg:
            encrypted = base64.b64decode(msg["encrypted_chunk"])
            des = pyDes.des(key_bytes, pyDes.ECB, padmode=pyDes.PAD_PKCS5)
            chunk_data = des.decrypt(encrypted)
            self._log_download(chunk_name, ip)
            return chunk_data

        return None

    def _log_download(self, chunk_name, ip):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(self.download_log_file, "a") as f:
            f.write(f"[{timestamp}] {chunk_name} {ip} RECEIVED\n")

    def stop(self):
        print("\nShutting down...")
        self.running = False
        for t in self.threads:
            if t.is_alive():
                t.join(timeout=1)
        print("Shutdown complete.")

if __name__ == "__main__":
    try:
        peer = PeerNode()
        peer.start()
    except KeyboardInterrupt:
        print("\nInterrupted.")
    except Exception as e:
        print(f"Error: {e}")