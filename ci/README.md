# CI konfiguracija

Ovaj direktorij dokumentira CI/CD konfiguraciju korištenu u projektu **TicketHub**.

## Napomena

GitHub Actions zahtijeva da se workflow datoteke nalaze u `.github/workflows/`.  
Zbog toga se stvarna CI konfiguracija nalazi u:

```text
.github/workflows/ci.yml
```

Ovaj direktorij (`ci/`) služi isključivo za dokumentaciju CI procesa i eventualne dodatne CI skripte.

## Što CI workflow radi?

Prilikom svakog `push` ili `pull_request` događaja na granu `main`, automatski se izvršavaju sljedeći koraci:

1. Checkout repozitorija
2. Postavljanje Python 3.11 okruženja (uz pip cache za bržu instalaciju)
3. Instalacija ovisnosti (`pip install -e ".[dev]"`)
4. Lint provjera koda (`ruff check src tests`)
5. Provjera Alembic migracija na čistoj SQLite bazi (`alembic upgrade head`)
6. Pokretanje testova uz coverage izvještaj (`pytest --cov=tickethub --cov-report=term-missing`)
7. Docker build za provjeru produkcijskog imagea

Ako bilo koji korak ne uspije, workflow se prekida (fail-fast), a GitHub označava build kao neuspješan. Time se sprječava merge koda koji ne prolazi osnovne provjere kvalitete.

## Lokalno pokretanje istih provjera

Sve CI provjere mogu se pokrenuti lokalno pomoću Makefile-a:

```bash
make lint
make migrate
make test-cov
make docker-build
```
```
