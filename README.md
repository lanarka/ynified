# ynified

**ynified** composes one JSON/YAML/BSON dataset out of many source files.

You point it at a directory containing a `_default.yaml` manifest, and
it resolves a set of custom YAML tags (`!source`, `!eval`, `!query`,
`!envvar`, input validators, small utilities...) into a single Python
object, which it then serializes to JSON, YAML or BSON.

It's meant as a small, embeddable building block for generating
config files, fixtures, or any other "dense" dataset that's easier to
maintain as several small, composable source files than as one giant
blob.

## Install

```bash
poetry install
```

## Quick example

```bash
ynified examples/simple --to json
```

```yaml
# examples/simple/_default.yaml
title: !ext:joinstr [My App, " v", "1.0"]
build_id: !ext:uuid4
port: !valid:int "8080"
```

See [DOC.md](DOC.md) for the full list of tags and how the compiler
works, and the `examples/` directory for runnable demos.

## Tests

```bash
pytest tests/
```
