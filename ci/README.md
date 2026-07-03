# CI konfiguracija

Ovaj direktorij dokumentira CI/CD pristup korišten u projektu.

## Zašto se workflow ne nalazi u ovom direktoriju?

GitHub Actions prepoznaje workflow datoteke isključivo ako se nalaze na sljedećoj putanji:

```text
.github/workflows/*.yml
```

To je ograničenje GitHub platforme, a ne odluka projekta. Workflow datoteke smještene na drugim lokacijama (uključujući ovaj `ci/` direktorij) GitHub neće izvršavati.

Stvarna definicija CI pipelinea nalazi se u:

```text
.github/workflows/ci.yml
```

## Što CI pipeline radi?

Na svaki `push` i `pull_request` prema grani `main` izvršavaju se sljedeći koraci:

1. Checkout izvornog koda.
2. Postavljanje Python 3.11 okruženja uz `pip` cache radi brže instalacije paketa.
3. Instalacija svih ovisnosti:

   ```bash
   pip install -e ".[dev]"
   ```

4. Pokretanje lint provjere:

   ```bash
   ruff check src tests
   ```

5. Provjera Alembic migracija izvršavanjem:

   ```bash
   alembic upgrade head
   ```

   na čistoj SQLite bazi kako bi se potvrdilo da su migracije ispravne i primjenjive.

6. Pokretanje testova uz mjerenje pokrivenosti:

   ```bash
   pytest --cov=tickethub --cov-report=term-missing
   ```

7. Izgradnja Docker slike kako bi se potvrdilo da se produkcijski image može uspješno izgraditi.

Ako bilo koji od navedenih koraka ne uspije, pipeline se odmah prekida (fail-fast), a GitHub označava izvršavanje kao neuspješno. Time se sprječava spajanje ili implementacija koda koji ne prolazi osnovne provjere kvalitete.

## Pokretanje provjera lokalno

Sve provjere koje se izvršavaju u CI pipelineu moguće je pokrenuti i lokalno pomoću `Makefile` naredbi:

```bash
make lint          # lint provjera
make migrate       # provjera migracija
make test-cov      # testovi s pokrivenošću
make docker-build  # Docker build
```
