"""
Small utility tools exposed as YAML tags under the `ext:` namespace:
!ext:uuid4, !ext:timestamp, !ext:joinstr, !ext:sha256-str.
(!ext:sha256, which hashes a *file*, needs the compiler's source
directory to resolve the path safely -- it lives in tags.py alongside
!source/!load-*, not here.)
"""
import datetime
import hashlib
import uuid

DEFAULT_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


def gen_uuid4():
    """Return a fresh random UUID4 as a string."""
    return str(uuid.uuid4())


def gen_timestamp(fmt=None):
    """Return the current local time formatted with a strftime pattern."""
    return datetime.datetime.now().strftime(fmt or DEFAULT_TIMESTAMP_FORMAT)


def join_strings(items):
    """
    Concatenate a YAML sequence of scalars (and/or aliases) into one
    string. Used by !ext:joinstr, e.g.:

        title: !ext:joinstr [*name, " ", *version]
    """
    if isinstance(items, str):
        return items
    parts = []
    for item in items:
        value = getattr(item, "value", item)
        parts.append(str(value))
    return "".join(parts)


def sha256_of_string(text):
    """Return the SHA256 hex digest of a string (UTF-8 encoded)."""
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()
