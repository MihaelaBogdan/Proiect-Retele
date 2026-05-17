# Sistem Distribuit de Fisiere

Un sistem profesional de partajare a fișierelor între clienți multipli, implementat în Python folosind Socket-uri și Multi-threading. Sistemul permite transferul de fișiere binare (imagini, arhive) și monitorizarea în timp real a directoarelor locale.

## Caracteristici principale
- Server Concurent: Gestionează mai mulți clienți simultan folosind thread-uri.
- Autentificare: Acces pe bază de Username și Parolă.
- Monitorizare Live: Detectează automat adăugarea sau ștergerea fișierelor din folderul local.
- Transfer Binar: Suportă orice tip de fișier (Imagini, ZIP, PDF, etc.) prin codificare Base64.
- Funcții Avansate:
  - Descărcare imagini direct de pe Internet (via URL).
  - Creare de arhive ZIP selective direct din meniu.
  - Re-partajare automată a fișierelor descărcate.

## Tehnologii utilizate
- Limbaj: Python 3.10+ (doar librării standard, zero dependențe externe).
- Infrastructură: Docker, Docker Compose.

## Structura Proiectului

/proiect_retele
├── /server
│   ├── server.py       # Logica centrală a serverului
│   └── Dockerfile      # Configurație container server
├── /client
│   └── client.py       # Aplicația client interactivă
├── docker-compose.yml  # Orchestrare Docker
└── README.md           # Documentație proiect
```

## Cum se rulează

### 1. Pornirea Serverului (Docker)
Din folderul rădăcină al proiectului, rulează:
```bash
docker compose up --build
```
Serverul va fi activ pe portul `5000`.

### 2. Pornirea Clienților
Deschide terminale noi pentru fiecare client și rulează:
```bash
cd client
python3 client.py
```
*Fiecare client își va crea automat propriul folder de partajare în interiorul folderului `client` (ex: `client/shared_mihaela`).*

## Instrucțiuni de Utilizare (Meniu)
1. **Lista**: Afișează fișierele tale locale și fișierele tuturor celorlalți clienți conectați.
2. **Download**: Descarcă un fișier de la un alt utilizator (se va salva cu prefixul `download_`).
3. **Exit**: Deconectare sigură de la server.
4. **Creaza**: Generează un fișier text nou cu nume și conținut ales de tine.
5. **IMAGINI**: Descarcă o imagine de pe un URL (Internet) direct în folderul de partajare.
6. **ZIP**: Creează o arhivă ZIP cu fișierele selectate de tine din folderul local.
