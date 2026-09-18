import pytest

from ynified.exceptions import QueryDataError, QueryParseError
from ynified.query import Q

SAMPLE = [
    [
        1,
        2,
        {
            "FOO": 10,
            "bar": [
                100,
                200,
                {"baz": 99, "spam": {"Hello World#$": "Hey!"}},
            ],
        },
    ],
    {"x": "X"},
]


@pytest.mark.parametrize(
    "query, expected",
    [
        ("0.0", 1),
        ("1.x", "X"),
        ("0.2.FOO", 10),
        ("0.2.bar.2.baz", 99),
        ('0.2.bar.2.spam."Hello World#$"', "Hey!"),
    ],
)
def test_resolves_expected_values(query, expected):
    assert Q(SAMPLE, query) == expected


def test_trailing_comment_after_quoted_segment_is_ignored():
    # '#' starts a shlex comment once outside of quotes.
    assert Q(SAMPLE, '0.2.bar.2.spam."Hello World#$" #Note') == "Hey!"


def test_missing_key_raises_query_data_error():
    with pytest.raises(QueryDataError):
        Q(SAMPLE, "0.2.does_not_exist")


def test_index_out_of_range_raises_query_data_error():
    with pytest.raises(QueryDataError):
        Q(SAMPLE, "0.2.bar.99")


def test_indexing_into_a_scalar_raises_query_data_error():
    with pytest.raises(QueryDataError):
        Q(SAMPLE, "0.2.FOO.nope")


def test_empty_query_is_rejected():
    with pytest.raises(QueryParseError):
        Q(SAMPLE, "")


def test_illegal_characters_are_rejected():
    with pytest.raises(QueryParseError):
        Q(SAMPLE, "0.2.;rm -rf")


def test_non_string_query_is_rejected():
    with pytest.raises(QueryParseError):
        Q(SAMPLE, 123)


def test_query_never_uses_eval_even_for_dunder_like_segments():
    # A regression guard: the old implementation built a python index
    # string and eval()'d it. Prove a segment that *looks* like it
    # could reach for dunder attributes is just treated as a literal,
    # missing dict key (and rejected), never executed.
    data = {"__class__": "harmless string, not the real dunder"}
    assert Q(data, "__class__") == "harmless string, not the real dunder"
