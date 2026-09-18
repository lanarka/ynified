# ynified — documentation

## Concept

A **manifest** is a directory containing a `_default.yaml` file. It is
the root of the dataset you want to produce — think of it as a
Makefile-like entry point. Everything else in the directory is a
source file the manifest can pull in.

```
myapp/
├── _default.yaml      <- entry point
├── root.yaml
└── res/
    └── countries.json
```

Running:

```bash
ynified myapp --to json
```

reads `myapp/_default.yaml`, resolves every custom YAML tag it
contains (`!source`, `!eval`, `!valid:int`, ...), and writes the
result to `myapp.json`.

## Two-pass compilation

The manifest is compiled twice:

1. **Preload pass** — every tag is resolved *except* `!query`, which
   has nothing to query yet (it returns `null` here). The result is
   normalized through a JSON round-trip, so it only ever contains
   plain JSON-safe values.
2. **Final pass** — everything is resolved again. This time `!query`
   and the `Query(...)` helper inside `!eval` can look up any value
   produced by the first pass, including values nested arbitrarily
   deep, by other tags, in other files.

This is what lets one part of a manifest reference a value computed by
another part, regardless of the order they appear in.

## Hidden keys

Any **top-level** key in `_default.yaml` starting with `--` is
resolved (so `!source`/`!eval`/... inside it still run, and other tags
can `!query` into it) but is **not included in the final output**.
Use this for staging values you only need as inputs to other tags:

```yaml
--module3: &module3 !source here/here/module3.yaml
# `module3` is available via the *module3 anchor elsewhere in the
# manifest, but "--module3" itself will not appear in the output.
```

## Renaming the output root

Because YAML lets an anchor be used as a mapping key, you can compute
the name of a top-level key at "compile time":

```yaml
id: &root hello_world

*root:
  a: 1
  b: 2
```

produces `{"hello_world": {"a": 1, "b": 2}}`.

## CLI

```
ynified <source_dir> [--to json|yaml|bson] [--gzip] [-o OUTPUT] [-v]

  source_dir            directory containing a _default.yaml manifest
  --to {json,yaml,bson} output format (default: json)
  --gzip                gzip-compress the output file
  -o, --output OUTPUT   output file path (default: <source_dir>.<format>[.gz])
  -v, --verbose         -v: info logging + pretty-printed preview
                        -vv: debug logging (every file/tag as it's processed)
  --version
```

The entire process environment is available to `!envvar` and to
`!eval` expressions (as plain names) when run from the CLI.

## Error messages

Any failure while resolving a tag — a missing file, a bad expression,
a validator rejecting its input, an exception in your own custom tag —
is reported as:

```
<file>:<line>:<column>: !<tag> <what went wrong>
```

For example:

```
$ ynified myapp
myapp/_default.yaml:4:9: !valid:int '12.5' is not a valid integer
```

If the failing tag lives inside a file pulled in with `!source`, the
location points at *that* file, not at the top-level manifest — so the
error always points at the actual line to fix.

Plain YAML syntax mistakes (bad indentation, unknown tags, ...) are
reported the same way, using PyYAML's own file/line/column-aware
messages.

---

## Tag reference

### Composition

#### `!source <path>`

Load another YAML (or JSON — JSON is valid YAML) file, relative to the
manifest directory, and inline it as the value of this node. Nested
`!source` calls work: a sourced file can itself `!source` further
files.

```yaml
app: !source app.yaml
```

#### `!source-bson <path>`

Same as `!source`, but the file is BSON instead of YAML/JSON.

```yaml
cached: !source-bson snapshot.bson
```

#### `!load-text <path>`

Inline the raw text content of a file as a string.

```yaml
page: !load-text page.html
```

#### `!load-binary <path>`

Inline the raw bytes of a file as a list of integers (0–255), one per
byte.

```yaml
icon: !load-binary icon.png
```

#### `!load-base64 <path>`

Inline the content of a file, base64-encoded, as a string.

```yaml
icon_b64: !load-base64 icon.png
```

All of `!source`, `!source-bson`, `!load-text`, `!load-binary` and
`!load-base64` resolve their path against the manifest directory and
refuse to resolve outside it (no `../../etc/passwd`, no absolute
paths) — see [Security](#security) below.

### Computation

#### `!query <dot.path>`

Look up a value elsewhere in the (already-preloaded) dataset using a
small "dot path" language:

```yaml
a:
  x: 10
b: !query a.x        # -> 10
```

- Numeric segments index into lists: `a.0.name`
- Quoted segments allow arbitrary characters (spaces, punctuation):
  `a."some odd key".b`
- `#` starts a comment, same as in Python/YAML.

`!query` can only see data produced by the *preload* pass (see
[Two-pass compilation](#two-pass-compilation)); it returns `null`
while the preload pass itself is running.

#### `!eval <python-expression>`

Evaluate a single Python expression and use its result as the value of
this node.

```yaml
total: !eval 10 * 4 + 2
```

Two names are always available inside `!eval`:

- **`Query("dot.path")`** — same lookup as the `!query` tag, usable
  inside a larger expression:

  ```yaml
  a:
    x: 10
  b: !eval Query("a.x") * 2 + 1     # -> 21
  ```

- **`Info`** — a small dict describing the running compiler, currently
  `{"generator": "ynified"}`.

Every process environment variable is also available by name (the CLI
passes the full environment in). A small set of safe builtins
(`int`, `float`, `str`, `len`, `abs`, `min`, `max`, `sum`, `round`,
`sorted`, `list`, `dict`, `tuple`, `set`, `range`, `enumerate`, `zip`,
`map`, `filter`, `any`, `all`, `bool`, `True`, `False`, `None`) are
available too. Everything else — `open`, `import`, `exec`, `eval`,
attribute access to `__dunder__` names, and a handful of other
introspection/IO builtins — is rejected before the expression ever
runs. See [Security](#security).

#### `!envvar <NAME>`

Read a single environment variable and use it as a string value.
Fails loudly (with file/line/column) if the variable isn't set.

```yaml
region: !envvar AWS_REGION
```

```bash
AWS_REGION=eu-west-1 ynified myapp
```

### Validators (`valid:` namespace)

Validators check that the given scalar is well-formed and raise a
clear error otherwise — they don't silently coerce bad input.

#### `!valid:ipv4 <address>`

```yaml
gateway: !valid:ipv4 192.168.0.1
```
```json
{"gateway": {"$ipv4": [192, 168, 0, 1]}}
```

#### `!valid:ipv6 <address>`

```yaml
gateway6: !valid:ipv6 "::1"
```
```json
{"gateway6": {"$ipv6": [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1]}}
```

#### `!valid:int <text>`

Accepts a plain decimal integer only (`"42"`, `"-7"`) — rejects
`"1.0"`, `"1e3"`, `"1,000"`, non-numeric text.

```yaml
port: !valid:int "8080"     # -> 8080 (int)
```

#### `!valid:float <text>`

Accepts a plain or scientific-notation real number (`"1.5"`, `".5"`,
`"1e-3"`) — rejects `"nan"`, `"inf"`, thousands separators,
non-numeric text.

```yaml
ratio: !valid:float "0.875" # -> 0.875 (float)
```

### Utilities (`ext:` namespace)

#### `!ext:uuid4`

A fresh random UUID4 string. Takes no argument.

```yaml
build_id: !ext:uuid4
```

#### `!ext:timestamp <strftime-format>`

The current local time, formatted with a `strftime` pattern.

```yaml
built_at: !ext:timestamp "%Y-%m-%d %H:%M:%S"
```

#### `!ext:joinstr [a, b, ...]`

Concatenate a YAML sequence of scalars (and/or aliases) into one
string. Handy for building a value out of several anchors:

```yaml
name: &name My App
version: &version "1.0.0"
title: !ext:joinstr [*name, " v", *version]   # -> "My App v1.0.0"
```

---

## Security

`!eval` and the file-loading tags accept input from the manifest
author, not from an end user — treat manifests the same way you'd
treat any other code you run. Two things are hardened, but neither is
a full sandbox:

- **`!eval`** runs with no builtins beyond a small allow-list, and an
  AST check rejects `import`, `exec`, `eval`, `open`,
  `__dunder__`-attribute access and a few other introspection
  builtins before the expression is ever executed. This blocks the
  common escape routes and any accidental misuse, but Python has no
  fully secure `eval()` sandbox — a sufficiently motivated,
  adversarial manifest could very likely still find a way out. Only
  compile manifests you trust.
- **File-loading tags** (`!source`, `!source-bson`, `!load-text`,
  `!load-binary`, `!load-base64`) resolve their path against the
  manifest directory and reject anything that would resolve outside
  it (`../..` traversal, absolute paths).

---

## Using ynified as a library

```python
from ynified import Compiler

compiler = Compiler(
    "myapp",
    env={"AWS_REGION": "eu-west-1"},      # available to !envvar and !eval
    custom_tags={
        "shout": lambda node: node.value.upper(),   # adds !shout
    },
)
data = compiler.compile()  # -> dict
```

`custom_tags` maps a tag name (without the leading `!`) to a function
taking the raw YAML node and returning the value to embed. Exceptions
raised inside it are automatically reported with file/line/column,
the same way built-in tags are.

`ynified.output.serialize(data, fmt)` / `write_output(data, path, fmt,
gzip_compress=False)` turn a compiled dict into `json`/`yaml`/`bson`
bytes, independently of the CLI.
