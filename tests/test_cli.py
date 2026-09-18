import json

from ynified.cli import main


def write(path, text):
    path.write_text(text, encoding="utf-8")


def test_cli_builds_json_by_default(tmp_path, capsys):
    write(tmp_path / "_default.yaml", "a: 1\n")
    output = tmp_path / "out.json"
    rc = main([str(tmp_path), "-o", str(output)])
    assert rc == 0
    assert json.loads(output.read_text()) == {"a": 1}


def test_cli_defaults_output_path_next_to_source_dir(tmp_path):
    write(tmp_path / "_default.yaml", "a: 1\n")
    rc = main([str(tmp_path)])
    assert rc == 0
    expected = str(tmp_path).rstrip("/") + ".json"
    assert json.loads(open(expected).read()) == {"a": 1}


def test_cli_supports_yaml_and_gzip(tmp_path):
    import gzip

    import yaml

    write(tmp_path / "_default.yaml", "a: 1\n")
    output = tmp_path / "out.yaml.gz"
    rc = main([str(tmp_path), "--to", "yaml", "--gzip", "-o", str(output)])
    assert rc == 0
    with gzip.open(output, "rt") as fh:
        assert yaml.safe_load(fh) == {"a": 1}


def test_cli_reports_a_clean_error_for_missing_manifest(tmp_path, capsys):
    rc = main([str(tmp_path)])
    assert rc == 1


def test_cli_rejects_unknown_format():
    with __import__("pytest").raises(SystemExit):
        main(["some_dir", "--to", "xml"])
