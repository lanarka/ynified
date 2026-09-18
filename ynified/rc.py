"""
	ynified transpiler
"""
import os
import sys
import base64
import gzip

import bson
import json
import yaml

from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import TerminalFormatter

import logging
logger = logging.getLogger(__name__)

from .query import Q

class RC:

	FN_DEFAULT = '_default.yaml'
	TAG_HIDDEN = '--'
	
	def __init__(self, base_name, custom_tags={}, env={}, debug=False):
		self.base_name = base_name
		self.debug = debug
		self.env = env
		self.custom_tags = custom_tags
		self.body = {}
		self.preload = False
		self.preload_data = {}

	def compile(self, target='json', compress=True):
		self.preload = True
		self.proc(target=target, compress=compress)
		self.preload = False
		return self.proc(target=target, compress=compress)

	def proc(self, target='json', compress=True):

		class QueryTag(yaml.YAMLObject):
			@classmethod
			def from_yaml(cls, loader, node):
				if not self.preload:
					return Q(self.preload_data, node.value)

		class LoadTextTag(yaml.YAMLObject):
			@classmethod
			def from_yaml(cls, loader, node):
				return self.load_text(node.value)

		class LoadBinaryTag(yaml.YAMLObject):
			@classmethod
			def from_yaml(cls, loader, node):
				return self.load_bin(node.value)

		class LoadBase64Tag(yaml.YAMLObject):
			@classmethod
			def from_yaml(cls, loader, node):
				return self.load_b64(node.value)

		class EvalTag(yaml.YAMLObject):
			@classmethod
			def from_yaml(cls, loader, node):
				return self.pyeval(node.value)

		class SourceYAMLTag(yaml.YAMLObject):
			@classmethod
			def from_yaml(cls, loader, node):
				return self.load_yaml(str(node.value))

		class SourceBSONTag(yaml.YAMLObject):
			@classmethod
			def from_yaml(cls, loader, node):
				return self.load_bson(str(node.value))

		yaml.SafeLoader.add_constructor('!load-text', LoadTextTag.from_yaml)
		yaml.SafeLoader.add_constructor('!load-binary', LoadBinaryTag.from_yaml)
		yaml.SafeLoader.add_constructor('!load-base64', LoadBase64Tag.from_yaml)
		yaml.SafeLoader.add_constructor('!source', SourceYAMLTag.from_yaml)
		yaml.SafeLoader.add_constructor('!source-bson', SourceBSONTag.from_yaml)
		yaml.SafeLoader.add_constructor('!eval', EvalTag.from_yaml)
		yaml.SafeLoader.add_constructor('!query', QueryTag.from_yaml)

		# custom tags
		for tag in self.custom_tags.keys():
			tag_c = type('CustomYamlTag',(yaml.YAMLObject,), {'from_yaml': self.custom_tags[tag]})
			yaml.SafeLoader.add_constructor('!%s' % tag, tag_c.from_yaml)
		
		outfilename = self.base_name + '.' + target
		done = self.load_yaml(self.FN_DEFAULT)
		
		self.body = done
		if not done:
			raise Exception('Nothing to do!')
		if not isinstance(done, dict):
			raise Exception('Dictionary object expected!')

		# remove hidden keys
		done_opt = {}
		for y in done.keys():
			if y[:2] != self.TAG_HIDDEN:
				done_opt[y] = done[y]
		done = done_opt

		# pre-processing: fix-me: ugly solution
		if self.preload:
			c_base_name = "ynified_" + self.base_name.replace("/", "_")
			fh=open("/tmp/%s" % c_base_name, "w")
			fh.write(json.dumps(done))
			fh.close()
			fh=open("/tmp/%s" % c_base_name, "r")
			self.preload_data=json.loads(fh.read())
			fh.close() # unlink file?

		if not self.preload:
			if self.debug:
				self.print_debug(done)

			if target == 'yaml':
				dump = yaml.dump(done)
				ft = 'w'

			if target == 'json':
				dump = json.dumps(done)
				ft = 'w'

			if target == 'bson':
				dump = bson.dumps(done)
				ft = 'wb'

			if compress:
				outfilename += '.gz'
				fh = gzip.open(outfilename, 'wb')
				if isinstance(dump, str):
					dump = bytes(dump, 'ascii')
			else:
				fh = open(outfilename, ft)
			fh.write(dump)
			fh.close()
			logger.info("Sucessfull! (%s Bytes)", len(dump))
		return 0

	def print_debug(self, obj):
		json_str = json.dumps(obj, indent=4, sort_keys=True)
		print(highlight(json_str, JsonLexer(), TerminalFormatter()))

	def load_yaml(self, filename):
		if self.preload:
			logger.debug("Processing file... %s", filename)
		else:
			logger.debug("Adding source...   %s", filename)
		fn = self.base_name + os.path.sep + filename
		fh = open(fn, 'r')
		obj = yaml.safe_load(fh)
		fh.close()
		return obj

	def load_bson(self, filename):
		if self.preload:
			logger.debug("Processing file... %s", filename)
		else:
			logger.debug("Adding source...   %s", filename)
		fn = self.base_name + os.path.sep + filename
		fh = open(fn, 'rb')
		data = fh.read()
		obj = bson.loads(data)
		fh.close()
		return obj

	def load_text(self, filename):
		logger.debug("Loading file...    %s", filename)
		fn = self.base_name + os.path.sep + filename
		fh = open(fn, 'r')
		data = fh.read()
		fh.close()
		return data

	def load_b64(self, filename):
		logger.debug("Loading file...    %s", filename)
		fn = self.base_name + os.path.sep + filename
		fh = open(fn, 'rb')
		data = fh.read()
		fh.close()
		return base64.b64encode(data).decode('ascii')

	def load_bin(self, filename):
		logger.debug("Loading file...    %s", filename)
		fn = self.base_name + os.path.sep + filename
		fh = open(fn, 'rb')
		data = fh.read()
		fh.close()
		return list(data)

	def pyeval(self, expression):
		if self.preload:
			self.env["Query"] = lambda q: 0
		else:
			self.env["Query"] = lambda q: Q(self.preload_data, q)
		self.env["Info"] = {"generator": "ynified-1"}
		done = eval(expression, self.env) # fix: catch exception for tracking
		return done


def run_rc(base_name, env, custom_tags, compress=False, debug=False, to='bson'):
	logger.info("Compiling source base: %s", base_name)
	rc = RC(base_name, env=env, custom_tags=custom_tags, debug=debug)
	return rc.compile(target=to, compress=compress)
