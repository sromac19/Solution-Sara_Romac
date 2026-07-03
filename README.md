# TicketHub

> **Napomena:** repozitorij je nazvan `solution-sara_romac` jer GitHub ne dopušta znak `/` u nazivu
> repozitorija (traženi format iz zadatka bio je `solution/<ime_prezime>`).

Middleware REST servis koji dohvaća "support tickete" iz [DummyJSON](https://dummyjson.com/todos)
(javni testni izvor), transformira ih u vlastiti `Ticket` model, pohranjuje ih u lokalnu bazu i
izlaže preko REST API-ja s punom CRUD funkcionalnošću, filtriranjem, pretragom, statistikom i
periodičkom pozadinskom sinkronizacijom.

Napravljeno kao stručni zadatak za Python Developer poziciju.

---

## Sadržaj

- [Tehnološki stack](#tehnološki-stack)
- [Arhitektura i ključne odluke](#arhitektura-i-ključne-odluke)
- [Pokretanje - lokalno](#pokretanje---lokalno)
- [Pokretanje - Docker Compose](#pokretanje---docker-compose)
- [Konfiguracija (env varijable)](#konfiguracija-env-varijable)
- [API endpointi](#api-endpointi)
- [Testovi](#testovi)
- [Migracije baze (Alembic)](#migracije-baze-alembic)
- [Statička API dokumentacija](#statička-api-dokumentacija)
- [Struktura projekta](#struktura-projekta)
- [Korištenje AI alata](#korištenje-ai-alata)

---

## Tehnološki stack

| Tehnologija | Verzija | Uloga |
|---|---|---|
| Python | 3.11 | `async`/`await`, moderni type hints |
| FastAPI | 0.111 | REST API + auto OpenAPI |
| httpx | 0.27 | Async HTTP klijent prema DummyJSON-u |
| Pydantic | 2.7 | Validacija ulaza/izlaza |
| SQLAlchemy | 2.0 | Async ORM (SQLite lokalno / PostgreSQL u Dockeru) |
| Alembic | najnovija | Migracije sheme baze |
| pytest | najnovija | Unit + integracijski testovi (`pytest-asyncio`, `respx` za mockanje HTTP-a) |
| ruff | najnovija | Linting |
| python-jose | 3.3 | JWT izdavanje/validacija (`POST /auth/login`) |
| slowapi | 0.1 | Rate limiting na login i write endpointe |
| redis | 5.0 | Cache backend (opcionalno - automatski fallback na in-memory ako `REDIS_URL` nije postavljen) |

## Arhitektura i ključne odluke

```
src/tickethub/
├── api/            # FastAPI routeri - tanki sloj (parsiranje requesta, poziv servisa)
├── core/           # config, logging, JWT security, rate limiting, cache (Redis/in-memory), background job
├── db/             # async SQLAlchemy engine/session
├── models/         # ORM modeli (SQLAlchemy)
├── schemas/        # Pydantic sheme (API ugovor - odvojeno od ORM modela)
└── services/       # poslovna logika: DummyJSON klijent, sync/transformacija, repository (upiti)
```

**Zašto su modeli i sheme odvojeni?** ORM model (`models/ticket.py`) opisuje što je u bazi.
Pydantic shema (`schemas/ticket.py`) opisuje što API prima/vraća. Ovo razdvajanje znači da API
ugovor može evoluirati (npr. skraćen opis u listi ticketa) bez diranja sheme baze, i obrnuto.

**Zašto repository sloj?** `services/ticket_repository.py` sadrži sve SQL upite. Routeri ne znaju
ništa o SQLAlchemy sintaksi - samo pozivaju funkcije poput `list_tickets(...)`. Ovo olakšava
testiranje upita neovisno o HTTP sloju i sprječava dupliciranje upita po više routera.

**Zašto upsert po `source_id` pri sync-u?** Ticketi kreirani kroz `POST /tickets` nemaju
`source_id` (to nije DummyJSON todo). Ticketi sinkronizirani iz izvora imaju `source_id` postavljen
na `todo.id`. Pri ponovnom sync-u tražimo postojeći ticket po `source_id` i **ažuriramo** ga umjesto
da kreiramo duplikat - servis se može sigurno pozivati periodički (background job) ili ručno
(`POST /sync`) bez nagomilavanja duplikata.

**Zašto background sync preko `asyncio.create_task` umjesto Celery/APScheduler?** Za jedan
periodički zadatak ovakve složenosti, vanjski scheduler bi bio prekomjeran (over-engineering) i
zahtijevao bi dodatnu infrastrukturu (message broker). `asyncio.create_task` pokrenut u FastAPI
`lifespan` handleru je dovoljan, jednostavan za pokretanje i lako zamjenjiv kasnije ako opseg
poraste.

**Zašto SQLite lokalno, PostgreSQL u Docker Compose-u?** SQLite ne zahtijeva nikakav vanjski
servis, pa je pokretanje projekta trivijalno (`make run`). Za "produkcijski" scenarij (Compose)
koristimo PostgreSQL jer bolje podnosi konkurentne pisanja i bliže je stvarnom deploymentu. Kôd se
ne mijenja - jedina razlika je `DATABASE_URL` (SQLAlchemy async driver apstrahira razliku).

**Kako radi autentifikacija?** `POST /auth/login` prima username/password i prosljeđuje ih
DummyJSON-ovom `/auth/login` endpointu (npr. demo korisnik `emilys`/`emilyspass`) radi provjere.
Ako DummyJSON potvrdi kredencijale, TicketHub izdaje **vlastiti** JWT (potpisan s
`JWT_SECRET_KEY`), koji se zatim šalje kao `Authorization: Bearer <token>` header prema write
endpointima (`POST /tickets`, `PATCH /tickets/{id}`). Razlog izdavanja vlastitog tokena umjesto
prosljeđivanja DummyJSON-ovog: TicketHub treba kontrolirati svoj expiry i payload neovisno o
vanjskom izvoru koji služi samo kao provjera identiteta.

**Zašto rate limiting baš na login i write rute?** Login je klasična meta brute-force napada
(5/min), a write rute štitimo od spama/zloupotrebe (10-20/min). Read rute nisu limitirane jer
uglavnom nose manji rizik zloupotrebe i veći je fokus na dostupnost podataka.

**Zašto Redis cache s in-memory fallbackom, a ne samo jedno ili drugo?** `core/cache.py` provjerava
je li `REDIS_URL` postavljen - ako da, koristi Redis (bitno kad app skalira na više instanci koje
trebaju dijeliti cache). Ako nije postavljen (npr. `make run` bez Dockera), automatski pada natrag
na in-memory rječnik - identična funkcionalnost, bez potrebe da lokalni razvoj ovisi o pokrenutom
Redis serveru.

## Pokretanje - lokalno

Preduvjeti: Python 3.11+, `pip`.

```bash
# 1. Kreirajte virtualno okruženje
python3.11 -m venv .venv
source .venv/bin/activate        # na Windowsu: .venv\Scripts\activate

# 2. Instalirajte dependency-je (uključujući dev alate)
make install
# ili ručno: pip install -e ".[dev]"

# 3. Kopirajte env template
cp .env.example .env
# (default vrijednosti rade odmah - SQLite, bez potrebe za daljnjim podešavanjem)

# 4. Primijenite migracije baze
make migrate

# 5. Pokrenite aplikaciju (hot-reload)
make run
```

Aplikacija je dostupna na `http://localhost:8000`, interaktivna dokumentacija na
`http://localhost:8000/docs`.

Baza kreće **prazna**. Podatke iz DummyJSON-a povucite jednim od dva načina:
- Ostavite aplikaciju upaljenu ~nekoliko sekundi - background job automatski sync-a pri startu.
- Ili odmah ručno: `curl -X POST http://localhost:8000/sync`

## Pokretanje - Docker Compose

Preduvjeti: Docker + Docker Compose.

```bash
make docker-up
# ili: docker compose up --build
```

Ovo pokreće tri servisa:
- **api** - TicketHub aplikacija (port `8000`), automatski primjenjuje migracije pri startu
- **db** - PostgreSQL 16 (port `5432`)
- **redis** - backend za `/stats` cache (port `6379`); aplikacija automatski koristi Redis kad je
  `REDIS_URL` postavljen (vidi `core/cache.py`)

Zaustavljanje: `make docker-down`

## Konfiguracija (env varijable)

Sve varijable su dokumentirane u [`.env.example`](.env.example). Najvažnije:

| Varijabla | Default | Opis |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./tickethub.db` | Connection string (SQLite ili PostgreSQL) |
| `DUMMYJSON_BASE_URL` | `https://dummyjson.com` | Vanjski izvor podataka |
| `SYNC_INTERVAL_SECONDS` | `300` | Koliko često background job osvježava podatke |
| `CACHE_TTL_SECONDS` | `30` | TTL za cache (`/stats` endpoint) |
| `REDIS_URL` | *(prazno)* | Ako je postavljen, cache koristi Redis; inače automatski in-memory fallback |
| `JWT_SECRET_KEY` | *(promijeniti u produkciji)* | Tajni ključ za potpisivanje TicketHub JWT-ova |
| `LOG_LEVEL` | `INFO` | Razina logiranja |

## API endpointi

### Autentifikacija

| Metoda | Putanja | Opis |
|---|---|---|
| POST | `/auth/login` | Prijava (proxy prema DummyJSON-u), vraća TicketHub JWT. Rate limited: 5/min |

Demo kredencijali (javno dokumentirani na [dummyjson.com/docs/auth](https://dummyjson.com/docs/auth)):
`username=emilys`, `password=emilyspass`

### Read

| Metoda | Putanja | Opis |
|---|---|---|
| GET | `/tickets` | Paginirana lista (`page`, `page_size`, opis skraćen na ≤100 znakova) |
| GET | `/tickets?status=open&priority=high` | Filtriranje po statusu i/ili prioritetu |
| GET | `/tickets/search?q=...` | Pretraga po naslovu/opisu |
| GET | `/tickets/{id}` | Detalji ticketa + puni originalni JSON iz izvora |

### Write (zahtijevaju `Authorization: Bearer <token>`)

| Metoda | Putanja | Opis |
|---|---|---|
| POST | `/tickets` | Kreiranje novog ticketa. Rate limited: 10/min |
| PATCH | `/tickets/{id}` | Djelomična izmjena (samo poslana polja). Rate limited: 20/min |

### Sistemsko

| Metoda | Putanja | Opis |
|---|---|---|
| GET | `/health` | Health-check (k8s/Compose liveness probe) |
| GET | `/stats` | Agregirane statistike po statusu i prioritetu (cachirano) |
| POST | `/sync` | Ručno okida sinkronizaciju s DummyJSON-om |

Puna interaktivna specifikacija: `/docs` (Swagger) ili `/redoc` (ReDoc), automatski generirana od
strane FastAPI-ja.

### Primjer toka: login → kreiranje ticketa

```bash
# 1. Prijava - dobij token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"emilys","password":"emilyspass"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 2. Kreiranje ticketa uz token
curl -X POST http://localhost:8000/tickets \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title":"Novi problem","priority":"high"}'
```

## Testovi

```bash
make test        # verbose
make test-cov     # s coverage izvještajem
```

29 testova, podijeljena u:
- **`tests/unit/`** - čista transformacijska logika (status/priority pravila) i cache TTL ponašanje,
  bez baze i mreže
- **`tests/integration/`** - puni HTTP tok kroz FastAPI `TestClient` + in-memory SQLite baza; sync
  servis i login testirani s mockanim DummyJSON pozivima (`respx`), **nikad se ne gađa pravi
  vanjski API** u testovima (stabilnost i brzina testova). Uključuje i dedicirani test rate
  limitinga koji potvrđuje da server stvarno vraća `429` nakon praga.

CI (GitHub Actions, `.github/workflows/ci.yml`) na svaki push/PR pokreće: lint → provjeru Alembic
migracija → testove s coverage-om → Docker build.

## Migracije baze (Alembic)

```bash
make migrate                          # primijeni sve migracije (upgrade head)
make migrate-new msg="opis promjene"  # generiraj novu migraciju iz promjena modela
```

Migracije su uključene u repozitorij (`alembic/versions/`) - shema baze prati git history, ne
oslanja se na `create_all()` u produkciji.

## Statička API dokumentacija

Bonus dio zadatka - statički generiran ReDoc HTML (ne zahtijeva pokrenutu aplikaciju za pregled):

```bash
make docs
```

Generira `docs/index.html` iz trenutne OpenAPI sheme aplikacije (preko `@redocly/cli`).

## Struktura projekta

```
tickethub/
├── src/tickethub/          # aplikacijski kod
├── tests/                  # unit + integracijski testovi
├── alembic/                # migracije baze
├── scripts/                # pomoćne skripte (export OpenAPI sheme)
├── docs/                   # statička API dokumentacija (bonus)
├── ci/                     # dokumentacija CI pristupa (stvarni workflow mora biti u .github/workflows/ - GitHub-ovo platformsko ograničenje, objašnjeno u ci/README.md)
├── .github/workflows/      # CI pipeline (GitHub Actions)
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── pyproject.toml
├── PROMPTS.md              # bonus - detaljan log AI promptova korištenih u razvoju
└── .env.example
```

## Korištenje AI alata

Ovaj projekt je razvijen uz pomoć Claude-a (Anthropic) kao pair-programming alata. Detaljan opis
tijeka rada i ključni promptovi nalaze se u [`PROMPTS.md`](PROMPTS.md) (bonus dio zadatka).

Ukratko, Claude je korišten za:
- scaffolding projektne strukture (routeri, sheme, servisi, repository sloj)
- implementaciju JWT autentifikacije, rate limitinga i Redis-backed cachea
- pisanje unit i integracijskih testova (uključujući mockanje vanjskog API-ja preko `respx`)
- postavljanje Alembic async konfiguracije, Dockerfile-a, docker-compose.yml-a i CI workflowa
- pisanje ove dokumentacije

Svaki generirani dio koda je ručno pregledan, pokrenut i testiran (`pytest`, `ruff`, ručni API
pozivi, Docker Compose s pravim PostgreSQL/Redis kontejnerima) prije uključivanja u repozitorij.
Arhitektonske odluke (razdvajanje shema/modela, repository pattern, upsert-by-source-id strategija,
izbor `asyncio.create_task` umjesto vanjskog schedulera, TicketHub izdaje vlastiti JWT nakon
provjere kod DummyJSON-a) donesene su i obrazložene svjesno, ne kopirane bez razumijevanja.
