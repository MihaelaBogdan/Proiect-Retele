# 🎓 Ghid Complet de Evaluare & Prezentare - Proiect Rețele

Acest document este creat special pentru **prezentarea finală a proiectului**. Conține toți pașii de rulare, scenariile cerute în barem și (cel mai important) **întrebările tehnice / capcană pe care le poate pune profesorul**, alături de explicații clare pentru a obține punctajul maxim.

---

## 1. Cum Rulăm Aplicația la Prezentare

### Pasul 1: Pornirea Server-ului (În Docker)
Deschide terminalul în folderul rădăcină (`proiect_retele`) și rulează:
```bash
docker compose up --build
```
> Server-ul se va inițializa și va rămâne în așteptare pe portul **5000**. Orice eveniment de rețea (logare, transferuri) se va afișa detaliat în această consolă.

### Pasul 2: Pornirea Clienților (În Terminale Separate)
Deschide **2 sau 3 terminale noi**, intră în folderul `client` și rulează comanda pentru fiecare:
```bash
cd client
python3 client.py
```
Autentifică fiecare client cu un nume diferit (ex: `mihaela`, `radu`, `maria`).

---

## 2. Cum demonstrezi Scenariile din Barem

| Scenariu din Barem | Cum îl demonstrezi practic |
| :--- | :--- |
| **Publicarea inițială** | După login, dă opțiunea `1. Lista`. Se va vedea că fișierele cu care ai intrat au fost trimise la toți ceilalți. |
| **Detectare adăugare / propagare** | În clientul 1 dă `4. Creaza` (sau trage un fișier cu mouse-ul în folderul `shared_mihaela`). Instantaneu, pe terminalele celorlalți va apărea notificarea `[*] mihaela a adaugat: <fisier>`. |
| **Detectare ștergere** | Mergi în File Explorer/Finder, șterge un fișier din `shared_mihaela`. Pe ecranul tuturor celorlalți clienți va scrie imediat că ai "retras" fișierul. |
| **Download prin server** | În clientul 2, alege opțiunea `2. Download`. Alege-o ca sursă pe "mihaela" și dă numele fișierului ei. Se va descărca cu succes sub numele `download_<nume>`. Dacă tragi o imagine JPEG sau o arhivă ZIP în folderul sursei, poți demonstra că se descarcă identic, fără a se corupe! |
| **Deconectare bruscă** | Pe clientul 3, pur și simplu închide terminalul ("X"-ul roșu din colț) sau dă `CTRL+C` (nu folosi meniul 3.Exit, simulează un crash real). Restul rețelei va primi instantaneu `[-] <nume> a plecat.`. |

---

## 3. Întrebări Capcană de la Profesor (Și cum să-i răspunzi tehnic)

Aici este „miezul” tehnic al proiectului. Profesorii de rețelistică adoră să întrebe cum au fost rezolvate anumite probleme clasice:

### Q1: "Cum asiguri că server-ul nu se blochează când comunică cu mai mulți clienți deodată?" (Concurrență)
**Răspuns tău:** „Server-ul este 100% concurent deoarece folosește Multi-threading. La fiecare conectare prin `self.sock.accept()`, instanțiez un `threading.Thread` independent (`server.py`, linia 114) care execută funcția `handle_client`. Mai mult, pentru că mai multe fire pot modifica lista globală de fișiere simultan, am folosit un **Mutex** (`self.lock = threading.Lock()`) atunci când scriem/ștergem useri în memoria server-ului pentru a preveni fenomenul de Race Condition.”

### Q2: "Dacă un client ia Crash (i se taie curentul), server-ul o să încerce la infinit să-i trimită date?"
**Răspunsul tău:** „Nu, deloc. Funcția `handle_client` din `server.py` este protejată integral de un bloc `try...finally`. Pe linia de cod `finally: self.cleanup(username, sock)` (linia 92) ne asigurăm că **indiferent de motivul deconectării** (eroare de rețea, crash forțat, quit intenționat), socket-ul lui va fi închis, el va fi șters din memoria RAM a serverului, iar metoda va face un *broadcast* automat (`NOTIFY_DISCONNECT`) restului clienților pentru actualizarea interfeței.”

### Q3: "Să zicem că trimit un fișier mare. Problema la TCP este că se 'lipesc' pachetele (TCP Streaming). Cum o rezolvi?"
**Răspunsul tău:** „TCP este bazat pe flux (stream-oriented), nu pe mesaje. De aceea am definit un **Protocol Custom la Nivel de Aplicație**. Orice JSON pe care-l trimitem (fie din client, fie din server) este precedat de un **Header de fix 4 bytes**.
- Când formăm pachetul, folosim `struct.pack('!I', lungime_payload)`.
- Când primim (`recv_msg`), facem un while-loop care citește fix primii 4 bytes pentru a afla lungimea, apoi un alt while care citește fix numărul ăla de bytes de date, garantând că pachetele nu se vor lipi / fragmenta greșit niciodată.”

### Q4: "Monitorizarea directorului gazdă... cum funcționează de știe instant că s-a adăugat ceva?"
**Răspunsul tău:** „Pe clienți rulează un "daemon thread" în fundal (`def monitor()`) care verifică folderul o dată pe secundă. Din punct de vedere algoritmic este extrem de optimizat pentru că citește starea nouă și o compară matematic prin **Set Differences (Diferență de mulțimi în Python)** (`for f in current - self.local_files`). O(N) la căutare. Găsește strict elementul nou/șters și dă hit la server.”

### Q5: "Cum rezolvi memoria RAM dacă doi utilizatori partajează un fișier video binar de 10 Gigabytes?"
**Răspunsul tău:** „Acesta este un punct forte al proiectului: folosește **Chunking (Streaming)** pentru transferul binar. Nu citim niciodată tot fișierul deodată. Când solicitantul dă Download, sursa deschide fișierul (`rb`), citește calupuri de fix 64 KB, le criptează Base64 și trimite la server tipul de mesaj `FILE_CHUNK`. Server-ul rutează chunk-ul mai departe, iar solicitantul îl asamblează local pe loc (`ab` - append binary). Acest mecanism menține utilizarea de memorie la nivelul câtorva Kilobytes per transfer, prevenind crash-urile de memorie indiferent de mărimea arhivei/fișierului!”
