"""
	ynified cli
"""
import argparse
import sys
import os
import traceback
import coloredlogs
import logging
logger = logging.getLogger(__name__)

from ynified import run_rc
from ynified.ext import custom_tags

def on_unhandled_exception(type, value, tb):
	tb_info = "".join(traceback.format_exception(type, value, tb))
	msg = "%s: %s" % (type.__name__, tb_info)
	logger.critical(msg)

def main():
	env = dict(os.environ)
	parser = argparse.ArgumentParser(description="ynified command line interface")
	#parser.add_argument("subcommand", type=str, help="Subcommand c|m")
	parser.add_argument("base_name", type=str, help="A required <base-name>")
	parser.add_argument("--debug", type=int, nargs="?", help="Debug level <int>")
	parser.add_argument("--to", type=str, nargs="?", help="Output format json|yaml|bson|bson+gz")
	args = parser.parse_args()
	#print('xxxx',args.subcommand)
	base_name = args.base_name
	debug = True if args.debug == 1 else False
	if (args.to=="bson"):
		output_format = "bson"
		compress = False
	if (args.to=="bson+gz"):
		output_format = "bson"
		compress = True
	if (args.to=="json"):
		output_format = "json"
		compress = False
	if (args.to=="yaml"):
		output_format = "yaml"
		compress = False
	logger = logging.getLogger("main")
	coloredlogs.DEFAULT_DATE_FORMAT = "%d/%m/%y %H:%M:%S"
	coloredlogs.DEFAULT_FIELD_STYLES = {
		"asctime": {"color": "green"},
		"hostname": {"color": "white", "faint": True},
		"levelname": {"color": "cyan"},
		"name": {"color": "magenta"},
		"programname": {"color": "cyan"},
		"username": {"color": "yellow"}
	}
	coloredlogs.DEFAULT_LEVEL_STYLES = {
		"critical": {"color": "red"},
		"debug": {"color": "green"},
		"error": {"color": "red"},
		"info": {"color": "white"},
		"notice": {"color": "magenta"},
		"spam": {"color": "red", "faint": True},
		"success": {"color": "green", "faint": True},
		"verbose": {"color": "blue"},
		"warning": {"color": "yellow"}
	}
	sys.excepthook = on_unhandled_exception
	if debug:
		coloredlogs.install(level="DEBUG")
	done = run_rc(base_name, env, custom_tags, to=output_format, debug=debug, compress=compress)
	sys.exit(done)
	
if __name__ == "__main__":
	main()
