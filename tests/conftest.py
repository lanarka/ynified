import os

import pytest

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")


@pytest.fixture
def sources_example_dir():
    return os.path.join(EXAMPLES_DIR, "01-sources")


@pytest.fixture
def computation_example_dir():
    return os.path.join(EXAMPLES_DIR, "02-computation")


@pytest.fixture
def validators_example_dir():
    return os.path.join(EXAMPLES_DIR, "03-validators")


@pytest.fixture
def utilities_example_dir():
    return os.path.join(EXAMPLES_DIR, "04-utilities")


@pytest.fixture
def tmp_source_dir(tmp_path):
    """An empty, writable manifest directory a test can populate."""
    return tmp_path
