# Configuring the application

Configuration is via environment.

## Minimal `.env`

```dotenv title="Minimal .env"
NAME=tmpl-starlite-saqlalchemy
DB_URL=postgresql+asyncpg://postgres:mysecretpassword@localhost:5432/postgres1
OPENAPI_CONTACT_EMAIL=peter.github@proton.me
OPENAPI_CONTACT_NAME="Peter Schutt"
OPENAPI_TITLE="Template starlite-saqlalchemy Application"
OPENAPI_VERSION=1.0.0
REDIS_URL=redis://localhost:6379/0
```

## Local Development

Structured logs are nice when sending our logs through to some ingestion service, however, not so
nice for local development.

set `ENVIRONMENT=local` in your local `.env` file for a nicer local development experience
(we implement
[this structlog pattern](https://www.structlog.org/en/stable/logging-best-practices.html#pretty-printing-vs-structured-output)
for you!).

## Full `.env`

```dotenv title="Example .env"
--8<-- ".env.example"
```
