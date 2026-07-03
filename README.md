# TicketHub

Middleware REST servis koji dohvaća "support tickete" iz vanjskog izvora [DummyJSON](https://dummyjson.com/todos), transformira ih u vlastiti `Ticket` model, pohranjuje u lokalnu bazu i izlaže putem REST API-ja.

Projekt je izrađen kao stručni zadatak za Python Developer poziciju.

---

## Tehnološki stack

| Tehnologija | Uloga |
|---|---|
| Python 3.11 | async/await, typing |
| FastAPI | REST API |
| httpx | async HTTP klijent |
| Pydantic | validacija |
| SQLAlchemy 2.x | async ORM |
| Alembic | migracije |
| pytest | testovi |
| ruff | lint |

---

## Arhitektura i ključne odluke

```
src/tickethub/
├── api/        # FastAPI routeri
├── core/       # config, logging, security, cache
├── db/         # engine i session
├── models/     # SQLAlchemy modeli
├── schemas/    # Pydantic sheme
└── services/   # poslovna logika
```

### Razdvajanje ORM i Pydantic modela
ORM modeli opisuju bazu, dok Pydantic sheme definiraju API ugovor. Ovo omogućuje neovisne promjene baze i API-ja.

### Repository/service sloj
SQL logika je izolirana u service/repository sloju kako bi routeri ostali čisti i fokusirani samo na HTTP sloj.

### Sinkronizacija podataka
DummyJSON se koristi kao izvor podataka. Pri sync-u se koristi upsert po `source_id` kako bi se izbjegli duplikati pri ponovnom dohvaćanju podataka.

### Background sync
Sinkronizacija se pokreće automatski pri startu aplikacije (FastAPI lifespan event), te se može ručno okinuti putem `POST /sync`.

### Autentifikacija
`POST /auth/login` koristi DummyJSON za provjeru korisnika, a aplikacija zatim izdaje vlastiti JWT token kako bi kontrolirala autorizaciju unutar sustava.

### Cache
Cache sloj koristi Redis ako je dostupan (`REDIS_URL`), inače fallback na in-memory implementaciju.

---

## API endpointi

### Auth
- POST `/auth/login` – login (DummyJSON proxy + JWT)

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
- GET `/tickets/search?q=`

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

⚠️ Svi DummyJSON pozivi su mockani (`respx`), bez vanjskih API poziva u testovima.

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
- Redis (cache opcionalno)

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
- implementaciju JWT autentifikacije
- rate limiting i cache sloj
- testove i CI setup

Svi dijelovi su:
- ručno pregledani
- testirani
- prilagođeni projektu

---

## Napomena o CI

GitHub Actions workflow mora se nalaziti u:

```
.github/workflows/
```

Direktorij `ci/` služi isključivo za dokumentaciju CI procesa.
