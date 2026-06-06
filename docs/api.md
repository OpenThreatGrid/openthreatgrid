# API Reference

The OpenThreatGrid API is described by an **OpenAPI 3.1** schema. The reference
below is rendered from [`openapi.json`](openapi.json) (also available as
[`openapi.yaml`](openapi.yaml)).

When the API is running you also get interactive docs for free:

| URL | Tool |
|---|---|
| `http://localhost:8000/docs` | Swagger UI (try-it-out) |
| `http://localhost:8000/redoc` | Redoc |
| `http://localhost:8000/openapi.json` | Raw OpenAPI schema |

Regenerate the committed schema after changing endpoints or models:

```bash
cd backend/otg-api && pip install -r requirements.txt
python ../../scripts/export_openapi.py     # writes docs/openapi.{json,yaml}
```

<!-- Redoc renders the committed schema. use_directory_urls puts this page at
     /api/, so the schema sits one level up at ../openapi.json. -->
<redoc spec-url="../openapi.json"></redoc>
<script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
