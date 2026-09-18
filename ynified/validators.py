"""
Strict input validators, used by the !valid:ipv4 / !valid:ipv6 /
!valid:int / !valid:float tags.

These are validators, not casts: they check that the given text is
*actually* a well-formed value of the expected kind and raise
ValidationError otherwise, rather than silently coercing ("1.9" -> 1).
"""
import ipaddress
import re

from .exceptions import ValidationError

_INT_RE = re.compile(r"^[+-]?\d+$")
_FLOAT_RE = re.compile(r"^[+-]?(\d+\.\d*|\.\d+|\d+)([eE][+-]?\d+)?$")
_MAC_RE = re.compile(
    r"^([0-9A-Fa-f]{2})([:-])"
    r"([0-9A-Fa-f]{2})\2([0-9A-Fa-f]{2})\2"
    r"([0-9A-Fa-f]{2})\2([0-9A-Fa-f]{2})\2([0-9A-Fa-f]{2})$"
)


def validate_ipv4(value):
    """Validate an IPv4 address, return {"$ipv4": [4 octets]}."""
    text = str(value).strip()
    try:
        ip = ipaddress.IPv4Address(text)
    except ValueError as exc:
        raise ValidationError("%r is not a valid IPv4 address" % value) from exc
    return {"$ipv4": list(ip.packed)}


def validate_ipv6(value):
    """Validate an IPv6 address, return {"$ipv6": [16 bytes]}."""
    text = str(value).strip()
    try:
        ip = ipaddress.IPv6Address(text)
    except ValueError as exc:
        raise ValidationError("%r is not a valid IPv6 address" % value) from exc
    return {"$ipv6": list(ip.packed)}


def validate_int(value):
    """
    Validate that `value` is a whole number written in plain decimal
    (optional leading +/-, digits only -- no "1.0", no "1e3", no
    thousands separators). Returns a Python int.
    """
    text = str(value).strip()
    if not _INT_RE.match(text):
        raise ValidationError("%r is not a valid integer" % value)
    return int(text)


def validate_float(value):
    """
    Validate that `value` is a real number in plain or scientific
    decimal notation ("1", "1.5", ".5", "1e-3", ...). Rejects things
    Python's float() would otherwise accept but that are rarely
    intended in a dataset, such as "nan", "inf" or "  1.0  " with
    embedded whitespace. Returns a Python float.
    """
    text = str(value).strip()
    if not _FLOAT_RE.match(text):
        raise ValidationError("%r is not a valid float" % value)
    return float(text)


def validate_macaddr(value):
    """
    Validate a MAC address written as six colon- or hyphen-separated
    hex octets, not mixed (e.g. "aa:bb:cc:dd:ee:ff" or
    "AA-BB-CC-DD-EE-FF"). Returns {"$macaddr": [6 octets]}.
    """
    text = str(value).strip()
    match = _MAC_RE.match(text)
    if not match:
        raise ValidationError("%r is not a valid MAC address" % value)
    groups = match.groups()
    octets = [int(groups[i], 16) for i in (0, 2, 3, 4, 5, 6)]
    return {"$macaddr": octets}
