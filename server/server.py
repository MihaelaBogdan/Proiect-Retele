import socket, threading, json, struct, logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [SISTEM] - %(message)s')
log = logging.getLogger("server")

class Server:
    def __init__(self, host='0.0.0.0', port=5000):
        self.clients = {} 
        self.registered_users = {} 
        self.lock = threading.Lock()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def send_msg(self, sock, t, d=None):
        try:
            payload = json.dumps({"type": t, "data": d}).encode('utf-8')
            sock.sendall(struct.pack('!I', len(payload)) + payload)
        except: pass

    def recv_msg(self, sock):
        try:
            h = b""
            while len(h) < 4:
                c = sock.recv(4 - len(h))
                if not c: return None
                h += c
            l = struct.unpack('!I', h)[0]
            p = b""
            while len(p) < l:
                c = sock.recv(l - len(p))
                if not c: return None
                p += c
            return json.loads(p.decode('utf-8'))
        except: return None

    def handle_client(self, sock, addr):
        log.info(f"Conexiune noua de la: {addr}")
        username = None
        try:
            msg = self.recv_msg(sock)
            if not msg or msg.get('type') != 'AUTH': return
            d = msg['data']
            username, password, files = d['username'], d['password'], d['files']
            with self.lock:
                if username in self.registered_users:
                    if self.registered_users[username] != password:
                        log.warning(f"Parola gresita pentru '{username}'")
                        self.send_msg(sock, "ERROR", {"message": "Parola gresita"})
                        return
                else: self.registered_users[username] = password
                if username in self.clients:
                    self.send_msg(sock, "ERROR", {"message": "Utilizator deja online"})
                    return
                log.info(f"--- AUTENTIFICARE REUSITA: '{username}' ---")
                for u, info in self.clients.items(): self.send_msg(info['socket'], "NOTIFY_CONNECT", {"username": username, "files": files})
                others = {u: info['files'] for u, info in self.clients.items()}
                self.clients[username] = {"socket": sock, "files": files}
                self.send_msg(sock, "SYNC_LIST", {"files": others})

            while True:
                msg = self.recv_msg(sock)
                if not msg: break
                t, d = msg['type'], msg.get('data')
                if t == "FILE_ADDED":
                    log.info(f"[{username}] A ADAUGAT: {d['filename']}")
                    with self.lock: self.clients[username]['files'].append(d['filename'])
                    self.broadcast("FILE_ADDED", {"username": username, "filename": d['filename']}, exclude=username)
                elif t == "FILE_REMOVED":
                    log.info(f"[{username}] A STERS: {d['filename']}")
                    with self.lock: 
                        if d['filename'] in self.clients[username]['files']: self.clients[username]['files'].remove(d['filename'])
                    self.broadcast("FILE_REMOVED", {"username": username, "filename": d['filename']}, exclude=username)
                elif t == "DOWNLOAD_REQ":
                    log.info(f"[{username}] CERE {d['filename']} de la {d['target_user']}")
                    target = d['target_user']
                    if target in self.clients:
                        if d['filename'] in self.clients[target]['files']:
                            self.send_msg(self.clients[target]['socket'], "UPLOAD_REQ", {"requester": username, "filename": d['filename']})
                        else:
                            self.send_msg(sock, "ERROR", {"message": f"Utilizatorul '{target}' nu partajeaza fisierul '{d['filename']}'."})
                    else:
                        self.send_msg(sock, "ERROR", {"message": f"Utilizatorul '{target}' nu este conectat."})
                elif t in ["FILE_CHUNK", "FILE_END"]:
                    if t == "FILE_END": log.info(f"[{username}] A FINALIZAT transferul pentru {d['filename']} catre {d['requester']}")
                    req = d['requester']
                    if req in self.clients:
                        self.send_msg(self.clients[req]['socket'], t, {
                            "sender": username, 
                            "filename": d['filename'], 
                            "content": d.get('content', '')
                        })
        finally: self.cleanup(username, sock)

    def broadcast(self, t, d, exclude):
        with self.lock:
            for u, info in self.clients.items():
                if u != exclude: self.send_msg(info['socket'], t, d)

    def cleanup(self, user, sock):
        sock.close()
        if user:
            with self.lock:
                if user in self.clients: del self.clients[user]
            log.info(f"DECONECTARE: {user}")
            self.broadcast("NOTIFY_DISCONNECT", {"username": user}, exclude=None)

    def start(self):
        self.sock.bind(('0.0.0.0', 5000))
        self.sock.listen(10)
        log.info("=== SERVER ACTIV PE PORTUL 5000 ===")
        while True:
            s, a = self.sock.accept()
            threading.Thread(target=self.handle_client, args=(s, a), daemon=True).start()

if __name__ == "__main__":
    Server().start()
