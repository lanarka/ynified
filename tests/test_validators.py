import pytest

from ynified.exceptions import ValidationError
from ynified.validators import validate_float, validate_int, validate_ipv4, validate_ipv6


class TestIPv4:
    def test_accepts_valid_address(self):
        assert validate_ipv4("192.168.0.1") == {"$ipv4": [192, 168, 0, 1]}

    def test_strips_surrounding_whitespace(self):
        assert validate_ipv4("  10.0.0.1  ") == {"$ipv4": [10, 0, 0, 1]}

    @pytest.mark.parametrize(
        "bad",
        ["999.1.1.1", "1.2.3", "not-an-ip", "::1", "1.2.3.4.5", ""],
    )
    def test_rejects_invalid_input(self, bad):
        with pytest.raises(ValidationError):
            validate_ipv4(bad)


class TestIPv6:
    def test_accepts_valid_address(self):
        result = validate_ipv6("::1")
        assert result["$ipv6"] == [0] * 15 + [1]

    def test_accepts_full_form(self):
        result = validate_ipv6("fe80::1")
        assert result["$ipv6"][0] == 0xFE
        assert result["$ipv6"][1] == 0x80

    @pytest.mark.parametrize("bad", ["192.168.0.1", "not-an-ip", "gggg::1", ""])
    def test_rejects_invalid_input(self, bad):
        with pytest.raises(ValidationError):
            validate_ipv6(bad)


class TestInt:
    @pytest.mark.parametrize(
        "value, expected",
        [("0", 0), ("42", 42), ("-7", -7), ("+7", 7), (10, 10)],
    )
    def test_accepts_valid_integers(self, value, expected):
        assert validate_int(value) == expected
        assert isinstance(validate_int(value), int)

    @pytest.mark.parametrize("bad", ["1.0", "1e3", "abc", "", "1,000", "1 2"])
    def test_rejects_non_integers(self, bad):
        with pytest.raises(ValidationError):
            validate_int(bad)


class TestFloat:
    @pytest.mark.parametrize(
        "value, expected",
        [("1", 1.0), ("1.5", 1.5), (".5", 0.5), ("-0.0625", -0.0625), ("1e-3", 0.001)],
    )
    def test_accepts_valid_floats(self, value, expected):
        assert validate_float(value) == expected

    @pytest.mark.parametrize("bad", ["abc", "", "nan", "inf", "1.2.3", "1_000"])
    def test_rejects_invalid_input(self, bad):
        with pytest.raises(ValidationError):
            validate_float(bad)
