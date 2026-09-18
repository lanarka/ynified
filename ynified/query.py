"""
ynified query -- a tiny "dot path" DSL for pulling a value out of
nested dict/list data, used by the !query tag and by Query(...) inside
!eval expressions.

Example
-------
    Q(data, "foo.0.bar.baz")           # data["foo"][0]["bar"]["baz"]
    Q(data, 'foo."Hello World".baz')   # quoted segment with spaces

This implementation walks the parsed path directly against the data
(plain dict/list indexing) -- it never builds a string and eval()s it,
so a query path cannot be used to run arbitrary code.
"""
import re
import shlex

from .exceptions import QueryDataError, QueryParseError

QUOTE = '"'
DOT = "."

_ILLEGAL_CHARS = re.compile(r"[^.,~a-zA-Z0-9_]")


def _is_quoted(token):
    return len(token) >= 2 and token[0] == QUOTE and token[-1] == QUOTE


def _strip_quotes(token):
    return token[1:-1]


def _is_plain_and_legal(token):
    return not bool(_ILLEGAL_CHARS.search(token))


class QueryCompiler:
    """Parses a dot-path query string into a list of path elements."""

    def __init__(self, query):
        self.query = query
        self.parsed = self.parse()

    def parse(self):
        if not isinstance(self.query, str):
            raise QueryParseError("query must be a string, got %r" % type(self.query))

        tokens = list(shlex.shlex(self.query, posix=False))
        if not tokens:
            raise QueryParseError("empty query")

        elements = []
        for token in tokens:
            if token == DOT:
                continue
            if _is_quoted(token):
                elements.append(_strip_quotes(token))
                continue
            if not _is_plain_and_legal(token):
                raise QueryParseError("illegal character in query segment %r" % token)
            elements.append(token)

        if not elements:
            raise QueryParseError("query %r has no path segments" % self.query)

        path = []
        for element in elements:
            try:
                path.append(int(element))
            except ValueError:
                path.append(element)
        return path

    def resolve(self, data):
        """Walk `self.parsed` against `data` and return the value found."""
        current = data
        walked = []
        for element in self.parsed:
            walked.append(element)
            try:
                current = current[element]
            except (KeyError, IndexError, TypeError) as exc:
                raise QueryDataError(
                    "cannot resolve %r in query %r (%s)"
                    % (".".join(str(w) for w in walked), self.query, exc)
                ) from exc
        return current

    # Kept for backwards compatibility with earlier call sites.
    def throw(self, data):
        return self.resolve(data)


def Q(data, query):
    """Shorthand: Q(data, "a.b.0.c") -> value, or raises QueryError."""
    return QueryCompiler(query).resolve(data)
