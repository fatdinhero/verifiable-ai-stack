# Detect API – Deployment

Production: https://agentsprotocol-detect.fly.dev/  
Platform: Fly.io (Frankfurt, shared-cpu-1x, 256 MB)

## Endpoints

| Method | Path        | Beschreibung              |
|--------|-------------|---------------------------|
| GET    | `/`         | Service-Info              |
| GET    | `/health`   | Liveness-Check            |
| POST   | `/validate` | Claim validieren          |
| GET    | `/docs`     | Swagger UI                |

## Lokaler Build

Der Depot-Builder (Fly.io Remote Build) hat keinen PyPI-Zugriff. Wheels müssen
vor dem Deploy lokal heruntergeladen werden:

```bash
pip download \
  fastapi "uvicorn[standard]" pydantic numpy scipy cryptography \
  --dest detect/wheels \
  --platform manylinux2014_x86_64 \
  --python-version 311 --implementation cp --abi cp311 \
  --only-binary=:all:
```

`detect/wheels/` und `detect/agentsprotocol_pkg/` sind per `.gitignore`
ausgeschlossen und müssen lokal vorhanden sein, bevor `fly deploy` aufgerufen
wird.

## Deploy

```bash
cd detect
fly deploy --remote-only --smoke-checks=false
```

## Bekannte Integrations-Details

`compute_s_con()` erwartet:

```python
compute_s_con(knowledge_corpus=..., embed=...)
```

nicht `corpus=` / `embed_fn=` — diese Namen stammen aus einer älteren API-Version.
