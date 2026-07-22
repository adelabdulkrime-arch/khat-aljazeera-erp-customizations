# Khat Al Jazeera Workshop

Vehicle-workshop customisations for ERPNext: custom DocTypes, Arabic dashboards,
Oman localisation (OMR + 5% VAT), and the bridge into real ERPNext accounting
and stock.

## Why this is an app

These customisations previously lived as loose `workshop_*.py` scripts that
`init.sh` copied **into the frappe framework itself**
(`apps/frappe/frappe/workshop_*.py`) and executed one by one. That meant:

- the code was wiped by any image rebuild (`apps/` is not a volume),
- there was no `hooks.py`, no migrations, no versioning,
- it could not be uninstalled cleanly,
- and a framework upgrade could collide with our files.

As a proper app the same logic is installed with `bench install-app` and runs
through `bench migrate` like any other Frappe app.

## How setup runs

`hooks.py` registers `after_migrate`, so every `bench migrate` re-runs the
ordered, idempotent setup steps in `khat_workshop/setup/`. This preserves the
previous behaviour — where each deploy re-applied all customisations — while
using a supported mechanism instead of copying files into the framework.

`workshop_futuristic.py` is a shared library (CSS/JS + command palette) that the
dashboards import. It has no `execute()` and is deliberately not a step.
