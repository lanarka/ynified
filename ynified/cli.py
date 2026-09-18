"""
ynified command line interface.
    ynified <source_dir> [--to json|yaml|bson] [--gzip] [-o OUTPUT] [-v]
"""
import argparse
import json
import logging
import os
import sys

from .core import ynified_version
from .core import Compiler
from .exceptions import YnifiedError
from .output import SUPPORTED_FORMATS, write_output

logger = logging.getLogger("ynified")


def _default_output_path(source_dir, fmt, gzip_compress):
    base = source_dir.rstrip(os.sep)
    path = "%s.%s" % (base, fmt)
    if gzip_compress:
        path += ".gz"
    return path


def _print_debug(data):
    text = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)
    try:
        from pygments import highlight
        from pygments.formatters import TerminalFormatter
        from pygments.lexers import JsonLexer

        print(highlight(text, JsonLexer(), TerminalFormatter()))
    except ImportError:  # pygments is optional at runtime
        print(text)


def build_arg_parser():
    parser = argparse.ArgumentParser(
        prog="ynified",
        description="Compose a single JSON/YAML/BSON dataset from a directory of sources.",
    )
    parser.add_argument(
        "source_dir",
        help="directory containing a _default.yaml manifest",
    )
    parser.add_argument(
        "--to",
        dest="fmt",
        choices=SUPPORTED_FORMATS,
        default="json",
        help="output format (default: json)",
    )
    parser.add_argument(
        "--gzip",
        action="store_true",
        help="gzip-compress the output file",
    )
    parser.add_argument(
        "-o",
        "--output",
        dest="output",
        default=None,
        help="output file path (default: <source_dir>.<format>[.gz])",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="-v for info logging and a pretty-printed preview, -vv for debug logging",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"ynified {ynified_version}",
    )
    return parser


def _configure_logging(verbosity):
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def main(argv=None):
    args = build_arg_parser().parse_args(argv)
    _configure_logging(args.verbose)

    output_path = args.output or _default_output_path(args.source_dir, args.fmt, args.gzip)

    try:
        compiler = Compiler(args.source_dir, env=dict(os.environ))
        data = compiler.compile()
        if args.verbose:
            _print_debug(data)
        size = write_output(data, output_path, args.fmt, gzip_compress=args.gzip)
    except YnifiedError as exc:
        logger.error("%s", exc)
        return 1
    except OSError as exc:
        logger.error("file error: %s", exc)
        return 1

    logger.info("Wrote %s (%d bytes)", output_path, size)
    print(output_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
