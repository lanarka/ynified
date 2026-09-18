"""
Serializing a compiled dataset (a plain dict) to bytes, and writing it
to disk. Kept separate from Compiler so it is trivial to unit test and
to reuse (e.g. to serialize to bytes without touching the filesystem).
"""
import gzip
import json
import bson
import yaml

SUPPORTED_FORMATS = ("json", "yaml", "bson")


def serialize(data, fmt):
    if fmt == "json":
        return json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
    if fmt == "yaml":
        return yaml.safe_dump(data, allow_unicode=True, sort_keys=True).encode("utf-8")
    if fmt == "bson":
        return bson.dumps(data)
    raise ValueError(
        "unsupported output format %r (expected one of %s)" % (fmt, SUPPORTED_FORMATS)
    )


def write_output(data, output_path, fmt, gzip_compress=False):
    payload = serialize(data, fmt)
    if gzip_compress:
        payload = gzip.compress(payload)
    with open(output_path, "wb") as fh:
        fh.write(payload)
    return len(payload)
