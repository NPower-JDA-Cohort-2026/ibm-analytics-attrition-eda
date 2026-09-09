"""Exercise every server-side callback through the real Dash request path.

Run from the project root::

    .venv/Scripts/python dashboards/app/smoke_test.py

Input values are taken from the layout's own defaults, so this checks the app as
a user first sees it, then repeats the sweep in dark mode, against a narrow
filter slice, and against a slice that matches nobody.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

import app as application  # noqa: E402
import datamodel as dm  # noqa: E402

SCENARIOS = {
    "defaults (light)": ({"filters": {}, "min_n": 10}, "light"),
    "defaults (dark)": ({"filters": {}, "min_n": 10}, "dark"),
    "narrow slice": (
        {
            "filters": {
                "Department": ["Sales"],
                "JobRole": ["Sales Representative"],
                "OverTime": ["Yes"],
                "Age": [18, 40],
            },
            "min_n": 0,
        },
        "light",
    ),
    "empty slice": (
        {"filters": {"Department": ["Sales"], "JobRole": ["Research Director"]}, "min_n": 30},
        "dark",
    ),
    "single cohort": (
        {"filters": {"JobLevelLabel": ["Level 5"], "Gender": ["Female"]}, "min_n": 0},
        "light",
    ),
}


def layout_defaults(node, found: dict) -> dict:
    """Record every component's initial `value`, so payloads match the real UI."""
    cid = getattr(node, "id", None)
    if isinstance(cid, str):
        for prop in ("value", "data", "n_clicks", "n_intervals"):
            if prop in getattr(node, "_prop_names", ()):
                found[(cid, prop)] = getattr(node, prop, None)
    children = getattr(node, "children", None)
    if isinstance(children, (list, tuple)):
        for child in children:
            layout_defaults(child, found)
    elif children is not None and not isinstance(children, str):
        layout_defaults(children, found)
    return found


def _outputs_payload(output):
    """Dash stores outputs as dependency objects; the wire format is plain dicts."""

    def one(dep):
        if isinstance(dep, dict):
            return dep
        if isinstance(dep, str):
            component_id, _, prop = dep.rpartition(".")
            return {"id": component_id, "property": prop}
        return {"id": dep.component_id, "property": dep.component_property}

    if isinstance(output, (list, tuple)):
        return [one(dep) for dep in output]
    return one(output)


def main() -> int:
    app = application.app
    client = app.server.test_client()

    page = client.get("/")
    assert page.status_code == 200, f"index returned {page.status_code}"
    # Dash renders the layout in the browser, so the index only carries the shell.
    assert b"Attrition explorer" in page.data, "index is missing the document title"
    assert b'data-theme="light"' in page.data, "index is missing the theme attribute"
    print(f"index: {page.status_code} · {len(page.data):,} bytes")

    served_layout = client.get("/_dash-layout")
    assert served_layout.status_code == 200, "layout endpoint failed"
    assert b"Employee attrition explorer" in served_layout.data, "layout is missing its title"
    print(f"layout: {served_layout.status_code} · {len(served_layout.data):,} bytes")

    css = client.get("/assets/dashboard.css")
    print(f"stylesheet: {css.status_code} · {len(css.data):,} bytes")
    assert css.status_code == 200, "dashboard.css is not being served"

    defaults = layout_defaults(app.layout, {})
    # Clientside callbacks (the theme toggle) run in the browser - there is no
    # Python function behind them to POST to.
    clientside = {
        entry["output"]
        for entry in app._callback_list
        if entry.get("clientside_function")
    }
    failures: list[str] = []
    checked = 0

    for name, (slice_data, mode) in SCENARIOS.items():
        print(f"\n--- {name} ---")
        for output, spec in app.callback_map.items():
            if output in clientside:
                continue

            def value_for(dep) -> object:
                key = (dep["id"], dep["property"])
                if dep["id"] == "slice-store":
                    return slice_data
                if dep["id"] == "theme-store":
                    return mode
                if dep["property"] in ("n_clicks", "n_intervals"):
                    return 1
                return defaults.get(key)

            payload = {
                "output": output,
                "outputs": _outputs_payload(spec["output"]),
                "inputs": [
                    {**dep, "value": value_for(dep)} for dep in spec["inputs"]
                ],
                "changedPropIds": [
                    f"{dep['id']}.{dep['property']}" for dep in spec["inputs"]
                ],
                "state": [{**dep, "value": value_for(dep)} for dep in spec["state"]],
            }
            response = client.post(
                "/_dash-update-component",
                data=json.dumps(payload),
                content_type="application/json",
            )
            checked += 1
            label = output.split("...")[0] if "..." in output else output
            if response.status_code != 200:
                body = response.data.decode("utf-8", "replace")[-400:]
                failures.append(f"{name} · {label}: HTTP {response.status_code}\n{body}")
                print(f"  FAIL {label}: HTTP {response.status_code}")
            else:
                print(f"  ok   {label}")

    print(f"\n{checked} callback invocations, {len(failures)} failures")
    for failure in failures:
        print("\n" + failure)
    if not failures:
        frame = dm.load_data()
        print(
            f"\nData: {len(frame):,} rows · {len(frame.columns)} columns · "
            f"baseline attrition {dm.baseline_rate() * 100:.1f}%"
        )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
