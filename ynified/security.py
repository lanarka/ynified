"""
Security helpers used by the !eval tag and by every file-loading tag
(!source, !source-bson, !load-text, !load-binary, !load-base64).

honest disclaimer:

`safe_eval()` below meaningfully reduces the attack surface of Python's
`eval()` (no builtins, no dunder-attribute access, no import statements,
no exec/compile/open/...), but there is no such thing as a fully secure
`eval()` sandbox in pure Python -- a sufficiently motivated author of a
malicious manifest can very likely still find an escape (this is a well
known, long-standing limitation of the language, not something specific
to this implementation). Treat !eval as "safe against accidents and
casual mistakes in trusted sources", *not* as a boundary against
untrusted or adversarial input. Only compile manifests you trust.
"""
import ast
import builtins as _builtins_module
import os

from .exceptions import PathTraversalError, UnsafeExpressionError

# Names that must never resolve inside a !eval expression, even though
# some of them are not real builtins (e.g. __builtins__) -- they are
# blocked defensively in case something injects them into the eval
# namespace by accident.
_FORBIDDEN_NAMES = frozenset({
    "__import__", "exec", "eval", "compile", "open", "input",
    "globals", "locals", "vars", "dir", "getattr", "setattr",
    "delattr", "breakpoint", "exit", "quit", "help", "memoryview",
    "__builtins__", "__loader__", "__spec__", "__debug__",
})

# A small, deliberately conservative allow-list of builtins that are
# genuinely useful for shaping dataset values and carry no I/O, import
# or introspection capability.
_ALLOWED_BUILTIN_NAMES = (
    "abs", "all", "any", "bool", "dict", "enumerate", "filter", "float",
    "int", "len", "list", "map", "max", "min", "range", "round", "set",
    "sorted", "str", "sum", "tuple", "zip", "True", "False", "None",
)

SAFE_BUILTINS = {
    name: getattr(_builtins_module, name)
    for name in _ALLOWED_BUILTIN_NAMES
    if hasattr(_builtins_module, name)
}


def _check_ast(tree, expression):
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise UnsafeExpressionError(
                "import statements are not allowed in !eval: %r" % expression
            )
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            raise UnsafeExpressionError(
                "access to dunder attribute '%s' is not allowed in !eval: %r"
                % (node.attr, expression)
            )
        if isinstance(node, ast.Name) and node.id in _FORBIDDEN_NAMES:
            raise UnsafeExpressionError(
                "use of '%s' is not allowed in !eval: %r" % (node.id, expression)
            )


def safe_eval(expression, env):
    """
    Evaluate a single Python expression with no builtins except a small
    allow-list, and with dunder-attribute access / import statements /
    a handful of dangerous names rejected up front by an AST check.

    Raises UnsafeExpressionError if the expression is not a single
    expression, or uses a disallowed construct.
    """
    if not isinstance(expression, str):
        raise UnsafeExpressionError("!eval expects a string expression")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise UnsafeExpressionError(
            "invalid expression for !eval: %r (%s)" % (expression, exc)
        ) from exc

    _check_ast(tree, expression)

    code = compile(tree, "<ynified:eval>", "eval")
    safe_globals = {"__builtins__": SAFE_BUILTINS}
    # env holds process environment variables plus the Query()/Info
    # helpers injected by the compiler; none of those are risky.
    safe_globals.update(env)
    return eval(code, safe_globals)


def safe_join(base_dir, relative_path):
    """
    Resolve `relative_path` against `base_dir` and guarantee the result
    stays inside `base_dir`. Raises PathTraversalError otherwise
    """
    if not isinstance(relative_path, str) or not relative_path.strip():
        raise PathTraversalError("empty or invalid file path")

    base_real = os.path.realpath(base_dir)
    candidate = os.path.join(base_real, relative_path)
    target_real = os.path.realpath(candidate)

    try:
        common = os.path.commonpath([base_real, target_real])
    except ValueError:
        common = None

    if common != base_real:
        raise PathTraversalError(
            "path %r escapes source directory %r" % (relative_path, base_dir)
        )
    return target_real
