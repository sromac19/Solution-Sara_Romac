"""
Exporta OpenAPI shemu FastAPI aplikacije u openapi.json.
Koristi se za generiranje statičke ReDoc HTML dokumentacije (bonus dio zadatka).

Pokretanje: python scripts/generate_openapi.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tickethub.main import app  # noqa: E402

if __name__ == "__main__":
    schema = app.openapi()
    output_path = Path(__file__).resolve().parent.parent / "openapi.json"
    output_path.write_text(json.dumps(schema, indent=2, ensure_ascii=False))
    print(f"OpenAPI shema zapisana u {output_path}")
