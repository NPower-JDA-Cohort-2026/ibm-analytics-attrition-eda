"""Employee attrition explorer - a Dash app over the IBM HR Analytics dataset.

Run it from the project root:

    .venv/Scripts/python dashboards/app/app.py

then open http://127.0.0.1:8050. ``--debug`` turns on hot reload, ``--port`` and
``--host`` move the server.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from dash import Dash  # noqa: E402

import callbacks  # noqa: E402
import datamodel  # noqa: E402
import layout  # noqa: E402

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="en" data-theme="light">
    <head>
        {%metas%}
        <title>{%title%}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <meta name="description"
              content="Interactive exploration of employee attrition in the IBM HR
                       Analytics dataset - filter by role, department and level.">
        {%favicon%}
        {%css%}
        <script>
          // Seed the palette before first paint so the page never flashes the
          // wrong mode. The boot callback re-reads the same value for Plotly.
          (function () {
            try {
              var saved = window.localStorage.getItem('attrition-theme');
              var dark = saved
                ? saved === 'dark'
                : window.matchMedia &&
                  window.matchMedia('(prefers-color-scheme: dark)').matches;
              document.documentElement.setAttribute(
                'data-theme', dark ? 'dark' : 'light');
            } catch (e) {}
          })();
        </script>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>"""


def create_app() -> Dash:
    app = Dash(
        __name__,
        title="Attrition explorer - IBM HR Analytics",
        update_title=None,
        # Tab panels unmount when another tab is selected, so their callbacks
        # are registered against components that are not always in the DOM.
        suppress_callback_exceptions=True,
    )
    app.index_string = INDEX_TEMPLATE
    app.layout = layout.build_layout()
    callbacks.register(app)
    return app


app = create_app()
#: WSGI entry point for gunicorn / waitress: ``dashboards.app.app:server``
server = app.server


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the attrition dashboard.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8050)
    parser.add_argument("--debug", action="store_true", help="enable hot reload")
    args = parser.parse_args()

    frame = datamodel.load_data()
    print(
        f"Loaded {len(frame):,} employee records "
        f"({datamodel.baseline_rate() * 100:.1f}% company attrition)."
    )
    print(f"Dashboard: http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
