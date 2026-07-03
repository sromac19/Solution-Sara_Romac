# CI konfiguracija

Ovaj folder dokumentira CI/CD pristup korišten u projektu.

## Zašto stvarna workflow definicija nije fizički ovdje

GitHub Actions **zahtijeva** da workflow YAML fajlovi budu na točno određenoj
putanji u repozitoriju: `.github/workflows/*.yml`. To je platformsko
ograničenje GitHuba, ne odluka projekta - GitHub jednostavno ne prepoznaje
workflow fajlove postavljene bilo gdje drugdje (uključujući ovaj `ci/` folder).

Stvarna definicija pipeline-a nalazi se u:
[`/.github/workflows/ci.yml`](../.github/workflows/ci.yml)

## Što pipeline radi

Na svaki `push` i `pull_request` prema `main` grani, pipeline izvršava:

1. **Checkout koda**
2. **Postavljanje Python 3.11** okruženja (uz pip cache za brže buildove)
3. **Instalacija dependency-ja** (`pip install -e ".[dev]"`)
4. **Lint** - `ruff check src tests`
5. **Provjera Alembic migracija** - `alembic upgrade head` na čistoj SQLite bazi
   (potvrđuje da migracije stvarno rade, ne samo da postoje)
6. **Testovi** - `pytest --cov=tickethub --cov-report=term-missing`
7. **Docker build** - potvrđuje da se produkcijski image uspješno gradi

Ako bilo koji korak padne, pipeline se prekida (fail-fast) i status na
GitHubu postaje crven - sprječava merge/deploy koda koji ne prolazi
osnovne provjere kvalitete.

## Lokalno pokretanje istih provjera

Sve što CI radi možeš pokrenuti i lokalno prije push-a, preko Makefile-a:

```bash
make lint        # korak 4
make migrate      # korak 5
make test-cov      # korak 6
make docker-build  # korak 7
```
