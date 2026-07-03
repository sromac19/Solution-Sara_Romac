# Korištenje AI alata u razvoju ovog projekta

Kompletan projekt razvijen je u suradnji s **Claude** (Anthropic, model Claude Sonnet),
kroz interaktivnu konverzaciju. Ovaj dokument sažima ključne promptove i tijek rada,
kako je traženo u zadatku ("Bonus ako priložite prompt").

## Tijek rada (sažetak)

1. **Analiza zadatka** - proslijeđen je cijeli tekst stručnog zadatka Claude-u uz
   pitanje o procjeni vremena, izboru razvojnog okruženja (Mac vs. Windows) i
   načinu rada (lokalno vs. cloud).

2. **Scaffolding projekta** - prompt otprilike: *"Počnimo, reci mi što, kako i
   gdje da napravim da ovo sve dovršim"* → Claude je generirao kompletnu
   strukturu projekta (FastAPI app, SQLAlchemy async modeli, Pydantic sheme,
   repository sloj, Alembic migracije, Docker setup, testovi, CI) direktno u
   izvršnom sandbox okruženju, testirajući svaki dio uživo (pokretanje testova,
   ručni API pozivi, provjera migracija) prije predaje korisniku.

3. **Lokalni setup na Mac M3 Air** - iterativno vođenje kroz instalaciju
   Homebrew-a, Python 3.11, Docker Desktop-a, git konfiguracije, kreiranja
   GitHub repozitorija te rješavanja stvarnih problema koji su se pojavili
   usput (npr. `.env`/`.gitignore` datoteke koje su nestale prilikom
   Safarijevog automatskog raspakiravanja zip arhive, nedostajući `greenlet`
   paket, GitHub Personal Access Token bez `workflow` scope-a).

4. **Detaljna revizija prema specifikaciji** - prompt: *"Prodi mi kroz sve
   detaljno jel izvršeno"* → Claude je proveo doslovnu provjeru svake stavke
   iz zadatka (obavezni dio, nice-to-have, dodatni zahtjevi) i iskreno
   identificirao rupe: nedostajuću JWT autentifikaciju, nekorišten
   `slowapi` rate limiting dependency, Redis koji je bio samo u
   `docker-compose.yml` bez stvarnog korištenja u kodu, te git historiju
   koja nije bila feature-based.

5. **Dovršavanje nedostajućih dijelova** - prompt: *"Sad apsolutno sve što
   nije odrađeno ili je djelomično, promijeni i reci kako da bude savršeno"*
   → dodani su: JWT auth preko `/auth/login` (proxy prema DummyJSON-u),
   `slowapi` rate limiting na login i write endpointe, Redis-backed cache s
   automatskim in-memory fallbackom, `ci/README.md` (objašnjenje GitHub
   Actions platformskog ograničenja), ovaj `PROMPTS.md`, dodatni testovi
   (27 → 29+), te uputa za reorganizaciju git historije u feature-based
   commitove.

## Napomena o pristupu

Svaki generirani dio koda je u sklopu konverzacije **stvarno pokrenut i
testiran** (ne samo napisan) - pytest test suite, ruff linter, Alembic
upgrade/downgrade ciklus, ručni API pozivi kroz FastAPI TestClient, te
naknadno i na stvarnom razvojnom stroju (Docker Compose s PostgreSQL-om i
Redisom, pravi sync poziv prema DummyJSON-u). Arhitektonske odluke
(razdvajanje ORM modela i Pydantic shema, repository pattern, upsert-by-
source-id strategija sinkronizacije, `asyncio.create_task` umjesto vanjskog
schedulera za background sync, JWT izdan od strane TicketHub-a nakon
provjere kredencijala kod DummyJSON-a) su svjesno donesene i obrazložene u
[README.md](README.md#arhitektura-i-ključne-odluke), ne kopirane bez
razumijevanja.
