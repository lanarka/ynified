"""
Builds a private yaml.SafeLoader subclass per Compiler instance, with
all built-in and custom tags bound to that instance.

Why a private subclass instead of registering on yaml.SafeLoader
directly (as the original implementation did)? yaml.add_constructor()
mutates a *class-level* registry. Registering there means every
Compiler instance overwrites the tag handlers of every other one, so
two Compiler objects alive at the same time (in the same process --
e.g. used as a library, or two datasets compiled from one script) step
on each other's toes. A fresh subclass per instance keeps each
compilation fully isolated.

Every constructor below is wrapped by `_wrap_tag`, so any failure
(a missing file, a bad !eval expression, a failed validator, an
exception raised by a user-supplied custom tag, ...) is reported with
the exact "file:line:column" of the tag that caused it, instead of a
bare Python traceback.
"""
import yaml

from .exceptions import EnvVarError, TagError, YnifiedError
from .query import Q
from .tools import gen_timestamp, gen_uuid4, join_strings
from .validators import validate_float, validate_int, validate_ipv4, validate_ipv6

# Tags that are always available, in the `ext:` (small utilities) and
# `valid:` (strict input validators) namespaces. Each handler receives
# the raw YAML node and returns the value to embed in the tree.
DEFAULT_TAGS = {
    "ext:uuid4": lambda node: gen_uuid4(),
    "ext:timestamp": lambda node: gen_timestamp(node.value),
    "ext:joinstr": lambda node: join_strings(node.value),
    "valid:ipv4": lambda node: validate_ipv4(node.value),
    "valid:ipv6": lambda node: validate_ipv6(node.value),
    "valid:int": lambda node: validate_int(node.value),
    "valid:float": lambda node: validate_float(node.value),
}


def _wrap_tag(tag_name, handler):
    """Wrap a `(node) -> value` handler so its failures carry a location."""

    def _constructor(loader, node):
        try:
            return handler(node)
        except YnifiedError as exc:
            raise TagError(tag_name, str(exc), node.start_mark) from exc
        except Exception as exc:  # noqa: BLE001 - deliberately broad, see module docstring
            raise TagError(tag_name, str(exc), node.start_mark) from exc

    return _constructor


def _envvar(compiler, node):
    name = str(node.value).strip()
    if name not in compiler.env:
        raise EnvVarError("environment variable '%s' is not set" % name)
    return compiler.env[name]


def build_loader_class(compiler):
    """Return a new SafeLoader subclass wired up to `compiler`."""

    class YnifiedLoader(yaml.SafeLoader):
        pass

    def _source(node):
        return compiler.load_yaml(str(node.value))

    def _source_bson(node):
        return compiler.load_bson(str(node.value))

    def _load_text(node):
        return compiler.load_text(node.value)

    def _load_binary(node):
        return compiler.load_bin(node.value)

    def _load_base64(node):
        return compiler.load_b64(node.value)

    def _eval(node):
        return compiler.pyeval(node.value)

    def _query(node):
        if compiler.preload:
            # The pre-pass has no resolved data yet to query against.
            return None
        return Q(compiler.preload_data, node.value)

    builtin_tags = {
        "source": _source,
        "source-bson": _source_bson,
        "load-text": _load_text,
        "load-binary": _load_binary,
        "load-base64": _load_base64,
        "eval": _eval,
        "query": _query,
        "envvar": lambda node: _envvar(compiler, node),
    }

    all_tags = dict(builtin_tags)
    all_tags.update(compiler.custom_tags)

    for tag_name, handler in all_tags.items():
        YnifiedLoader.add_constructor("!%s" % tag_name, _wrap_tag(tag_name, handler))

    return YnifiedLoader
