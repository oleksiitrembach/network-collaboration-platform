from __future__ import annotations

from pathlib import Path

import uvicorn

from app.config import API_HOST, API_PORT, TLS_CERT_PATH, TLS_KEY_PATH


if __name__ == "__main__":
    cert_path = Path(TLS_CERT_PATH)
    key_path = Path(TLS_KEY_PATH)
    if not cert_path.exists() or not key_path.exists():
        raise SystemExit(
            "Brak certyfikatu TLS. Uruchom skrypt scripts/generate_certs.ps1 albo scripts/generate_certs.sh"
        )

    uvicorn.run(
        "app.main:app",
        host=API_HOST,
        port=API_PORT,
        ssl_certfile=str(cert_path),
        ssl_keyfile=str(key_path),
        reload=False,
    )
