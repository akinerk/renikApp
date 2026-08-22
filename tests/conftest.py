import os
import sys
import tempfile
from pathlib import Path

import pytest


os.environ.setdefault(
    "RENIKAPP_DB_PATH",
    os.path.join(tempfile.gettempdir(), f"renikapp-test-{os.getpid()}.db"),
)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import app, login_attempts  # noqa: E402


@pytest.fixture()
def client():
    app.config.update(TESTING=True)
    login_attempts.clear()
    with app.test_client() as test_client:
        yield test_client
