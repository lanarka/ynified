import re
from types import SimpleNamespace

from ynified.tools import gen_timestamp, gen_uuid4, join_strings

UUID4_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$", re.I
)


def test_gen_uuid4_looks_like_a_uuid4():
    assert UUID4_RE.match(gen_uuid4())


def test_gen_uuid4_is_random():
    assert gen_uuid4() != gen_uuid4()


def test_gen_timestamp_uses_given_format():
    value = gen_timestamp("%Y")
    assert value.isdigit() and len(value) == 4


def test_gen_timestamp_default_format():
    value = gen_timestamp(None)
    # default format: YYYY-MM-DD HH:MM:SS
    assert re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", value)


def test_join_strings_passes_through_plain_string():
    assert join_strings("already a string") == "already a string"


def test_join_strings_concatenates_scalar_nodes():
    nodes = [SimpleNamespace(value="Hello"), SimpleNamespace(value=" "), SimpleNamespace(value="World")]
    assert join_strings(nodes) == "Hello World"


def test_join_strings_handles_plain_values_too():
    assert join_strings(["a", "b", "c"]) == "abc"
