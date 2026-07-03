# TicketHub

> **Napomena:** repozitorij je nazvan `solution-sara_romac` jer GitHub ne dopušta znak `/` u nazivu repozitorija (traženi format iz zadatka bio je `solution/<ime_prezime>`).

Middleware REST servis koji dohvaća "support tickete" iz DummyJSON (javni testni izvor), transformira ih u vlastiti Ticket model, pohranjuje u lokalnu bazu i izlaže preko REST API-ja s CRUD funkcionalnošću, filtriranjem, pretragom, statistikama i periodičkom sinkronizacijom.

Napravljeno kao stručni zadatak za Python Developer poziciju.

---

## Sadržaj

- Tehnološki stack  
- Arhitektura i ključne odluke  
- Pokretanje - lokalno  
- Pokretanje - Docker Compose  
- Konfiguracija (env varijable)  
- API endpointi  
- Testovi  
- Migracije baze (Alembic)  
- Statička API dokumentacija  
- Struktura projekta  
- Korištenje AI alata  

---

## Tehnološki stack

| Tehnologija | Verzija | Uloga |
|---|---|---|
| Python | 3.11 | async/await, moderni type hints |
| FastAPI | 0.111 | REST API + OpenAPI |
| httpx | 0.27 | Async HTTP klijent prema DummyJSON-u |
| Pydantic | 2.7 | Validacija |
| SQLAlchemy | 2.0 | Async ORM |
| Alembic | latest | Migracije baze |
| pytest | latest | Unit + integracijski testovi |
| ruff | latest | Linting |
| python-jose | 3.3 | JWT autentifikacija |
| slowapi | 0.1 | Rate limiting |
| redis | 5.0 | Cache (optional fallback in-memory) |

---

## Arhitektura i ključne odluke

```
src/tickethub/
├── api/        # FastAPI routeri (HTTP sloj)
├── core/       # config, logging, security, cache
├── db/         # DB engine i session
├── models/     # ORM modeli
├── schemas/    # Pydantic sheme
└── services/   # business logika
```

---

### Razdvajanje ORM i Pydantic modela
ORM modeli definiraju bazu, a Pydantic sheme API ugovor.  
To omogućuje neovisne promjene baze i API sloja.

---

### Repository sloj
SQL logika je izolirana u service/repository sloju.  
Routeri ne sadrže SQL upite nego samo pozivaju servis funkcije.

---

### Sync logika
DummyJSON se koristi kao vanjski izvor.  
Pri sync-u se koristi upsert po `source_id` kako bi se izbjegli duplikati.

---

### Background sync
Sinkronizacija se pokreće automatski pri startu aplikacije (FastAPI lifespan event),  
te se može ručno pokrenuti putem `POST /sync`.

---

### Autentifikacija
`POST /auth/login` koristi DummyJSON za provjeru korisnika,  
a aplikacija izdaje vlastiti JWT token za autorizaciju.

---

### Cache
Cache koristi Redis ako je dostupan (`REDIS_URL`),  
inače fallback na in-memory implementaciju.

---

## API endpointi

### Auth

- POST `/auth/login` – login (DummyJSON + JWT)

Demo:
```
username: emilys  
password: emilyspass
```

---

### Read

- GET `/tickets`
- GET `/tickets/{id}`
- GET `/tickets?status=&priority=`
- GET `/tickets/search?q=...`

---

### Write

- POST `/tickets`
- PATCH `/tickets/{id}`

---

### System

- GET `/health`
- GET `/stats`
- POST `/sync`

---

## Testovi

Testovi su podijeljeni na:

- unit testove (logika + cache)
- integracijske testove (FastAPI + SQLite in-memory)

⚠️ Svi DummyJSON pozivi su mockani (`respx`), bez vanjskih API poziva.

```bash
make test
make test-cov
```

---

## CI pipeline

GitHub Actions (`.github/workflows/ci.yml`) se izvršava na svaki push/PR na `main`:

- lint (ruff)
- migracije (alembic)
- testovi (pytest + coverage)
- docker build

---

## Lokalno pokretanje

```bash
make install
make migrate
make run
```

---

## Docker

```bash
make docker-up
```

Servisi:
- API (FastAPI)
- PostgreSQL
- Redis (optional cache)

---

## Migracije

```bash
make migrate
make migrate-new msg="opis"
```

---

## AI korištenje

Projekt je razvijen uz pomoć AI alata kao pair-programming asistenta.

AI je korišten za:
- scaffolding FastAPI strukture
- JWT implementaciju
- rate limiting i cache
- testove i CI setup

Svi dijelovi su:
- ručno pregledani
- testirani
- prilagođeni projektu

---

## Struktura projekta

```
tickethub/
├── src/tickethub/
├── tests/
├── alembic/
├── scripts/
├── docs/
├── ci/
├── .github/workflows/
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── pyproject.toml
└── .env.example
```

---

## Napomena o CI

GitHub Actions workflow mora biti u:

```
.github/workflows/
```

Direktorij `ci/` služi samo za dokumentaciju CI procesa.
