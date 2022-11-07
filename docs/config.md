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

## Full `.env`

```dotenv title="Example .env"
--8<-- ".env.example"
```
