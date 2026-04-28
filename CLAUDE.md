# CLAUDE.md

Notes for future Claude sessions working in this repo. Read this before doing anything non-trivial — it captures project-specific conventions and lessons that aren't obvious from a fresh `ls`.

## What this is

Python SDK for the Kapso WhatsApp ecosystem. Ships **two clients** that share an internal HTTP transport:

- `WhatsAppClient` — sends/receives WhatsApp messages via Meta Graph or the Kapso Meta-proxy (`graph.facebook.com` / `api.kapso.ai/meta/whatsapp`). URL shape: `{base}/{graph_version}/{path}`. Bearer or `X-API-Key` auth.
- `KapsoPlatformClient` — manages your Kapso project itself (customers, broadcasts, webhooks, database, integrations, WhatsApp Flows lifecycle, …) at `api.kapso.ai/platform/v1`. URL shape: `{base}/{path}`. `X-API-Key` only. Response envelope: `{"data": ..., "meta": {...}}`.

Both clients delegate to the private `_HttpCore` class in `src/kapso_whatsapp/_http.py` for httpx pool, retry-with-backoff, and error categorization. Touch `_HttpCore` if you need to change retry semantics; touch the individual clients for URL/auth/response-shape changes.

## Project layout

```
src/kapso_whatsapp/
├── _http.py              # private shared transport (don't change without testing both clients)
├── client.py             # WhatsAppClient
├── exceptions.py         # error hierarchy + categorize_error()
├── types.py              # Pydantic models for messaging (100+ types)
├── builders.py           # template builders (TS SDK parity helpers)
├── kapso.py              # Kapso field helpers
├── resources/            # WhatsAppClient resource modules (messages, media, templates, flows, …)
├── platform/             # KapsoPlatformClient
│   ├── client.py
│   ├── types.py
│   └── resources/        # 18 platform resource modules; each defines its own Pydantic models
├── webhooks/             # signature verify + payload normalize (messaging side)
└── server/flows.py       # WhatsApp Flow data exchange (AES-256-CBC + HMAC-SHA256)
```

## Verification before any commit

These three are non-negotiable:

```bash
python -m pytest -q        # 340+ tests must pass
python -m mypy src/        # 0 errors across 45 source files
python -m ruff check src/ tests/
```

Run live smoke (read-only against api.kapso.ai) when touching Platform resource models:

```bash
set -a && source .env && set +a
python examples/platform_smoke.py
```

`.env` has `KAPSO_API_TOKEN` already; the smoke script falls back to it if `KAPSO_PLATFORM_API_KEY` is unset.

## Adding a new Platform API resource

The reference template is `src/kapso_whatsapp/platform/resources/customers.py` + `tests/platform/test_customers.py`. Pattern:

1. Define Pydantic models at the top of the resource file (NOT in `platform/types.py` — that's reserved for shared envelope types like `PlatformMeta`).
2. Resource class extends `PlatformBaseResource`. Methods: `list` returns one page, `iter` async-generates across all pages via `self._client.paginate(path, ...)`, `get/create/update/delete` for CRUD.
3. Use the local `_filters(**kwargs)` helper to drop None query params (each resource has its own copy; that's fine).
4. **Match the API's request body shape literally.** Some endpoints wrap Rails-style (`{"customer": {...}}`), some don't. Read the docs and copy what's there. Don't try to be clever.
5. Wire into `KapsoPlatformClient`: `TYPE_CHECKING` import + instance var + lazy `@property`.
6. Tests in `tests/platform/test_<name>.py`. Use `platform_client` and `mock_platform_api` fixtures from `tests/conftest.py`. respx mocks should target `https://api.kapso.ai/platform/v1` (the fixture handles the base URL).
7. Add the resource to `examples/platform_smoke.py` for live verification.

## Pydantic strictness — the bug pattern that bit us 3× in v0.2.0

The Kapso API returns `null` for fields the docs show as required. Three resources (`User`, `ProjectWebhook`, `Webhook`) shipped with `field: str` and live-failed. Default posture for new models:

- `model_config = ConfigDict(extra="allow")` — accepts unknown future fields without breaking.
- Only `id` is `str` required. Everything else is `Optional[T] = None` unless you've verified it's never null in real responses.
- After implementing a model, run `examples/platform_smoke.py` and confirm validation passes against live data. Empty lists in the response don't prove the model — the model is only validated against returned items.

For each Platform resource, there's a `TestDocExampleValidates` class in its test file that asserts the doc's published JSON example validates against the model. This catches doc/API drift over time.

## Known quirks

- `_to_snake_case_deep` in `client.py` converts camelCase → snake_case for Meta Graph requests. The Platform client doesn't do this — its API is already snake_case.
- Pagination: most Platform endpoints use `meta.page`; some (e.g. `display_names`) use `meta.current_page`. The `paginate()` helper accepts both.
- 19 sites in Platform resource files use `# type: ignore[valid-type]` because methods named `list` shadow the `list[...]` builtin in mypy's class scope. Workaround until 1.0 (where we'll either alias or rename).
- Errors: `categorize_error(status, response)` in `exceptions.py` handles both `{"error": "string"}` (Platform) and `{"error": {"message": "..."}}` (Meta) shapes.

## Don't touch without explicit reason

- `src/kapso_whatsapp/server/flows.py` — AES-256-CBC + HMAC-SHA256 over Meta's flow data exchange. Security-critical. Tests in `tests/test_server_flows.py` cover round-trip + tamper detection.
- `tests/conftest.py` fixtures — used by every test file. Adding a fixture here is fine; renaming/removing breaks 340+ tests.
- `pyproject.toml` version field — bump only when shipping. Currently `0.3.0`. Next bump goes with whatever's accumulated under `## [Unreleased]` in `CHANGELOG.md`.

## How releases work

Two paths in this repo, used historically in this order:

1. **Manual** (what shipped `v0.3.0`): bump version in `pyproject.toml` + `__init__.py`, flip `[Unreleased]` → `[X.Y.Z] - <date>` in `CHANGELOG.md`, run `python -m build`, then `python -m twine upload dist/*`. Twine reads `TWINE_USERNAME` / `TWINE_PASSWORD` from `.env` (the project ships with these set; the password is a PyPI API token). Then `git tag -a vX.Y.Z` + push tag.
2. **CI-driven** (configured but not yet exercised): `.github/workflows/release.yml` triggers on `v*.*.*` tag pushes, runs tests, builds, and publishes via OIDC trusted publishing. Operational prereq: a `pypi` GitHub environment must exist and PyPI must have the trusted publisher configured. See the comments at the top of `release.yml`.

Either path verifies with a fresh-venv install:

```bash
python -m venv /tmp/.verify && /tmp/.verify/bin/pip install kapso-whatsapp-cloud-api==X.Y.Z
/tmp/.verify/bin/python -c "from kapso_whatsapp import __version__; print(__version__)"
rm -rf /tmp/.verify
```

Latest live: [`v0.3.0` on PyPI](https://pypi.org/project/kapso-whatsapp-cloud-api/0.3.0/) (template builders + BSUID compatibility).

## Where to learn more

- `IMPLEMENTATION_PLAN.md` — running status of what's shipped, what's deferred, and what's intentionally NOT being built (with reasons).
- `docs/architecture.md` — system topology with diagrams.
- `docs/platform-api.md` — full Platform API reference.
- `docs/cookbook-database.md` and `docs/cookbook-integrations.md` — pattern libraries for the two most complex Platform resources.
- `docs/deprecation-policy.md` — semver rules and the planned `kapso_whatsapp` → `kapso` rename for 1.0.

## Lessons baked in (don't re-learn the hard way)

- **Live smoke before tagging.** v0.2.0 had three Pydantic strictness bugs that respx-mocked tests didn't catch. The `examples/platform_smoke.py` read-only sweep is the cheapest way to surface them.
- **Don't add features users haven't asked for.** `IMPLEMENTATION_PLAN.md` has a "Removed from this plan" section with 9 items dropped because they were YAGNI or duplicates. Same review pass before adding new items.
- **Sub-agents need explicit DO-NOT-TOUCH lists.** When parallelizing across resources, agents will edit `client.py` to wire up their resource if you don't forbid it. They'll also edit `platform/types.py` if you let them; tell them to put types in their resource file instead.
- **The TS SDK is the source of truth for parity.** `github.com/gokapso/whatsapp-cloud-api-js`. When in doubt about Python API shape, port what TS does.
