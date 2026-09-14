# Pricing Anomaly, OCR & Receipt Item Analysis Service

Independent FastAPI service consumed by a .NET application over HTTP.
Three business endpoints, frozen in Phase 0:

| Endpoint | Input | Output |
|---|---|---|
| `POST /api/v1/pricing/score` | `name`, `category`, `price` | expected price + anomaly score |
| `POST /api/v1/ocr/extract` | `object_key` | OCR/NLP line items |
| `POST /api/v1/receipt/analyze` | `object_key` | OCR + NLP + per-item pricing |

File-based endpoints take an S3 `object_key`, not a multipart upload — the
bucket is server-side configuration, never caller-supplied.

## Status

- **Phase 0 (this delivery):** architecture, schemas, config, error model,
  service interfaces. Business logic is stubbed (`Unimplemented*Service`,
  returns HTTP 501) so the contracts are provable before real code lands.
- Phase 1+ fill in each service one phase at a time; see the development
  plan document for the full phase map and acceptance gates.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Run

```bash
uvicorn app.main:app --reload
```

OpenAPI docs: `http://127.0.0.1:8000/docs`

## Test

```bash
pytest
```

## Auth

All business endpoints require header `X-API-Key: <API_KEY>` (see `.env`).
This is service-to-service auth for the .NET caller, not a user login.
