"""Start the renikApp local training lab without enabling Flask's reloader."""

import os
import tempfile

os.environ.setdefault(
    "RENIKAPP_DB_PATH",
    os.path.join(tempfile.gettempdir(), "renikapp-dev-users.db"),
)
from app import app


if __name__ == "__main__":
    port = int(os.getenv("RENIKAPP_PORT", "5000"))
    app.run(debug=False, use_reloader=False, port=port)
