"""
ynified core compiler.

Reads a directory containing a `_default.yaml` manifest and resolves
its custom YAML tags (!source, !eval, !query, ...) into a single
in-memory Python dict, which can then be serialized to JSON, YAML or
BSON via `ynified.output`.
"""
import base64
import json
import logging
import os

import bson
import yaml

from .exceptions import CompilerError, EvalError
from .query import Q
from .security import safe_eval, safe_join
from .tags import DEFAULT_TAGS, build_loader_class

logger = logging.getLogger(__name__)


class Compiler:
    """
    Two-pass manifest compiler.

    Pass 1 ("preload"): resolves every tag *except* !query (which has
    nothing to query yet), producing a JSON-safe snapshot of the data.
    Pass 2: resolves everything again, this time with !query and
    Query(...) inside !eval able to look up values from the pass-1
    snapshot (`self.preload_data`).
    """

    DEFAULT_MANIFEST = "_default.yaml"
    HIDDEN_PREFIX = "--"

    def __init__(self, source_dir, env=None, custom_tags=None):
        self.source_dir = os.path.abspath(source_dir)
        # Also used by the !envvar tag; the CLI passes the full process
        # environment here, but a library caller can pass any dict.
        self.env = dict(env or {})
        # User-supplied tags may add to or override the built-in ext:/valid: tags.
        self.custom_tags = {**DEFAULT_TAGS, **(custom_tags or {})}
        self.preload = False
        self.preload_data = {}
        self._loader_cls = build_loader_class(self)

    # -- public API ---------------------------------------------------

    def compile(self):
        """Run both passes and return the assembled dataset."""
        self.preload = True
        self.preload_data = self._run_pass()
        self.preload = False
        return self._run_pass()

    # -- pass machinery -------------------------------------------------

    def _run_pass(self):
        try:
            data = self.load_yaml(self.DEFAULT_MANIFEST)
        except (OSError, yaml.YAMLError) as exc:
            raise CompilerError(
                "failed to load manifest '%s': %s" % (self.DEFAULT_MANIFEST, exc)
            ) from exc

        if not data:
            raise CompilerError(
                "nothing to compile: '%s' produced no data"
                % os.path.join(self.source_dir, self.DEFAULT_MANIFEST)
            )
        if not isinstance(data, dict):
            raise CompilerError(
                "root node of '%s' must be a mapping, got %s"
                % (os.path.join(self.source_dir, self.DEFAULT_MANIFEST), type(data).__name__)
            )

        visible = {
            key: value
            for key, value in data.items()
            if not str(key).startswith(self.HIDDEN_PREFIX)
        }

        if self.preload:
            # Normalize through a JSON round-trip so !query / Query(...)
            # only ever see plain JSON-safe data (no bytes, datetimes,
            # etc. that a tag may have produced). Done in memory -- the
            # original implementation wrote this snapshot to a
            # predictable path under /tmp, which was both an
            # unnecessary round-trip and an information-disclosure /
            # race-condition risk on multi-user machines.
            return json.loads(json.dumps(visible, default=str))
        return visible

    # -- tag implementations -------------------------------------------

    def load_yaml(self, filename):
        path = safe_join(self.source_dir, filename)
        logger.debug("%s %s", "Processing" if self.preload else "Adding source", filename)
        with open(path, "r", encoding="utf-8") as fh:
            return yaml.load(fh, Loader=self._loader_cls)

    def load_bson(self, filename):
        path = safe_join(self.source_dir, filename)
        logger.debug("%s %s", "Processing" if self.preload else "Adding source", filename)
        with open(path, "rb") as fh:
            return bson.loads(fh.read())

    def load_text(self, filename):
        path = safe_join(self.source_dir, filename)
        logger.debug("Loading file... %s", filename)
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()

    def load_b64(self, filename):
        path = safe_join(self.source_dir, filename)
        logger.debug("Loading file... %s", filename)
        with open(path, "rb") as fh:
            return base64.b64encode(fh.read()).decode("ascii")

    def load_bin(self, filename):
        path = safe_join(self.source_dir, filename)
        logger.debug("Loading file... %s", filename)
        with open(path, "rb") as fh:
            return list(fh.read())

    def pyeval(self, expression):
        env = dict(self.env)
        # During preload, real data isn't assembled yet: Query() returns a
        # neutral placeholder so arithmetic !eval expressions don't crash.
        # The final pass re-evaluates everything with real data anyway.
        env["Query"] = (lambda q: 0) if self.preload else (lambda q: Q(self.preload_data, q))
        env["Info"] = {"generator": "ynified"}
        try:
            return safe_eval(expression, env)
        except EvalError:
            raise
        except Exception as exc:  # pragma: no cover - defensive net
            raise EvalError("%r: %s" % (expression, exc)) from exc


def compile_dataset(source_dir, env=None, custom_tags=None):
    """Convenience wrapper: compile a manifest directory into a dict."""
    return Compiler(source_dir, env=env, custom_tags=custom_tags).compile()
