# Documentație Proiect Rețele: Sistem Distribuit de Partajare a Fișierelor

## 1. Descriere generală
Aplicația este un sistem distribuit de tip client-server pentru partajarea de fișiere. Server-ul funcționează ca un intermediar, menținând evidența clienților și a fișierelor pe care le expun în rețea, fără a stoca permanent aceste date. Clienții se pot conecta, pot partaja un director local (care este monitorizat automat pentru modificări) și pot descărca fișiere de la alți utilizatori conectați.

## 2. Arhitectura Aplicației
- **Model:** Client-Server.
- **Protocol:** TCP, cu un protocol propriu la nivel de aplicație bazat pe pachete JSON precedate de lungimea mesajului (4 bytes, format network-byte-order `!I`).
- **Concurrență:** Multi-threading. Server-ul asignează un fir de execuție separat pentru fiecare client, permițând comunicare concurentă.
- **Format Transfer Date:** Text și binar. Fișierele binare (imagini, arhive etc.) sunt citite, encodate Base64 și împachetate într-un dicționar JSON.
- **Containerizare:** Server-ul rulează într-un container Docker pentru izolare și ușurință în execuție.

## 3. Implementarea Cerințelor Funcționale

### 3.1 Autentificarea Clienților
Clientul trimite către server un mesaj de tip `AUTH` la conectare. Acesta conține un `username`, o parolă opțională și lista inițială de fișiere detectate în folderul său partajat (`shared_{username}`). 
Server-ul verifică datele și, dacă autentificarea are succes, trimite mesajul `SYNC_LIST` cu toate fișierele rețelei.

### 3.2 Notificări de Conectare și Deconectare
- **Conectare:** Server-ul transmite un mesaj `NOTIFY_CONNECT` tuturor clienților existenți cu numele noului utilizator și lista sa de fișiere.
- **Deconectare:** Prin intermediul blocului `finally` din server, închiderea subită a aplicației client (sau ieșirea voită) generează automat un mesaj `NOTIFY_DISCONNECT` propagat către restul clienților.

### 3.3 Transferul de Fișiere (Optimizat pentru fișiere mari / Binare)
Pentru a suporta "tratatrea corectă pentru fișiere binare și arhive", aplicația nu încarcă fișierele complet în memoria RAM, prevenind astfel crash-urile (`MemoryError`) specifice transferurilor masive de date:
Când utilizatorul cere descărcarea unui fișier (`DOWNLOAD_REQ`):
1. **Validare pe Server:** Înainte de a intermedia cererea, server-ul caută dacă target-ul (utilizatorul-sursă) este conectat și dacă posedă fișierul respectiv. Dacă verificarea pică, solicitantul primește o eroare descriptivă.
2. Dacă fișierul există, server-ul trimite către țintă un `UPLOAD_REQ`.
3. Ținta primește mesajul, deschide fișierul local (`"rb"`) și citește conținutul **în bucăți secvențiale (chunks de 64 KB)**.
4. Fiecare chunk este encodat în Base64 și transmis serverului sub formă de `FILE_CHUNK`. La terminarea citirii, se trimite `FILE_END`.
5. Server-ul funcționează ca un proxy rapid și rutează toate mesajele `FILE_CHUNK` și `FILE_END` direct către solicitant.
6. Solicitantul primește chunk-urile Base64, le decodifică pe rând și le adaugă (append `"ab"`) în fișierul local `download_{nume_fișier}` în timp real, asigurând astfel suportul nelimitat ca dimensiune pentru filme, poze sau arhive ZIP. La primirea semnalului `FILE_END`, transferul se încheie complet cu un mesaj de confirmare pe ecran.

### 3.4 Monitorizarea Directorului Gazdă
Clientul rulează un fir de execuție în fundal (`monitor`) care face diferența constantă între structura directoarelor la secunda curentă și starea anterioară. 
Orice fișier nou adăugat generează un `FILE_ADDED`, iar cele șterse trimit `FILE_REMOVED`. Server-ul retrimite aceste actualizări sub formă de `broadcast` la restul clienților.

## 4. Structura de Mesaje (Protocol)
- `AUTH` - Solicită conectarea și anunță prezența în rețea.
- `SYNC_LIST` - Emis de server; furnizează noii conexiuni datele existente în rețea.
- `NOTIFY_CONNECT` - Alertă generală transmisă la aderarea unui client.
- `NOTIFY_DISCONNECT` - Alertă generală transmisă la deconectarea unui client.
- `FILE_ADDED` / `FILE_REMOVED` - Notificări de actualizare a directoarelor.
- `DOWNLOAD_REQ` - Client către Server; cere un fișier de la un alt utilizator.
- `UPLOAD_REQ` - Server către Client-țintă; comandă citirea fișierului pentru transfer.
- `FILE_DATA` - Mesajul cu payload-ul în Base64 al fișierului.

## 5. Tehnologii și Rulare
- **Limbaj:** Python 3
- **Containerizare Server:** Docker / docker-compose. Serverul ascultă pe `0.0.0.0:5000`.
- **Rulare Client:** Simplu `python3 client.py` în consolă, cu meniu CLI interactiv.
