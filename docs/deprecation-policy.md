# Deprecation Policy

This document describes how the `kapso-whatsapp` SDK (and its future canonical name `kapso`)
handles breaking changes, deprecates symbols, and communicates planned removals to users.

---

## Semver guarantees

The SDK follows [Semantic Versioning 2.0](https://semver.org/): `MAJOR.MINOR.PATCH`.

### Patch releases (0.0.X)

Patch releases contain only backwards-compatible bug fixes. No public API is added, changed, or
removed. Safe to apply with no code changes.

Examples: fixing a typo in an exception message, correcting a wrong HTTP method in an internal
helper, patching a retry-backoff calculation edge case.

### Minor releases (0.X.0)

Minor releases add new public functionality in a backwards-compatible way. Existing code
continues to work without modification. Minor releases may also add new optional parameters to
existing methods, provided all new parameters have defaults that preserve current behavior.

Examples: adding a new resource (e.g. `kp.analytics`), adding an optional `timeout` parameter
to an existing method, exposing a new Pydantic model that previously returned a raw dict.

A minor release may also mark existing symbols as deprecated (see
[Deprecation timeline](#deprecation-timeline)), but it will not remove them.

### Major releases (X.0.0)

Major releases may contain breaking changes. Any symbol that was deprecated in a prior minor
release is a candidate for removal in the next major. Major releases are accompanied by a
migration guide in `CHANGELOG.md`.

Examples: removing a deprecated method, changing a required parameter's type, replacing an
exception class with a different one in the hierarchy.

---

## What counts as a breaking change

The following changes are **breaking** and will not appear in a minor or patch release:

- Removing a public method, property, or class that was previously part of the SDK's public API.
- Renaming a public method, property, or class without providing a compatibility shim.
- Changing the type or name of a required positional or keyword parameter.
- Adding a new **required** parameter to an existing method.
- Changing the return type of a method in a way that removes fields or changes their types
  (e.g. returning a `dict` where a Pydantic model was previously returned, or removing a
  field from a Pydantic model).
- Changing the exception class hierarchy in a way that breaks existing `except` clauses
  (e.g. making `NotFoundError` no longer inherit from `WhatsAppAPIError`).
- Removing or renaming an exported symbol from the package's top-level `__init__.py`.
- Changing the interpretation of an existing parameter's value in a backwards-incompatible way.

The following changes are **not breaking** and may appear in minor or patch releases:

- Adding an optional parameter with a default that preserves current behavior.
- Adding a new resource to `KapsoPlatformClient` or `WhatsAppClient`.
- Adding new fields to an existing Pydantic model (consumers should ignore unknown fields).
- Adding new exception subclasses that inherit from existing ones.
- Internal refactors that do not affect the public API surface.
- Improving type annotations without changing runtime behavior.
- Adding new convenience methods that duplicate (but do not replace) existing functionality.

---

## Deprecation timeline

When a public symbol needs to be replaced or removed, we follow a two-step process:

1. **Deprecation warning (minor release):** The symbol is kept but annotated with a
   `DeprecationWarning`. The warning message names the replacement and the planned removal
   version. The deprecation is noted in `CHANGELOG.md`.

2. **Removal (next major release):** The deprecated symbol is removed. Users who acted on the
   warning during the deprecation window can update at their own pace before the major bump.

The minimum deprecation window is **one full minor release** before removal in a major. In
practice, we aim for at least one minor release's worth of calendar time (typically several
weeks to a few months) so that users of less-frequently-updated applications have a reasonable
chance to encounter the warning.

### Emitting a DeprecationWarning

The standard Python mechanism for deprecation warnings is `warnings.warn()` with the
`DeprecationWarning` category. Here is how we apply it in the SDK:

```python
import warnings

class IntegrationsResource:

    async def list_connected_accounts(self, *, app: str | None = None):
        """Deprecated: use list_accounts(app_slug=...) instead."""
        warnings.warn(
            "list_connected_accounts() is deprecated and will be removed in v1.0. "
            "Use list_accounts(app_slug=...) instead.",
            DeprecationWarning,
            stacklevel=2,   # points the warning at the caller's line, not this line
        )
        return await self.list_accounts(app_slug=app)
```

`stacklevel=2` is important: it makes the warning point to the caller's code, not the SDK's
internal implementation, so users can find and fix the call site directly.

Python silences `DeprecationWarning` by default in non-`__main__` code, but development
environments, test runners (pytest shows them by default), and `python -W all` surface them.
Users running tests will see the warning; production deployments are not noisy.

### Checking for deprecation warnings in your code

To audit your code for deprecated SDK usage, run your test suite with warnings enabled:

```bash
python -W error::DeprecationWarning -m pytest
```

This converts all `DeprecationWarning` instances into errors, making any use of deprecated
SDK symbols fail loudly.

---

## Worked example: `kapso_whatsapp` → `kapso` rename for 1.0

The current package name is `kapso_whatsapp`. For version 1.0 we plan to publish the canonical
package under the name `kapso`, reflecting its broader scope beyond WhatsApp messaging.

This rename affects every import statement in every application using the SDK. We handle it in
two phases to give users a comfortable migration window.

### Phase 1 — 1.0 ships `kapso` as canonical; `kapso_whatsapp` becomes a shim

When 1.0 is released, `kapso` is the primary installable package:

```bash
pip install kapso
```

The `kapso_whatsapp` package continues to be published on PyPI for one more major version
cycle, but its content becomes a thin re-export shim that emits a `DeprecationWarning` on
import:

```python
# kapso_whatsapp/__init__.py  (shim, shipped in 1.0)
import warnings

warnings.warn(
    "The 'kapso_whatsapp' package is deprecated. "
    "Install 'kapso' and update your imports to 'from kapso import ...' instead. "
    "'kapso_whatsapp' will be removed in version 2.0.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything so existing code continues to work without changes.
from kapso import *                          # noqa: F401, F403
from kapso import (
    WhatsAppClient,
    KapsoPlatformClient,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ValidationError,
    RateLimitError,
    WhatsAppAPIError,
    NetworkError,
    TimeoutError,
)

__all__ = [
    "WhatsAppClient",
    "KapsoPlatformClient",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "WhatsAppAPIError",
    "NetworkError",
    "TimeoutError",
]
```

Applications that import from `kapso_whatsapp` will continue to work without any code changes.
They will simply see a `DeprecationWarning` in their test output, prompting them to migrate.

### Phase 2 — 2.0 removes the `kapso_whatsapp` shim

In version 2.0, `kapso_whatsapp` is no longer published. Applications must have updated their
imports before upgrading to 2.0:

```python
# Before (deprecated in 1.x, removed in 2.0)
from kapso_whatsapp import WhatsAppClient, KapsoPlatformClient

# After (works from 1.0 onwards, required from 2.0)
from kapso import WhatsAppClient, KapsoPlatformClient
```

The migration is mechanical: a simple find-and-replace of `kapso_whatsapp` with `kapso` in
import statements is sufficient. No method signatures, model names, or exception classes
change as part of this rename.

### Summary of the rename timeline

| Version | `pip install kapso` | `pip install kapso_whatsapp` | Behavior |
|---|---|---|---|
| 0.x (current) | Not published | Primary package | No warnings |
| 1.0 | Primary package | Shim with `DeprecationWarning` | Both work; shim warns |
| 2.0 | Primary package | Not published | Must use `kapso` |

---

## Pre-1.0 caveat

Semantic versioning [explicitly allows](https://semver.org/#spec-item-4) minor-version breaking
changes in the `0.x` range: "Anything MAY change at any time. The public API SHOULD NOT be
considered stable."

We acknowledge this. While we will honor deprecation warnings where practical during the
`0.x` series, we reserve the right to make minor breaking changes in minor releases before
1.0 when the cost of a full deprecation cycle outweighs the benefit. Any breaking change in
a `0.x` minor release will be clearly labeled **BREAKING** in `CHANGELOG.md`.

In practice, the `0.x` public API has been stable since `0.1.0` and we do not anticipate
disruptive changes before 1.0. The planned `kapso_whatsapp` → `kapso` rename is the only
known breaking change on the 1.0 roadmap.
