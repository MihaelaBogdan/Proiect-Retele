import socket, threading, json, struct, os, base64, time, sys
import urllib.request, zipfile

class Client:
    def __init__(self, host='127.0.0.1'):
        self.host = host
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.global_files = {} 
        self.running = True
        self.local_files = set()

    def connect(self):
        try:
            self.sock.connect((self.host, 5000))
            print("\n=== SISTEM PARTAJARE PROFESIONAL ===")
            self.username = input("Username: ")
            self.password = input("Parola: ")
            self.shared_dir = f"shared_{self.username}"
            if not os.path.exists(self.shared_dir): os.makedirs(self.shared_dir)
            self.local_files = set(self.get_local_files())
            self.send_msg("AUTH", {"username": self.username, "password": self.password, "files": list(self.local_files)})
            msg = self.recv_msg()
            if msg and msg['type'] == "ERROR":
                print(f"\n[EROARE] {msg['data']['message']}"); self.sock.close(); return
            if msg and msg['type'] == "SYNC_LIST":
                self.global_files = msg['data'].get('files', {})
                print("\n[OK] Conectat!")
            threading.Thread(target=self.listen, daemon=True).start()
            threading.Thread(target=self.monitor, daemon=True).start()
            self.menu()
        except Exception as e: print(f"Eroare: {e}")

    def send_msg(self, t, d=None):
        payload = json.dumps({"type": t, "data": d}).encode('utf-8')
        self.sock.sendall(struct.pack('!I', len(payload)) + payload)

    def recv_msg(self):
        try:
            h = self.sock.recv(4)
            if not h: return None
            l = struct.unpack('!I', h)[0]
            p = b""
            while len(p) < l:
                c = self.sock.recv(l - len(p)); p += c
            return json.loads(p.decode('utf-8'))
        except: return None

    def listen(self):
        while self.running:
            msg = self.recv_msg()
            if not msg: break
            t, d = msg.get('type'), msg.get('data')
            if t == "NOTIFY_CONNECT": 
                self.global_files[d['username']] = d['files']
                print(f"\n[+] {d['username']} s-a conectat.")
            elif t == "NOTIFY_DISCONNECT": 
                if d['username'] in self.global_files: del self.global_files[d['username']]
                print(f"\n[-] {d['username']} a plecat.")
            elif t == "FILE_ADDED": 
                if d['username'] in self.global_files: self.global_files[d['username']].append(d['filename'])
                print(f"\n[*] {d['username']} a adaugat: {d['filename']}")
            elif t == "FILE_REMOVED":
                if d['username'] in self.global_files and d['filename'] in self.global_files[d['username']]:
                    self.global_files[d['username']].remove(d['filename'])
                print(f"\n[*] {d['username']} a retras: {d['filename']}")
            elif t == "UPLOAD_REQ": self.handle_upload(d['requester'], d['filename'])
            elif t == "FILE_DATA": self.save_file(d['sender'], d['filename'], d['content'])
            elif t == "ERROR": print(f"\n[SERVER] {d['message']}")
        self.running = False

    def monitor(self):
        while self.running:
            current = set(self.get_local_files())
            for f in current - self.local_files: self.send_msg("FILE_ADDED", {"filename": f})
            for f in self.local_files - current: self.send_msg("FILE_REMOVED", {"filename": f})
            self.local_files = current
            time.sleep(1)

    def handle_upload(self, req, fname):
        path = os.path.join(self.shared_dir, fname)
        if os.path.exists(path):
            with open(path, "rb") as f: content = base64.b64encode(f.read()).decode('utf-8')
            self.send_msg("FILE_DATA", {"requester": req, "filename": fname, "content": content})

    def save_file(self, sender, fname, content):
        nume_nou = f"download_{fname}"
        path = os.path.join(self.shared_dir, nume_nou)
        with open(path, "wb") as f: f.write(base64.b64decode(content))
        self.send_msg("FILE_ADDED", {"filename": nume_nou})
        print(f"\n[OK] Descarcat '{fname}' de la {sender}. Salvat ca '{nume_nou}'.")

    def menu(self):
        while self.running:
            print(f"\nMENIU [{self.username}] | 1.Lista | 2.Download | 3.Exit | 4.Creaza | 5.IMAGINI | 6.ZIP")
            c = input("> ")
            if c == "1":
                print("\n--- LISTA REȚEA ---")
                print(f" [EU] {self.username}: {list(self.local_files)}")
                for u, fs in self.global_files.items(): print(f" [RETEA] {u}: {fs}")
            elif c == "2":
                u, f = input("De la cine: "), input("Fisier: ")
                self.send_msg("DOWNLOAD_REQ", {"target_user": u, "filename": f})
            elif c == "3":
                self.running = False; self.sock.close(); sys.exit(0)
            elif c == "4":
                n, txt = input("Nume: "), input("Continut: ")
                with open(os.path.join(self.shared_dir, n), "w") as f: f.write(txt)
                print(f"[OK] Creat: {n}")
            elif c == "5":
                url, n = input("URL Imagine: "), input("Nume salvare: ")
                try: urllib.request.urlretrieve(url, os.path.join(self.shared_dir, n)); print(f"[OK] Imagine descarcata: {n}")
                except: print("[EROARE]")
            elif c == "6":
                nume_zip = input("Nume arhiva: ")
                fisiere_str = input("Fisiere (separate prin virgula): ")
                lista = [f.strip() for f in fisiere_str.split(",")]
                try:
                    path_zip = os.path.join(self.shared_dir, nume_zip)
                    with zipfile.ZipFile(path_zip, 'w') as z:
                        for f in lista:
                            if os.path.exists(os.path.join(self.shared_dir, f)): z.write(os.path.join(self.shared_dir, f), f)
                    print(f"[OK] Arhiva {nume_zip} creata!")
                except Exception as e: print(f"[EROARE] {e}")

    def get_local_files(self):
        if not os.path.exists(self.shared_dir): return []
        return [f for f in os.listdir(self.shared_dir) if os.path.isfile(os.path.join(self.shared_dir, f))]

if __name__ == "__main__":
    Client(host=os.getenv("SERVER_HOST", "127.0.0.1")).connect()
