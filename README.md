# payloadworker-rust

Async webhook ingestion and job processing service built with Rust + Axum.

## Endpoints

- `POST /webhook` — ingest webhook payload (validates HMAC-SHA256 signature)
- `GET /jobs/:id` — check job status
- `GET /health` — health check

## Environment Variables

- `DATABASE_URL` — PostgreSQL connection string
- `WEBHOOK_SECRET` — HMAC secret for signature verification
- `BIND_ADDR` — bind address (default: `0.0.0.0:8084`)
