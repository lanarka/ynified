import os

import pytest

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")


@pytest.fixture
def simple_dir():
    return os.path.join(EXAMPLES_DIR, "simple")


@pytest.fixture
def complex_dir():
    return os.path.join(EXAMPLES_DIR, "complex")


@pytest.fixture
def tmp_source_dir(tmp_path):
    """An empty, writable manifest directory a test can populate."""
    return tmp_path
