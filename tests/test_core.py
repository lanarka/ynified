import json

import pytest

from ynified.core import Compiler, compile_dataset
from ynified.exceptions import (
    CompilerError,
    EvalError,
    PathTraversalError,
    TagError,
    UnsafeExpressionError,
)


def write(path, text):
    path.write_text(text, encoding="utf-8")


class TestBasics:
    def test_hidden_top_level_keys_are_stripped(self, tmp_path):
        write(tmp_path / "_default.yaml", "--secret: 1\nvisible: 2\n")
        data = compile_dataset(str(tmp_path))
        assert data == {"visible": 2}

    def test_missing_manifest_raises_compiler_error(self, tmp_path):
        with pytest.raises((CompilerError, OSError)):
            compile_dataset(str(tmp_path))

    def test_non_mapping_root_raises_compiler_error(self, tmp_path):
        write(tmp_path / "_default.yaml", "- 1\n- 2\n")
        with pytest.raises(CompilerError):
            compile_dataset(str(tmp_path))

    def test_empty_manifest_raises_compiler_error(self, tmp_path):
        write(tmp_path / "_default.yaml", "")
        with pytest.raises(CompilerError):
            compile_dataset(str(tmp_path))


class TestSourceTag:
    def test_source_merges_another_yaml_file(self, tmp_path):
        write(tmp_path / "_default.yaml", "extra: !source part.yaml\n")
        write(tmp_path / "part.yaml", "a: 1\nb: 2\n")
        data = compile_dataset(str(tmp_path))
        assert data == {"extra": {"a": 1, "b": 2}}

    def test_source_cannot_escape_the_source_directory(self, tmp_path):
        write(tmp_path / "_default.yaml", "extra: !source ../../etc/passwd\n")
        # Tag failures are wrapped in TagError (adds file:line:column);
        # the original cause is still available via __cause__.
        with pytest.raises(TagError) as exc_info:
            compile_dataset(str(tmp_path))
        assert isinstance(exc_info.value.__cause__, PathTraversalError)
        assert "_default.yaml:1:" in str(exc_info.value)


class TestLoadTags:
    def test_load_text(self, tmp_path):
        write(tmp_path / "_default.yaml", "note: !load-text note.txt\n")
        write(tmp_path / "note.txt", "hello there")
        assert compile_dataset(str(tmp_path))["note"] == "hello there"

    def test_load_text_cannot_escape_source_directory(self, tmp_path):
        write(tmp_path / "_default.yaml", "note: !load-text ../../etc/passwd\n")
        with pytest.raises(TagError) as exc_info:
            compile_dataset(str(tmp_path))
        assert isinstance(exc_info.value.__cause__, PathTraversalError)

    def test_load_binary_returns_list_of_byte_values(self, tmp_path):
        write(tmp_path / "_default.yaml", "blob: !load-binary blob.bin\n")
        (tmp_path / "blob.bin").write_bytes(bytes([1, 2, 3]))
        assert compile_dataset(str(tmp_path))["blob"] == [1, 2, 3]

    def test_load_base64_roundtrips(self, tmp_path):
        import base64

        write(tmp_path / "_default.yaml", "blob: !load-base64 blob.bin\n")
        (tmp_path / "blob.bin").write_bytes(b"hello")
        data = compile_dataset(str(tmp_path))
        assert base64.b64decode(data["blob"]) == b"hello"


class TestQueryAndEval:
    def test_query_reads_a_sibling_value(self, tmp_path):
        write(
            tmp_path / "_default.yaml",
            "a:\n  x: 10\nb: !query a.x\n",
        )
        assert compile_dataset(str(tmp_path)) == {"a": {"x": 10}, "b": 10}

    def test_eval_can_use_query_and_env(self, tmp_path):
        write(
            tmp_path / "_default.yaml",
            'a:\n  x: 10\nb: !eval Query("a.x") * 2 + factor\n',
        )
        data = compile_dataset(str(tmp_path), env={"factor": 5})
        assert data["b"] == 25

    def test_eval_rejects_dangerous_expressions(self, tmp_path):
        write(tmp_path / "_default.yaml", 'a: !eval __import__("os").system("echo hi")\n')
        with pytest.raises(TagError) as exc_info:
            compile_dataset(str(tmp_path))
        assert isinstance(exc_info.value.__cause__, (EvalError, UnsafeExpressionError))


class TestValidatorTags:
    def test_valid_ipv4(self, tmp_path):
        write(tmp_path / "_default.yaml", "ip: !valid:ipv4 10.0.0.1\n")
        assert compile_dataset(str(tmp_path)) == {"ip": {"$ipv4": [10, 0, 0, 1]}}

    def test_invalid_ipv4_raises(self, tmp_path):
        write(tmp_path / "_default.yaml", "ip: !valid:ipv4 999.0.0.1\n")
        with pytest.raises(Exception):
            compile_dataset(str(tmp_path))

    def test_valid_int(self, tmp_path):
        write(tmp_path / "_default.yaml", 'n: !valid:int "42"\n')
        assert compile_dataset(str(tmp_path)) == {"n": 42}

    def test_valid_macaddr(self, tmp_path):
        write(tmp_path / "_default.yaml", 'mac: !valid:macaddr "AA:BB:CC:DD:EE:FF"\n')
        data = compile_dataset(str(tmp_path))
        assert data == {"mac": {"$macaddr": [0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF]}}

    def test_invalid_macaddr_raises(self, tmp_path):
        write(tmp_path / "_default.yaml", 'mac: !valid:macaddr "not-a-mac"\n')
        with pytest.raises(Exception):
            compile_dataset(str(tmp_path))


class TestSha256Tags:
    def test_sha256_of_a_string(self, tmp_path):
        import hashlib

        write(tmp_path / "_default.yaml", 'h: !ext:sha256-str "Hello"\n')
        data = compile_dataset(str(tmp_path))
        assert data == {"h": hashlib.sha256(b"Hello").hexdigest()}

    def test_sha256_of_a_file(self, tmp_path):
        import hashlib

        (tmp_path / "payload.txt").write_bytes(b"Hello")
        write(tmp_path / "_default.yaml", "h: !ext:sha256 payload.txt\n")
        data = compile_dataset(str(tmp_path))
        assert data == {"h": hashlib.sha256(b"Hello").hexdigest()}

    def test_sha256_file_matches_sha256_str_for_same_content(self, tmp_path):
        (tmp_path / "payload.txt").write_bytes(b"same content")
        write(
            tmp_path / "_default.yaml",
            'from_file: !ext:sha256 payload.txt\nfrom_str: !ext:sha256-str "same content"\n',
        )
        data = compile_dataset(str(tmp_path))
        assert data["from_file"] == data["from_str"]

    def test_sha256_file_cannot_escape_source_directory(self, tmp_path):
        write(tmp_path / "_default.yaml", "h: !ext:sha256 ../../etc/passwd\n")
        with pytest.raises(TagError) as exc_info:
            compile_dataset(str(tmp_path))
        assert isinstance(exc_info.value.__cause__, PathTraversalError)


class TestExampleFixtures:
    def test_01_sources_example_compiles(self, sources_example_dir):
        data = Compiler(sources_example_dir).compile()
        assert data["config"] == {"a": 1, "b": 2}
        assert data["snapshot"] == {"source": "bson", "value": 7}
        assert data["readme"] == "Hello from note.txt\n"
        assert data["logo_bytes"] == [1, 2, 3, 4, 5]
        assert data["app_root"] == {"from_hidden_key": 42}
        assert "staging_value" not in data  # hidden key stripped
        json.dumps(data)

    def test_02_computation_example_compiles(self, computation_example_dir):
        data = Compiler(computation_example_dir, env={"region": "eu-west-1", "factor": "3"}).compile()
        assert data["base_price_copy"] == 10
        assert data["total_price"] == 12.0
        assert data["scaled_price"] == 30
        assert data["region"] == "eu-west-1"
        json.dumps(data)

    def test_03_validators_example_compiles(self, validators_example_dir):
        data = Compiler(validators_example_dir).compile()
        assert data["network"]["ipv4"] == {"$ipv4": [192, 168, 1, 10]}
        assert data["network"]["mac"] == {"$macaddr": [0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF]}
        assert data["limits"] == {"max_connections": 254, "load_factor": 0.875}
        json.dumps(data)

    def test_04_utilities_example_compiles(self, utilities_example_dir):
        import hashlib

        data = Compiler(utilities_example_dir).compile()
        assert data["build"]["title"] == "My App v1.0.0"
        assert data["hashes"]["greeting_sha256"] == hashlib.sha256(b"Hello").hexdigest()
        json.dumps(data)


class TestEnvVarTag:
    def test_reads_a_set_variable(self, tmp_path):
        write(tmp_path / "_default.yaml", "region: !envvar YNIFIED_TEST_REGION\n")
        data = compile_dataset(str(tmp_path), env={"YNIFIED_TEST_REGION": "eu-west-1"})
        assert data == {"region": "eu-west-1"}

    def test_missing_variable_raises_tag_error_with_location(self, tmp_path):
        write(tmp_path / "_default.yaml", "region: !envvar DOES_NOT_EXIST\n")
        with pytest.raises(TagError) as exc_info:
            compile_dataset(str(tmp_path), env={})
        message = str(exc_info.value)
        assert "!envvar" in message
        assert "DOES_NOT_EXIST" in message
        assert "_default.yaml:1:" in message


class TestErrorMessagesHaveLocations:
    def test_tag_error_message_points_at_file_line_column(self, tmp_path):
        write(tmp_path / "_default.yaml", "a: 1\nb: !valid:int not-a-number\n")
        with pytest.raises(TagError) as exc_info:
            compile_dataset(str(tmp_path))
        message = str(exc_info.value)
        assert str(tmp_path / "_default.yaml") in message
        assert ":2:" in message  # the !valid:int tag is on line 2

    def test_error_points_at_the_nested_source_file_not_the_manifest(self, tmp_path):
        write(tmp_path / "_default.yaml", "extra: !source part.yaml\n")
        write(tmp_path / "part.yaml", "bad: !valid:int nope\n")
        with pytest.raises(TagError) as exc_info:
            compile_dataset(str(tmp_path))
        assert str(tmp_path / "part.yaml") in str(exc_info.value)


class TestCustomTags:
    def test_user_supplied_custom_tag(self, tmp_path):
        write(tmp_path / "_default.yaml", "shout: !shout hello\n")
        data = compile_dataset(
            str(tmp_path), custom_tags={"shout": lambda node: node.value.upper()}
        )
        assert data == {"shout": "HELLO"}
