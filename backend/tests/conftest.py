import os
import sys
import tempfile
from pathlib import Path

# Isolated data folder and no LLM for every test run (set before the app is imported).
os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="termguard-test-")
os.environ["LLM_API_KEY"] = ""
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixture_bytes():
    def load(name: str) -> bytes:
        return (FIXTURES / name).read_bytes()
    return load
