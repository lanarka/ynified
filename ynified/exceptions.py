"""
Central exception hierarchy for ynified.

Everything the library can raise on purpose derives from YnifiedError,
so callers can do `except YnifiedError` to catch any "expected" failure
(bad manifest, bad expression, bad path, ...) and let anything else
(programming bugs) propagate as a real traceback.
"""


class YnifiedError(Exception):
    """Base class for all ynified errors."""


class CompilerError(YnifiedError):
    """Raised for structural problems with the manifest being compiled."""


class EvalError(YnifiedError):
    """Raised when a !eval expression fails to evaluate."""


class UnsafeExpressionError(EvalError):
    """Raised when a !eval expression uses a disallowed construct."""


class PathTraversalError(YnifiedError):
    """Raised when a referenced file would resolve outside the source directory."""


class ValidationError(YnifiedError):
    """Raised by input validators (IPv4/IPv6/int/float) on bad input."""


class EnvVarError(YnifiedError):
    """Raised by !envvar when the requested environment variable is missing."""


class QueryError(YnifiedError):
    """Base class for query-path errors."""


class QueryParseError(QueryError):
    """Raised when a query-path string cannot be parsed."""


class QueryDataError(QueryError):
    """Raised when a parsed query-path cannot be resolved against the data."""


def format_mark(mark):
    """
    Render a yaml Mark (or None) as "path:line:column" for error
    messages. yaml marks are 0-indexed; humans count from 1.
    """
    if mark is None:
        return "<unknown location>"
    name = getattr(mark, "name", "<unknown source>")
    return "%s:%d:%d" % (name, mark.line + 1, mark.column + 1)


class TagError(YnifiedError):
    """
    Raised whenever resolving a YAML tag (!source, !eval, !valid:int, a
    user-supplied custom tag, ...) fails for any reason. Wraps the
    original error together with the tag name and its exact location
    (file, line, column) in the manifest source, so failures point
    straight at the offending line instead of a bare Python traceback.
    """

    def __init__(self, tag, message, mark=None):
        self.tag = tag
        self.mark = mark
        self.original_message = message
        super().__init__("%s: !%s %s" % (format_mark(mark), tag, message))
