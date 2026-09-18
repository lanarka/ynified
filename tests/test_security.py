import os

import pytest

from ynified.exceptions import PathTraversalError, UnsafeExpressionError
from ynified.security import safe_eval, safe_join


class TestSafeEval:
    def test_basic_arithmetic(self):
        assert safe_eval("1 + 2 * 3", {}) == 7

    def test_allowed_builtins_work(self):
        assert safe_eval("len('abc') + int('4')", {}) == 7

    def test_env_variables_are_visible(self):
        assert safe_eval("hello + 1", {"hello": 41}) == 42

    def test_query_callable_from_env_is_usable(self):
        assert safe_eval('Query("a.b")', {"Query": lambda q: q}) == "a.b"

    @pytest.mark.parametrize(
        "expression",
        [
            '__import__("os").system("echo pwned")',
            'open("/etc/passwd").read()',
            "exec('1')",
            "eval('1')",
            "compile('1', '<s>', 'eval')",
            "globals()",
            "locals()",
            "vars()",
            "dir()",
            "getattr(1, '__class__')",
            "().__class__",
            "(1).__class__.__bases__",
            "__builtins__",
        ],
    )
    def test_dangerous_expressions_are_rejected(self, expression):
        with pytest.raises(UnsafeExpressionError):
            safe_eval(expression, {})

    def test_syntax_errors_are_reported_as_unsafe_expression_error(self):
        with pytest.raises(UnsafeExpressionError):
            safe_eval("this is not ) valid python", {})

    def test_statements_are_rejected_not_only_expressions(self):
        with pytest.raises(UnsafeExpressionError):
            safe_eval("import os", {})

    def test_non_string_expression_is_rejected(self):
        with pytest.raises(UnsafeExpressionError):
            safe_eval(123, {})


class TestSafeJoin:
    def test_resolves_a_normal_relative_path(self, tmp_path):
        (tmp_path / "data.yaml").write_text("a: 1\n")
        result = safe_join(str(tmp_path), "data.yaml")
        assert result == os.path.realpath(str(tmp_path / "data.yaml"))

    def test_resolves_into_a_subdirectory(self, tmp_path):
        (tmp_path / "sub").mkdir()
        result = safe_join(str(tmp_path), "sub/data.yaml")
        assert result == os.path.realpath(str(tmp_path / "sub" / "data.yaml"))

    def test_rejects_parent_directory_traversal(self, tmp_path):
        with pytest.raises(PathTraversalError):
            safe_join(str(tmp_path), "../../etc/passwd")

    def test_rejects_absolute_path_outside_base(self, tmp_path):
        with pytest.raises(PathTraversalError):
            safe_join(str(tmp_path), "/etc/passwd")

    def test_rejects_traversal_hidden_inside_a_longer_path(self, tmp_path):
        with pytest.raises(PathTraversalError):
            safe_join(str(tmp_path), "sub/../../outside")

    def test_rejects_empty_path(self, tmp_path):
        with pytest.raises(PathTraversalError):
            safe_join(str(tmp_path), "")
